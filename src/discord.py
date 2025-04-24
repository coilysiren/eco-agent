import discord
import asyncio


class Client(discord.Client):
    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        print(f"Message from {message.author}: {message.content}")

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
