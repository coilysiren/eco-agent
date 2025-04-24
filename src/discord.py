import discord
import asyncio

from . import model


class Client(discord.Client):
    def subscribe(self, channel):
        @self.event
        async def on_message(message):
            # Only respond to messages in the subscribed channel that start with #bot
            if message.channel.id == channel.id and message.content.startswith("#bot"):
                # Get the prompt by removing the #bot prefix
                prompt = message.content.strip("#bot").strip()

                # Get response from model
                response = model.request(prompt)

                # Send response back to the channel
                await channel.send(response)

    @classmethod
    async def init(cls, token: str, server_id: int):
        intents = discord.Intents.default()
        intents.message_content = True

        client = cls(intents=intents)
        asyncio.create_task(client.start(token))

        while not client.is_ready():
            await asyncio.sleep(0.1)

        guild = client.get_guild(server_id)

        return (client, guild)
