import streamlit as st

from config import AppConfig, load_config
from services.ai import format_plan_as_markdown, generate_travel_plan
from services.images import get_place_images
from services.maps import get_location_frame
from utils.pdf import create_pdf_bytes


st.set_page_config(page_title="AI Travel Planner", layout="wide")


THEMES = {
    "Light": {
        "bg": "#f6f7fb",
        "panel": "rgba(255, 255, 255, 0.82)",
        "panel_solid": "#ffffff",
        "text": "#14213d",
        "muted": "#5c677d",
        "accent": "#ef8354",
        "accent_2": "#4f7cac",
        "border": "rgba(79, 124, 172, 0.18)",
        "shadow": "0 18px 45px rgba(20, 33, 61, 0.08)",
        "hero": "linear-gradient(135deg, rgba(239,131,84,0.18), rgba(79,124,172,0.18))",
    },
    "Dark": {
        "bg": "#10151f",
        "panel": "rgba(18, 25, 38, 0.82)",
        "panel_solid": "#141b29",
        "text": "#f4f7fb",
        "muted": "#b6c2d9",
        "accent": "#ffb703",
        "accent_2": "#6dd3ce",
        "border": "rgba(255, 255, 255, 0.08)",
        "shadow": "0 18px 45px rgba(0, 0, 0, 0.28)",
        "hero": "linear-gradient(135deg, rgba(255,183,3,0.18), rgba(109,211,206,0.18))",
    },
}


def initialize_session_state() -> None:
    if "plan" not in st.session_state:
        st.session_state.plan = None
    if "plan_markdown" not in st.session_state:
        st.session_state.plan_markdown = None
    if "destination" not in st.session_state:
        st.session_state.destination = None
    if "theme" not in st.session_state:
        st.session_state.theme = "Dark"


