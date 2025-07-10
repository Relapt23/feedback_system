from fastapi import HTTPException
from httpx import AsyncClient, Timeout, RequestError

import os


async def analyze_sentiment(text: str) -> str:
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("API_KEY environment variable is not set")

    url = "https://api.apilayer.com/sentiment/analysis"
    headers = {"apikey": api_key}
    payload = text

    async with AsyncClient() as client:
        try:
            response = await client.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=Timeout(15.0, connect=5.0),
            )
        except RequestError:
            raise HTTPException(detail="Sentiment API error", status_code=502)

    data = response.json()
    return data.get("sentiment") or "unknown"
