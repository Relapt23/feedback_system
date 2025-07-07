from fastapi import HTTPException
from httpx import AsyncClient

import os


api_key = os.getenv("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY environment variable is not set")
url = "https://api.apilayer.com/sentiment/analysis"


async def analyze_sentiment(text: str) -> str:
    headers = {"apikey": api_key}
    payload = {"body": text}
    async with AsyncClient() as client:
        response = await client.post(url=url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(detail="Sentiment API error", status_code=502)
    data = response.json()
    return data.get("sentiment")
