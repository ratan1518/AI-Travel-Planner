from openai import OpenAI

from config import AppConfig


def _build_prompt(destination: str, budget: int, days: int) -> str:
    day_sections = []
    for day_number in range(1, days + 1):
        day_sections.append(
            f"Day {day_number}:\n"
            "- Morning:\n"
            "- Afternoon:\n"
            "- Evening:\n"
        )

    day_format = "\n".join(day_sections)

    return (
        f"Plan a {days}-day trip to {destination} within INR {budget}.\n\n"
        "Return a practical itinerary using this structure:\n"
        f"{day_format}\n\n"
        "Also include:\n"
        "- Recommended hotels\n"
        "- Budget breakdown\n"
        "- Food suggestions\n"
        "- Local travel tips\n"
        "- A short packing checklist\n"
    )


def generate_itinerary(destination: str, budget: int, days: int, config: AppConfig) -> str:
    try:
        client = OpenAI(
            api_key=config.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": config.app_url,
                "X-Title": config.app_title,
            },
        )

        response = client.chat.completions.create(
            model=config.model_name,
            messages=[{"role": "user", "content": _build_prompt(destination, budget, days)}],
            timeout=20,
        )

        content = response.choices[0].message.content
        return content or "No itinerary was generated."
    except Exception as exc:
        return f"Error generating itinerary: {exc}"
