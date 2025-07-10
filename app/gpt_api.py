import os
from openai import OpenAI, OpenAIError


async def category_definition(text: str) -> str:
    API_KEY = os.getenv("API_GPT_KEY")
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=os.getenv("GPT_URL"))
    sys_prompt = (
        f"Определи категорию жалобы: {text}. Варианты: техническая, оплата, другое."
        f" Ответ только одним словом. "
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": sys_prompt},
            ],
            temperature=0.0,
        )
        category = response.choices[0].message.content.strip().lower()
    except OpenAIError:
        category = "другое"
    return category
