import os
from openai import OpenAI, OpenAIError


API_KEY = os.getenv("API_GPT_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=API_KEY, base_url=os.getenv("GPT_URL"))


async def category_definition(text: str) -> str:
    sys_prompt = (
        "Ты — специалист по заявкам от клиентов.\n"
        "Определи категорию жалобы.\n"
        "Варианты: техническая, оплата, другое.\n"
        "Ответь одним словом, без дополнительных пояснений."
    )
    user_msg = f'Жалоба: "{text}"'
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.0,
        )
        category = response.choices[0].message.content.strip().lower()
    except OpenAIError:
        category = "другое"
    return category
