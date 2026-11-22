import discord
from discord import app_commands
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

    async def _build_conversation(
        self,
        channel: discord.abc.Messageable,
        guild: discord.Guild | None,
        author_name: str,
        prompt: str,
        before_message: discord.Message | None = None
    ) -> list[dict]:
        past_calls = []
        past_replies = []

        async for msg in channel.history(limit=60, before=before_message):
            if msg.author == self.bot.user:
                if len(past_replies) < 5 and msg.content.strip():
                    past_replies.append((msg.created_at, {
                        "role": "assistant",
                        "content": msg.content.strip()
                    }))
            elif not msg.author.bot and self._is_bot_called(msg):
                if len(past_calls) < 5:
                    clean_text = self._clean_mentions(msg.content, guild)
                    if clean_text:
                        past_calls.append((msg.created_at, {
                            "role": "user",
                            "content": f"{msg.author.display_name}: {clean_text}"
                        }))

            if len(past_calls) >= 5 and len(past_replies) >= 5:
                break

        combined = past_calls + past_replies
        combined.sort(key=lambda item: item[0])

        conversation = [entry for _, entry in combined]
        conversation.append({
            "role": "user",
            "content": f"{author_name}: {prompt}"
        })
        return conversation

    # 1. Respuesta por mención (@Cerebro)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not self._is_bot_called(message):
            return

        prompt = self._clean_mentions(message.content, message.guild)
        if not prompt:
            await message.reply("¿En qué puedo ayudarte?")
            return

        async with message.channel.typing():
            try:
                conversation = await self._build_conversation(
                    channel=message.channel,
                    guild=message.guild,
                    author_name=message.author.display_name,
                    prompt=prompt,
                    before_message=message
                )
                reply_text = await ask_cerebro(conversation)
                for i in range(0, len(reply_text), 2000):
                    await message.reply(reply_text[i:i+2000])
            except discord.Forbidden:
                await message.reply("No tengo permiso de **Leer el historial de mensajes** en este canal.")
            except Exception as e:
                await message.reply(f"Error al consultar Ollama Cloud: `{e}`")

    # 2. Respuesta por Slash Command (/cerebro)
    @app_commands.command(name="cerebro", description="Haz una pregunta o pide ayuda a Cerebro")
    @app_commands.describe(mensaje="Lo que quieres preguntar o pedir a Cerebro")
    async def cerebro_slash(self, interaction: discord.Interaction, mensaje: str):
        # Obligatorio: Discord exige responder en menos de 3 segundos; defer() evita el timeout mientras Ollama piensa
        await interaction.response.defer(thinking=True)

        try:
            conversation = await self._build_conversation(
                channel=interaction.channel,
                guild=interaction.guild,
                author_name=interaction.user.display_name,
                prompt=mensaje.strip()
            )
            reply_text = await ask_cerebro(conversation)

            # Primer bloque (hasta 2000 caracteres) cierra el defer()
            await interaction.followup.send(reply_text[:2000])
            # Si la respuesta supera los 2000 caracteres, envía el resto en mensajes seguidos
            for i in range(2000, len(reply_text), 2000):
                await interaction.followup.send(reply_text[i:i+2000])
        except discord.Forbidden:
            await interaction.followup.send("No tengo permiso de **Leer el historial de mensajes** en este canal.")
        except Exception as e:
            await interaction.followup.send(f"Error al consultar Ollama Cloud: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))