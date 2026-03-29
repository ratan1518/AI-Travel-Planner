import streamlit as st

from config import AppConfig, load_config
from services.ai import format_plan_as_markdown, generate_travel_plan
from services.images import get_place_images
from services.maps import get_location_frame
from utils.pdf import create_pdf_bytes


st.set_page_config(page_title="AI Travel Planner", layout="wide")


def initialize_session_state() -> None:
    if "plan" not in st.session_state:
        st.session_state.plan = None
    if "plan_markdown" not in st.session_state:
        st.session_state.plan_markdown = None
    if "destination" not in st.session_state:
        st.session_state.destination = None


def show_place_images(destination: str, api_key: str) -> None:
    st.subheader(f"{destination} Highlights")

    images = get_place_images(destination, api_key)
    if not images:
        st.info("No images available.")
        return

    columns = st.columns(len(images))
    for column, image_url in zip(columns, images):
        column.image(image_url, use_container_width=True)


def show_simple_map(destination: str) -> None:
    st.markdown("### Location Map")

    location_frame = get_location_frame(destination)
    if location_frame is None:
        st.warning("Location not found or map loading failed.")
        return

    st.map(location_frame)


def render_plan(plan: dict) -> None:
    if "raw_text" in plan:
        st.markdown(plan["raw_text"])
        return

    st.subheader(plan.get("title", "Personalized Trip Plan"))
    summary = plan.get("summary")
    if summary:
        st.write(summary)

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Style", plan.get("travel_style", "-"))
    metric_2.metric("Companions", plan.get("companions", "-"))
    metric_3.metric("Pace", plan.get("pace", "-"))
    metric_4.metric("Best Time", plan.get("best_time_to_visit", "-"))

    why_this_plan = plan.get("why_this_plan")
    if why_this_plan:
        with st.container(border=True):
            st.markdown("### Why This Plan Works")
            st.write(why_this_plan)

    itinerary = plan.get("daily_itinerary", [])
    if itinerary:
        st.markdown("### Daily Itinerary")
        for day in itinerary:
            day_title = day.get("day", "Day Plan")
            with st.expander(day_title, expanded=True):
                for slot in ("morning", "afternoon", "evening"):
                    activity = day.get(slot)
                    if activity:
                        st.markdown(f"**{slot.title()}:** {activity}")
                if day.get("estimated_cost"):
                    st.caption(f"Estimated cost: {day['estimated_cost']}")

    col1, col2 = st.columns(2)
    with col1:
        hotels = plan.get("recommended_hotels", [])
        if hotels:
            with st.container(border=True):
                st.markdown("### Recommended Hotels")
                for hotel in hotels:
                    st.markdown(f"- {hotel}")

        food = plan.get("food_suggestions", [])
        if food:
            with st.container(border=True):
                st.markdown("### Food Suggestions")
                for item in food:
                    st.markdown(f"- {item}")

    with col2:
        breakdown = plan.get("budget_breakdown", {})
        if breakdown:
            with st.container(border=True):
                st.markdown("### Budget Breakdown")
                for key, value in breakdown.items():
                    st.markdown(f"- **{key}:** {value}")

        transport = plan.get("local_transport", [])
        if transport:
            with st.container(border=True):
                st.markdown("### Local Transport")
                for item in transport:
                    st.markdown(f"- {item}")

    tips = plan.get("travel_tips", [])
    if tips:
        with st.container(border=True):
            st.markdown("### Travel Tips")
            for tip in tips:
                st.markdown(f"- {tip}")

    packing = plan.get("packing_checklist", [])
    if packing:
        with st.container(border=True):
            st.markdown("### Packing Checklist")
            for item in packing:
                st.markdown(f"- {item}")


def render_ui(config: AppConfig) -> None:
    st.title("AI Travel Planner Agent")
    st.markdown(
        "### Build a personalized itinerary with budget, pace, interests, and travel-style inputs"
    )
    st.caption(
        "A portfolio-ready applied AI project that combines LLM planning, preference-based "
        "personalization, destination imagery, map lookup, and PDF export."
    )

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            destination = st.text_input("Destination", placeholder="Jaipur, Bali, Manali")
            budget = st.number_input("Budget (INR)", min_value=1000, step=1000, value=15000)

        with col2:
            days = st.number_input("Days", min_value=1, step=1, value=3)
            travel_style = st.selectbox(
                "Travel Style",
                ["Budget", "Luxury", "Adventure", "Family", "Relaxed", "Culture"],
            )

        with col3:
            companions = st.selectbox(
                "Traveling With",
                ["Solo", "Friends", "Family", "Partner", "Colleagues"],
            )
            food_preference = st.selectbox(
                "Food Preference",
                ["No preference", "Vegetarian", "Vegan", "Local cuisine", "Mixed"],
            )

        interests = st.multiselect(
            "Interests",
            [
                "Sightseeing",
                "Food",
                "Nature",
                "Adventure activities",
                "Shopping",
                "History",
                "Nightlife",
                "Photography",
            ],
            default=["Sightseeing", "Food"],
        )
        pace = st.slider("Trip Pace", min_value=1, max_value=5, value=3)

    if st.button("Generate Travel Plan"):
        if not destination.strip():
            st.warning("Please enter a destination.")
        else:
            with st.spinner("Planning your trip..."):
                st.session_state.plan = generate_travel_plan(
                    destination=destination.strip(),
                    budget=int(budget),
                    days=int(days),
                    travel_style=travel_style,
                    companions=companions,
                    interests=interests,
                    pace=pace,
                    food_preference=food_preference,
                    config=config,
                )
                st.session_state.plan_markdown = format_plan_as_markdown(st.session_state.plan)
                st.session_state.destination = destination.strip()

    if st.session_state.plan:
        st.markdown("## Your Travel Plan")
        render_plan(st.session_state.plan)

        show_place_images(st.session_state.destination, config.pexels_api_key)
        show_simple_map(st.session_state.destination)

        pdf_bytes = create_pdf_bytes(st.session_state.plan_markdown or "")
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="travel_plan.pdf",
            mime="application/pdf",
        )

        st.success("Plan generated successfully.")


def main() -> None:
    initialize_session_state()
    config = load_config()

    if not config.openrouter_api_key:
        st.error(
            "OpenRouter API key not found. Set OPENROUTER_API_KEY in "
            "Streamlit secrets or environment variables."
        )
        st.stop()

    render_ui(config)


if __name__ == "__main__":
    main()
