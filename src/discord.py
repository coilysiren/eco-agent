import asyncio
import typing

import discord
import structlog

from . import model


logger = structlog.get_logger()


class Client(discord.Client):
    """
    A singleton client for the Discord bot.
    """

    _instance: typing.Union["Client", None] = None
    _initialized = False
    _authorized = False
    _channel_subscriptions: dict[int, bool] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # pylint: disable=no-value-for-parameter
        return cls._instance

    def __init__(self, *args, **kwargs):
        if not self._initialized:
            logger.info("initializing discord client class")

            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            intents.guild_messages = True

            super().__init__(*args, intents=intents, **kwargs)
            self._initialized = True

            @self.event
            async def on_message(message: discord.Message):
                """Handle #bot commands whenever a message is sent"""

                logger.info(
                    "on_message: start",
                    message=message,
                    channel=message.channel,
                    author=message.author,
                    text=message.content,
                )

                if message.author.bot:
                    logger.info("on_message: message from a bot", author=message.author)
                    return

                if "?" not in message.content:
                    logger.info(
                        "on_message: message does not include ?",
                        text=message.content,
                    )
                    return

                if not self._channel_subscriptions.get(message.channel.id):
                    logger.info(
                        "on_message: channel not subscribed",
                        channel=message.channel.id,
                        subscribed=self._channel_subscriptions,
                    )
                    return

                if len(message.content) > 256:
                    logger.info(
                        "on_message: message is too long", length=len(message.content)
                    )
                    return

                prompt = message.content.strip("#bot").strip()
                response = model.request(prompt)
                await message.reply(response)

    def subscribe(self, channel_id: int):
        """
        Subscribe to a channel to handle #bot commands,
        don't create duplicate subscriptions
        """
        if channel_id in self._channel_subscriptions:
            logger.info("subscribe: channel already subscribed", channel_id=channel_id)
            return

        logger.info("subscribe: subscribing to channel", channel_id=channel_id)
        self._channel_subscriptions[channel_id] = True

    async def init(self, token: str, server_id: int):
        logger.info("initializing discord client authorization", server_id=server_id)

        if self._authorized:
            return

        # Start in background
        asyncio.create_task(self.start(token))

        # Wait until ready
        while not self.is_ready():
            await asyncio.sleep(0.1)

        guild = self.get_guild(server_id)
        if not guild:
            raise ValueError(f"Could not find guild with ID {server_id}")

        logger.info("discord client initialized", guild=guild)
        self._authorized = True
