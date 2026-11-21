from ollama import AsyncClient
from config import OLLAMA_API_KEY, OLLAMA_MODEL

client = AsyncClient(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"}
)

SYSTEM_PROMPT = (
    "Te llamas Cerebro. Eres el asistente inteligente de este servidor de Discord. "
    "Tienes acceso a los últimos mensajes del canal para mantener el contexto de la conversación. "
    "Responde de forma clara, directa y útil."
)

async def ask_cerebro(conversation_history: list[dict]) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
    response = await client.chat(
        model=OLLAMA_MODEL,
        messages=messages
    )
    return response["message"]["content"]