def apply_custom_theme(theme_name: str) -> None:
    theme = THEMES[theme_name]
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap');

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
            font-family: 'Manrope', sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(255,255,255,0.08), transparent 28%),
                radial-gradient(circle at bottom right, rgba(255,255,255,0.05), transparent 24%),
                {theme["bg"]};
            color: {theme["text"]};
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stSidebar"] {{
            background: {theme["panel_solid"]};
            border-right: 1px solid {theme["border"]};
        }}

        [data-testid="stSidebar"] * {{
            color: {theme["text"]};
        }}

        [data-testid="stMetric"] {{
            background: {theme["panel"]};
            border: 1px solid {theme["border"]};
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: {theme["shadow"]};
            backdrop-filter: blur(12px);
        }}

        [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
            color: {theme["text"]};
        }}

        .hero-card, .glass-card {{
            background: {theme["panel"]};
            border: 1px solid {theme["border"]};
            box-shadow: {theme["shadow"]};
            border-radius: 24px;
            backdrop-filter: blur(14px);
            animation: fadeUp 0.65s ease both;
        }}

        .hero-card {{
            background-image: {theme["hero"]};
            padding: 1.8rem 1.8rem 1.4rem 1.8rem;
            margin-bottom: 1.1rem;
            overflow: hidden;
            position: relative;
        }}

        .hero-card::after {{
            content: "";
            position: absolute;
            right: -60px;
            top: -50px;
            width: 190px;
            height: 190px;
            border-radius: 50%;
            background: linear-gradient(135deg, {theme["accent"]}22, {theme["accent_2"]}22);
            filter: blur(8px);
        }}

        .hero-kicker {{
            display: inline-block;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {theme["accent"]};
            margin-bottom: 0.9rem;
        }}

        .hero-title {{
            font-size: clamp(2rem, 3.4vw, 3.6rem);
            line-height: 1.03;
            font-weight: 800;
            max-width: 760px;
            margin: 0 0 0.75rem 0;
            color: {theme["text"]};
        }}

        .hero-copy {{
            font-size: 1rem;
            line-height: 1.7;
            color: {theme["muted"]};
            max-width: 760px;
            margin-bottom: 1rem;
        }}

        .chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 0.2rem;
        }}

        .chip {{
            border-radius: 999px;
            padding: 0.45rem 0.85rem;
            border: 1px solid {theme["border"]};
            background: rgba(255,255,255,0.06);
            color: {theme["text"]};
            font-size: 0.85rem;
            font-weight: 700;
        }}

        .section-card {{
            background: {theme["panel"]};
            border: 1px solid {theme["border"]};
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: {theme["shadow"]};
            backdrop-filter: blur(12px);
            animation: fadeUp 0.7s ease both;
        }}

        .mini-title {{
            color: {theme["muted"]};
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.8rem;
            margin: 0.8rem 0 1.1rem 0;
        }}

        .info-card {{
            background: {theme["panel"]};
            border: 1px solid {theme["border"]};
            border-radius: 18px;
            padding: 0.95rem;
            box-shadow: {theme["shadow"]};
            min-height: 118px;
        }}

        .info-card h4 {{
            margin: 0 0 0.45rem 0;
            color: {theme["text"]};
            font-size: 1rem;
        }}

        .info-card p {{
            margin: 0;
            color: {theme["muted"]};
            line-height: 1.55;
            font-size: 0.95rem;
        }}

        .stButton > button, .stDownloadButton > button {{
            width: 100%;
            border-radius: 16px;
            border: 1px solid transparent;
            color: #0f172a;
            font-weight: 800;
            padding: 0.8rem 1rem;
            background: linear-gradient(135deg, {theme["accent"]}, {theme["accent_2"]});
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }}

        .stButton > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 16px 32px rgba(0, 0, 0, 0.22);
        }}

        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"],
        .stMultiSelect div[data-baseweb="select"] {{
            border-radius: 14px !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 999px;
            padding: 0.5rem 1rem;
            background: {theme["panel"]};
            border: 1px solid {theme["border"]};
        }}

        .stExpander {{
            border: 1px solid {theme["border"]};
            border-radius: 18px;
            background: {theme["panel"]};
            overflow: hidden;
        }}

        div[data-testid="stCaptionContainer"] p, p, li, label {{
            color: {theme["text"]};
        }}

        @keyframes fadeUp {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">AI Travel Experience</div>
            <div class="hero-title">Plan smarter trips with a premium AI travel dashboard.</div>
            <div class="hero-copy">
                Personalize your itinerary by travel style, pace, interests, and companions.
                Explore a cleaner breakdown of your trip, then export a polished PDF in one click.
            </div>
            <div class="chip-row">
                <span class="chip">Dark / Light Mode</span>
                <span class="chip">Personalized Itineraries</span>
                <span class="chip">Maps + Visuals</span>
                <span class="chip">PDF Export</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intro_grid() -> None:
    st.markdown(
        """
        <div class="info-grid">
            <div class="info-card">
                <h4>Preference-Aware</h4>
                <p>The itinerary adapts to budget, travel style, trip pace, and food choices.</p>
            </div>
            <div class="info-card">
                <h4>Structured Output</h4>
                <p>Daily plans, budget breakdowns, local transport, and packing suggestions stay readable.</p>
            </div>
            <div class="info-card">
                <h4>Portfolio Ready</h4>
                <p>A polished interface makes the project feel more like a product and less like a demo.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_place_images(destination: str, api_key: str) -> None:
    images = get_place_images(destination, api_key)
    if not images:
        st.info("No images available.")
        return

    columns = st.columns(len(images))
    for column, image_url in zip(columns, images):
        with column:
            st.image(image_url, use_container_width=True)


def show_simple_map(destination: str) -> None:
    location_frame = get_location_frame(destination)
    if location_frame is None:
        st.warning("Location not found or map loading failed.")
        return
    st.map(location_frame)


def render_bullet_section(title: str, items: list[str]) -> None:
    if not items:
        return
    with st.container(border=True):
        st.markdown(f"### {title}")
        for item in items:
            st.markdown(f"- {item}")


def render_budget_section(breakdown: dict) -> None:
    if not breakdown:
        return
    with st.container(border=True):
        st.markdown("### Budget Breakdown")
        for key, value in breakdown.items():
            st.markdown(f"- **{key}:** {value}")


def render_plan(plan: dict) -> None:
    if "raw_text" in plan:
        st.markdown(plan["raw_text"])
        return

    st.markdown(f"## {plan.get('title', 'Personalized Trip Plan')}")

    summary = plan.get("summary")
    if summary:
        st.markdown(
            f"""
            <div class="section-card">
                <div class="mini-title">Trip Summary</div>
                <div>{summary}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

    overview_tab, itinerary_tab, essentials_tab, explore_tab = st.tabs(
        ["Overview", "Itinerary", "Essentials", "Explore"]
    )

    with overview_tab:
        col1, col2 = st.columns(2)
        with col1:
            render_bullet_section("Recommended Hotels", plan.get("recommended_hotels", []))
            render_bullet_section("Food Suggestions", plan.get("food_suggestions", []))
        with col2:
            render_budget_section(plan.get("budget_breakdown", {}))
            render_bullet_section("Local Transport", plan.get("local_transport", []))

    with itinerary_tab:
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
        else:
            st.info("No detailed itinerary available.")

    with essentials_tab:
        render_bullet_section("Travel Tips", plan.get("travel_tips", []))
        render_bullet_section("Packing Checklist", plan.get("packing_checklist", []))

    with explore_tab:
        st.markdown("### Destination Highlights")
        show_place_images(st.session_state.destination, st.session_state.pexels_api_key)
        st.markdown("### Location Map")
        show_simple_map(st.session_state.destination)


def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("## Customize")
        theme = st.radio("Theme", ["Dark", "Light"], index=["Dark", "Light"].index(st.session_state.theme))
        st.session_state.theme = theme

        st.markdown("---")
        destination = st.text_input("Destination", placeholder="Jaipur, Bali, Manali")
        budget = st.number_input("Budget (INR)", min_value=1000, step=1000, value=15000)
        days = st.number_input("Days", min_value=1, step=1, value=3)
        travel_style = st.selectbox(
            "Travel Style",
            ["Budget", "Luxury", "Adventure", "Family", "Relaxed", "Culture"],
        )
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
        generate = st.button("Generate Travel Plan")

        st.markdown("---")
        st.caption(
            "Trip pace controls how relaxed or packed the itinerary should feel. "
            "Lower values create more breathing room."
        )

    return {
        "destination": destination,
        "budget": int(budget),
        "days": int(days),
        "travel_style": travel_style,
        "companions": companions,
        "food_preference": food_preference,
        "interests": interests,
        "pace": pace,
        "generate": generate,
    }


def render_ui(config: AppConfig) -> None:
    st.session_state.pexels_api_key = config.pexels_api_key
    controls = render_sidebar()
    apply_custom_theme(st.session_state.theme)

    render_hero()
    render_intro_grid()

    left, right = st.columns([1.35, 0.95], gap="large")
    with left:
        st.markdown(
            """
            <div class="glass-card" style="padding:1.1rem 1.2rem; margin-bottom:1rem;">
                <div class="mini-title">Experience</div>
                <div style="font-size:1.1rem; font-weight:800;">Create a detailed travel plan in one flow</div>
                <div style="margin-top:0.45rem; color:inherit; opacity:0.82;">
                    Tune the controls from the sidebar, generate a personalized itinerary,
                    and explore the destination through organized tabs.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="glass-card" style="padding:1.1rem 1.2rem; margin-bottom:1rem;">
                <div class="mini-title">Highlights</div>
                <div class="chip-row">
                    <span class="chip">Animated cards</span>
                    <span class="chip">Theme toggle</span>
                    <span class="chip">Tabbed results</span>
                    <span class="chip">Styled PDF</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if controls["generate"]:
        if not controls["destination"].strip():
            st.warning("Please enter a destination.")
        else:
            with st.spinner("Designing your travel plan..."):
                st.session_state.plan = generate_travel_plan(
                    destination=controls["destination"].strip(),
                    budget=controls["budget"],
                    days=controls["days"],
                    travel_style=controls["travel_style"],
                    companions=controls["companions"],
                    interests=controls["interests"],
                    pace=controls["pace"],
                    food_preference=controls["food_preference"],
                    config=config,
                )
                st.session_state.plan_markdown = format_plan_as_markdown(st.session_state.plan)
                st.session_state.destination = controls["destination"].strip()

    if st.session_state.plan:
        render_plan(st.session_state.plan)
        pdf_bytes = create_pdf_bytes(st.session_state.plan_markdown or "")
        st.download_button(
            "Download Styled PDF",
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
