import discord
from discord.ext import commands
from services.ollama import ask_cerebro

class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _clean_mentions(self, content: str, guild: discord.Guild | None) -> str:
        for mention in (f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"):
            content = content.replace(mention, "")
        if guild:
            for role in guild.me.roles:
                content = content.replace(f"<@&{role.id}>", "")
        return content.strip()

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

        prompt = self._clean_mentions(message.content, message.guild)
        if not prompt:
            await message.reply("¿En qué puedo ayudarte?")
            return

        async with message.channel.typing():
            try:
                history_messages = []
                # Lee los últimos 15 mensajes del canal (incluyendo el actual)
                raw_history = [msg async for msg in message.channel.history(limit=15)]
                raw_history.reverse()  # Orden cronológico: del más antiguo al más reciente

                for msg in raw_history:
                    clean_text = self._clean_mentions(msg.content, message.guild)
                    if not clean_text:
                        continue
                    if msg.author == self.bot.user:
                        history_messages.append({"role": "assistant", "content": clean_text})
                    else:
                        history_messages.append({
                            "role": "user",
                            "content": f"{msg.author.display_name}: {clean_text}"
                        })

                reply_text = await ask_cerebro(history_messages)
                for i in range(0, len(reply_text), 2000):
                    await message.reply(reply_text[i:i+2000])
            except discord.Forbidden:
                await message.reply("No tengo permiso de **Leer el historial de mensajes** en este canal.")
            except Exception as e:
                await message.reply(f"Error al consultar Ollama Cloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))