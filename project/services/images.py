import requests


def get_place_images(destination: str, api_key: str) -> list[str]:
    if not api_key:
        return []

    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": destination, "per_page": 3},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return []

    return [photo["src"]["large"] for photo in data.get("photos", [])]
