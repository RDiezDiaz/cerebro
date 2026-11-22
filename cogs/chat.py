from collections import defaultdict, deque
import discord
from discord.ext import commands
from services.ollama import ask_cerebro

class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Guarda las últimas 5 llamadas (5 pares de mensaje usuario + respuesta bot = 10 mensajes) por canal
        self.channel_memory: dict[int, deque] = defaultdict(lambda: deque(maxlen=10))

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

        # Ignora cualquier mensaje donde no se le llame directamente
        if not (is_dm or is_user_mentioned or is_role_mentioned):
            return

        prompt = self._clean_mentions(message.content, message.guild)
        if not prompt:
            await message.reply("¿En qué puedo ayudarte?")
            return

        channel_id = message.channel.id
        user_entry = {
            "role": "user",
            "content": f"{message.author.display_name}: {prompt}"
        }

        async with message.channel.typing():
            try:
                # Construye el contexto solo con las últimas 5 llamadas guardadas + la actual
                conversation = list(self.channel_memory[channel_id]) + [user_entry]
                reply_text = await ask_cerebro(conversation)

                # Guarda esta llamada y su respuesta en la memoria del canal
                self.channel_memory[channel_id].append(user_entry)
                self.channel_memory[channel_id].append({
                    "role": "assistant",
                    "content": reply_text
                })

                for i in range(0, len(reply_text), 2000):
                    await message.reply(reply_text[i:i+2000])
            except Exception as e:
                await message.reply(f"Error al consultar Ollama Cloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))