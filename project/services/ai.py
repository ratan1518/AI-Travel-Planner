import json
import re

from openai import OpenAI

from config import AppConfig


def _build_prompt(
    destination: str,
    budget: int,
    days: int,
    travel_style: str,
    companions: str,
    interests: list[str],
    pace: int,
    food_preference: str,
) -> str:
    day_sections = []
    for day_number in range(1, days + 1):
        day_sections.append(
            "{"
            f'"day": "Day {day_number}", '
            '"morning": "", '
            '"afternoon": "", '
            '"evening": "", '
            '"estimated_cost": ""'
            "}"
        )

    itinerary_template = ",\n".join(day_sections)
    interests_text = ", ".join(interests) if interests else "general sightseeing"
    pace_label = {
        1: "very relaxed",
        2: "relaxed",
        3: "balanced",
        4: "active",
        5: "packed",
    }.get(pace, "balanced")

    return (
        f"Create a {days}-day travel plan for {destination} within INR {budget}.\n"
        f"Travel style: {travel_style}\n"
        f"Companions: {companions}\n"
        f"Interests: {interests_text}\n"
        f"Pace: {pace_label}\n"
        f"Food preference: {food_preference}\n\n"
        "Use real place names for sightseeing locations.\n"
        "For hotels, suggest real hotels that plausibly exist in the destination, match the overall budget, "
        "and stay close to the main places or areas mentioned in the itinerary.\n"
        "If you are not confident, return fewer hotel suggestions rather than inventing details.\n\n"
        "Return only valid JSON with this exact schema:\n"
        "{\n"
        '  "title": "string",\n'
        '  "summary": "string",\n'
        '  "why_this_plan": "string",\n'
        f'  "travel_style": "{travel_style}",\n'
        f'  "companions": "{companions}",\n'
        f'  "pace": "{pace_label}",\n'
        '  "best_time_to_visit": "string",\n'
        '  "daily_itinerary": [\n'
        f"    {itinerary_template}\n"
        "  ],\n"
        '  "recommended_hotels": [\n'
        "    {\n"
        '      "name": "string",\n'
        '      "area": "string",\n'
        '      "price_range": "string",\n'
        '      "near_places": ["string"],\n'
        '      "why_it_matches": "string"\n'
        "    }\n"
        "  ],\n"
        '  "budget_breakdown": {\n'
        '    "Stay": "string",\n'
        '    "Food": "string",\n'
        '    "Transport": "string",\n'
        '    "Activities": "string",\n'
        '    "Buffer": "string"\n'
        "  },\n"
        '  "food_suggestions": ["string"],\n'
        '  "local_transport": ["string"],\n'
        '  "travel_tips": ["string"],\n'
        '  "packing_checklist": ["string"]\n'
        "}\n\n"
        "Keep recommendations practical, realistic, and portfolio-demo friendly."
    )


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"raw_text": text}


def generate_travel_plan(
    destination: str,
    budget: int,
    days: int,
    travel_style: str,
    companions: str,
    interests: list[str],
    pace: int,
    food_preference: str,
    config: AppConfig,
) -> dict:
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
            messages=[
                {
                    "role": "user",
                    "content": _build_prompt(
                        destination,
                        budget,
                        days,
                        travel_style,
                        companions,
                        interests,
                        pace,
                        food_preference,
                    ),
                }
            ],
            timeout=20,
        )

        content = response.choices[0].message.content
        if not content:
            return {"raw_text": "No itinerary was generated."}
        return _extract_json(content)
    except Exception as exc:
        return {"raw_text": f"Error generating itinerary: {exc}"}


def format_plan_as_markdown(plan: dict) -> str:
    if "raw_text" in plan:
        return plan["raw_text"]

    lines = [f"# {plan.get('title', 'Travel Plan')}", ""]

    summary = plan.get("summary")
    if summary:
        lines.extend([summary, ""])

    why_this_plan = plan.get("why_this_plan")
    if why_this_plan:
        lines.extend(["## Why This Plan Works", why_this_plan, ""])

    for label, key in (
        ("Travel Style", "travel_style"),
        ("Companions", "companions"),
        ("Pace", "pace"),
        ("Best Time to Visit", "best_time_to_visit"),
    ):
        value = plan.get(key)
        if value:
            lines.append(f"- {label}: {value}")
    lines.append("")

    itinerary = plan.get("daily_itinerary", [])
    if itinerary:
        lines.append("## Daily Itinerary")
        for day in itinerary:
            lines.append(f"### {day.get('day', 'Day Plan')}")
            for slot in ("morning", "afternoon", "evening"):
                activity = day.get(slot)
                if activity:
                    lines.append(f"- {slot.title()}: {activity}")
            if day.get("estimated_cost"):
                lines.append(f"- Estimated Cost: {day['estimated_cost']}")
            lines.append("")

    hotels = plan.get("recommended_hotels", [])
    if hotels:
        lines.append("## Recommended Hotels")
        for hotel in hotels:
            if isinstance(hotel, dict):
                lines.append(f"- {hotel.get('name', 'Hotel')}")
                if hotel.get("area"):
                    lines.append(f"  Area: {hotel['area']}")
                if hotel.get("price_range"):
                    lines.append(f"  Price Range: {hotel['price_range']}")
                near_places = hotel.get("near_places", [])
                if near_places:
                    lines.append(f"  Near: {', '.join(near_places)}")
                if hotel.get("why_it_matches"):
                    lines.append(f"  Why it matches: {hotel['why_it_matches']}")
            else:
                lines.append(f"- {hotel}")
        lines.append("")

    for heading, key in (
        ("Food Suggestions", "food_suggestions"),
        ("Local Transport", "local_transport"),
        ("Travel Tips", "travel_tips"),
        ("Packing Checklist", "packing_checklist"),
    ):
        items = plan.get(key, [])
        if items:
            lines.append(f"## {heading}")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    breakdown = plan.get("budget_breakdown", {})
    if breakdown:
        lines.append("## Budget Breakdown")
        for key, value in breakdown.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    return "\n".join(lines).strip()
