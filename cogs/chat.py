import discord
from discord.ext import commands
from services.ollama import ask_cerebro

class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_user_mentioned = self.bot.user in message.mentions
        is_role_mentioned = bool(
            message.guild and any(role in message.guild.me.roles for role in message.role_mentions)
        )

        if not (is_dm or is_user_mentioned or is_role_mentioned):
            return

        prompt = message.content
        for mention in (f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"):
            prompt = prompt.replace(mention, "")

        if message.guild:
            for role in message.role_mentions:
                if role in message.guild.me.roles:
                    prompt = prompt.replace(f"<@&{role.id}>", "")

        prompt = prompt.strip()

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