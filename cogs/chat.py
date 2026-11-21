import discord
from discord.ext import commands
from services.ollama import ask_cerebro

class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if self.bot.user in message.mentions:
            prompt = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not prompt:
                await message.reply("¿En qué puedo ayudarte?")
                return

            async with message.channel.typing():
                try:
                    reply_text = await ask_cerebro(prompt)
                    for i in range(0, len(reply_text), 2000):
                        await message.reply(reply_text[i:i+2000])
                except Exception as e:
                    await message.reply(f"Error al consultar Ollama Cloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))