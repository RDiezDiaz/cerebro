from ollama import AsyncClient
from config import OLLAMA_API_KEY, OLLAMA_MODEL

client = AsyncClient(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"}
)

SYSTEM_PROMPT = (
    "Te llamas Cerebro. Eres el asistente inteligente de este servidor de Discord. "
    "Responde de forma clara, directa y útil."
)

async def ask_cerebro(user_message: str) -> str:
    response = await client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    return response["message"]["content"]