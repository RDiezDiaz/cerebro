import discord
from discord.ext import commands
from services.ollama import ask_cerebro

class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_bot_called(self, message: discord.Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True
        if self.bot.user in message.mentions:
            return True
        if message.guild and any(role in message.guild.me.roles for role in message.role_mentions):
            return True
        return False

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

        if not self._is_bot_called(message):
            return

        prompt = self._clean_mentions(message.content, message.guild)
        if not prompt:
            await message.reply("¿En qué puedo ayudarte?")
            return

        async with message.channel.typing():
            try:
                past_calls = []
                past_replies = []

                # Recorre los mensajes anteriores al actual desde el más reciente hacia atrás
                async for msg in message.channel.history(limit=60, before=message):
                    if msg.author == self.bot.user:
                        if len(past_replies) < 5 and msg.content.strip():
                            past_replies.append((msg.created_at, {
                                "role": "assistant",
                                "content": msg.content.strip()
                            }))
                    elif not msg.author.bot and self._is_bot_called(msg):
                        if len(past_calls) < 5:
                            clean_text = self._clean_mentions(msg.content, message.guild)
                            if clean_text:
                                past_calls.append((msg.created_at, {
                                    "role": "user",
                                    "content": f"{msg.author.display_name}: {clean_text}"
                                }))

                    # Detiene la lectura en cuanto tiene las 5 últimas menciones y las 5 últimas respuestas
                    if len(past_calls) >= 5 and len(past_replies) >= 5:
                        break

                # Combina ambas listas y las ordena cronológicamente (de más antigua a más reciente)
                combined = past_calls + past_replies
                combined.sort(key=lambda item: item[0])

                conversation = [entry for _, entry in combined]
                conversation.append({
                    "role": "user",
                    "content": f"{message.author.display_name}: {prompt}"
                })

                reply_text = await ask_cerebro(conversation)
                for i in range(0, len(reply_text), 2000):
                    await message.reply(reply_text[i:i+2000])
            except discord.Forbidden:
                await message.reply("No tengo permiso de **Leer el historial de mensajes** en este canal.")
            except Exception as e:
                await message.reply(f"Error al consultar Ollama Cloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))