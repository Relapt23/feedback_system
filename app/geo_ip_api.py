from httpx import AsyncClient, Timeout, RequestError


async def get_geolocation(ip: str) -> dict:
    url = "http://ip-api.com/json/{ip}"
    DEFAULT_GEO = {
        "country": None,
        "region": None,
        "city": None,
        "latitude": None,
        "longitude": None,
    }
    async with AsyncClient() as client:
        try:
            response = await client.get(
                url=url, timeout=Timeout(Timeout(15.0, connect=5.0))
            )
        except RequestError:
            return DEFAULT_GEO

    data = response.json()
    if data["status"] != "success":
        return DEFAULT_GEO
    return {
        "country": data.get("country"),
        "region": data.get("regionName"),
        "city": data.get("city"),
        "latitude": data.get("lat"),
        "longitude": data.get("lon"),
    }
