import asyncio
import discord
from discord.ext import commands
from config import DISCORD_TOKEN, OLLAMA_MODEL

class CerebroBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Carga automática de los módulos en la carpeta cogs
        await self.load_extension("cogs.chat")

    async def on_ready(self):
        print(f"🧠 {self.user} está en línea | Modelo: {OLLAMA_MODEL}")

async def main():
    bot = CerebroBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())