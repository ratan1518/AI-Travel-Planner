import streamlit as st

from config import AppConfig, load_config
from services.ai import format_plan_as_markdown, generate_travel_plan
from services.images import get_place_images
from services.maps import get_location_frame
from utils.pdf import create_pdf_bytes


st.set_page_config(page_title="AI Travel Planner", layout="wide")


THEMES = {
    "Light": {
        "bg": "#f4efe6",
        "bg_accent": "#fff8f1",
        "panel": "rgba(255, 252, 247, 0.92)",
        "panel_solid": "#fffaf3",
        "text": "#1d2a38",
        "muted": "#66768a",
        "accent": "#c26d3f",
        "accent_2": "#245c69",
        "border": "rgba(36, 92, 105, 0.14)",
        "shadow": "0 20px 50px rgba(29, 42, 56, 0.09)",
        "hero": "linear-gradient(135deg, #fff6e9 0%, #f4efe6 46%, #edf6f7 100%)",
        "input_bg": "#fffdf9",
        "tab_bg": "#f8f2e9",
    },
    "Dark": {
        "bg": "#0b1220",
        "bg_accent": "#101a2c",
        "panel": "rgba(16, 24, 40, 0.92)",
        "panel_solid": "#101827",
        "text": "#eef4ff",
        "muted": "#a8b4c8",
        "accent": "#f4a261",
        "accent_2": "#70c1b3",
        "border": "rgba(255, 255, 255, 0.09)",
        "shadow": "0 24px 55px rgba(0, 0, 0, 0.34)",
        "hero": "linear-gradient(135deg, #121b2c 0%, #0f1726 46%, #13283a 100%)",
        "input_bg": "#0f1726",
        "tab_bg": "#132033",
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

        :root {{
            --bg: {theme["bg"]};
            --bg-accent: {theme["bg_accent"]};
            --panel: {theme["panel"]};
            --panel-solid: {theme["panel_solid"]};
            --text: {theme["text"]};
            --muted: {theme["muted"]};
            --accent: {theme["accent"]};
            --accent-2: {theme["accent_2"]};
            --border: {theme["border"]};
            --shadow: {theme["shadow"]};
            --input-bg: {theme["input_bg"]};
            --tab-bg: {theme["tab_bg"]};
        }}

        .stApp {{
            background:
                radial-gradient(circle at 12% 14%, rgba(255,255,255,0.08), transparent 22%),
                radial-gradient(circle at 88% 18%, rgba(255,255,255,0.05), transparent 20%),
                linear-gradient(180deg, var(--bg-accent), var(--bg));
            color: {theme["text"]};
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stToolbar"] {{
            right: 1rem;
        }}

        [data-testid="stAppViewBlockContainer"] {{
            padding-top: 2rem;
            max-width: 1180px;
        }}

        [data-testid="stSidebar"] {{
            background: var(--panel-solid);
            border-right: 1px solid var(--border);
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background: linear-gradient(180deg, var(--panel-solid), var(--bg));
        }}

        [data-testid="stSidebar"] * {{
            color: var(--text);
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--text) !important;
            letter-spacing: -0.02em;
        }}

        p, li, label, span {{
            color: var(--text);
        }}

        .stMarkdown a {{
            color: var(--accent);
        }}

        [data-testid="stMetric"] {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 1rem 1rem;
            box-shadow: var(--shadow);
        }}

        [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
            color: var(--text);
        }}

        .hero-card, .glass-card, .section-card, .feature-card {{
            background: var(--panel);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            border-radius: 28px;
            animation: fadeUp 0.55s ease both;
        }}

        .hero-card {{
            background-image: {theme["hero"]};
            padding: 2.4rem 2.3rem 2rem 2.3rem;
            margin-bottom: 1.2rem;
            overflow: hidden;
            position: relative;
        }}

        .hero-card::after {{
            content: "";
            position: absolute;
            right: -30px;
            top: -30px;
            width: 170px;
            height: 170px;
            border-radius: 50%;
            background: linear-gradient(135deg, {theme["accent"]}28, {theme["accent_2"]}22);
            filter: blur(2px);
        }}

        .hero-kicker {{
            display: inline-block;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 0.9rem;
        }}

        .hero-title {{
            font-size: clamp(2rem, 3.4vw, 3.6rem);
            line-height: 0.98;
            font-weight: 800;
            max-width: 820px;
            margin: 0 0 0.75rem 0;
            color: var(--text);
        }}

        .hero-copy {{
            font-size: 1rem;
            line-height: 1.8;
            color: var(--muted);
            max-width: 720px;
            margin-bottom: 1.2rem;
        }}

        .chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 0.25rem;
        }}

        .chip {{
            border-radius: 999px;
            padding: 0.48rem 0.88rem;
            border: 1px solid var(--border);
            background: rgba(255,255,255,0.08);
            color: var(--text);
            font-size: 0.84rem;
            font-weight: 700;
        }}

        .section-card {{
            border-radius: 24px;
            padding: 1.15rem 1.2rem;
            margin-bottom: 1rem;
        }}

        .mini-title {{
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.9rem;
            margin: 0.9rem 0 1.2rem 0;
        }}

        .feature-card {{
            padding: 1rem 1rem 1.1rem 1rem;
            min-height: 118px;
        }}

        .feature-card h4 {{
            margin: 0 0 0.45rem 0;
            color: var(--text);
            font-size: 1rem;
        }}

        .feature-card p {{
            margin: 0;
            color: var(--muted);
            line-height: 1.55;
            font-size: 0.95rem;
        }}

        .stButton > button, .stDownloadButton > button {{
            width: 100%;
            border-radius: 18px;
            border: 1px solid transparent;
            color: {"#0f172a" if theme_name == "Dark" else "#fffaf3"};
            font-weight: 800;
            padding: 0.85rem 1rem;
            background: {"linear-gradient(135deg, var(--accent), var(--accent-2))" if theme_name == "Dark" else "linear-gradient(135deg, #b76a42, #cc8453)"};
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }}

        .stButton > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 16px 32px rgba(0, 0, 0, 0.22);
        }}

        .stTextInput input, .stNumberInput input {{
            border-radius: 16px !important;
            background: var(--input-bg) !important;
            border: 1px solid var(--border) !important;
            color: var(--text) !important;
            box-shadow: none !important;
        }}

        .stTextInput input::placeholder,
        .stNumberInput input::placeholder {{
            color: var(--muted) !important;
        }}

        [data-testid="stNumberInput"] {{
            background: transparent !important;
        }}

        [data-testid="stNumberInput"] button {{
            background: var(--input-bg) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 14px !important;
            box-shadow: none !important;
        }}

        [data-testid="stNumberInput"] button:hover {{
            border-color: var(--accent) !important;
            color: var(--accent) !important;
        }}

        .stSelectbox div[data-baseweb="select"],
        .stMultiSelect div[data-baseweb="select"] {{
            border-radius: 16px !important;
            background: var(--input-bg) !important;
            border: 1px solid var(--border) !important;
            box-shadow: none !important;
        }}

        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {{
            color: var(--text) !important;
            background: var(--input-bg) !important;
        }}

        .stSelectbox svg, .stMultiSelect svg {{
            fill: var(--text) !important;
        }}

        .stSlider [data-baseweb="slider"] {{
            padding-top: 0.5rem;
        }}

        .stRadio > div {{
            gap: 0.6rem;
        }}

        .stRadio label {{
            background: var(--input-bg);
            padding: 0.55rem 0.8rem;
            border-radius: 999px;
            border: 1px solid var(--border);
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem;
            margin-bottom: 0.8rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 999px;
            padding: 0.52rem 1rem;
            background: var(--tab-bg);
            border: 1px solid var(--border);
            color: var(--text);
        }}

        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
            color: {"#0f172a" if theme_name == "Dark" else "#fffaf3"} !important;
            border-color: transparent !important;
            font-weight: 800 !important;
        }}

        .stExpander, [data-testid="stExpander"] {{
            border: 1px solid var(--border);
            border-radius: 20px;
            background: var(--panel);
            overflow: hidden;
            box-shadow: var(--shadow);
        }}

        details[data-testid="stExpander"] summary,
        .streamlit-expanderHeader {{
            background: var(--panel-solid) !important;
            color: var(--text) !important;
            border-bottom: 1px solid var(--border) !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }}

        details[data-testid="stExpander"] summary:hover,
        .streamlit-expanderHeader:hover {{
            color: var(--accent) !important;
        }}

        details[data-testid="stExpander"] summary p,
        details[data-testid="stExpander"] summary span,
        .streamlit-expanderHeader p,
        .streamlit-expanderHeader span {{
            color: var(--text) !important;
            opacity: 1 !important;
        }}

        details[data-testid="stExpander"] > div {{
            background: var(--panel) !important;
        }}

        [data-testid="stAlert"] {{
            border-radius: 18px;
        }}

        div[data-testid="stCaptionContainer"] p, small {{
            color: var(--muted) !important;
        }}

        .block-container {{
            padding-top: 1.5rem;
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
            <div class="hero-kicker">Curated Journey Design</div>
            <div class="hero-title">A premium AI travel planner with a calmer, more refined interface.</div>
            <div class="hero-copy">
                Shape the trip around style, pace, interests, and company. Review your plan through
                elegant sections, then export a polished report when it feels right.
            </div>
            <div class="chip-row">
                <span class="chip">Adaptive Themes</span>
                <span class="chip">Curated Itineraries</span>
                <span class="chip">Visual Discovery</span>
                <span class="chip">Styled Export</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intro_grid() -> None:
    st.markdown(
        """
        <div class="info-grid">
            <div class="feature-card">
                <h4>Preference-Led Planning</h4>
                <p>The itinerary shifts with budget, travel style, pace, and food choices.</p>
            </div>
            <div class="feature-card">
                <h4>Editorial Layout</h4>
                <p>Daily plans, budget details, travel tips, and transport stay organized and readable.</p>
            </div>
            <div class="feature-card">
                <h4>Recruiter-Friendly Polish</h4>
                <p>The interface now feels closer to a finished product than a default prototype.</p>
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
    st.markdown(f"### {title}")
    columns = st.columns(2)
    for index, item in enumerate(items):
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{title[:-1] if title.endswith('s') else title}**")
                st.caption(item)


def render_hotel_section(hotels: list) -> None:
    if not hotels:
        return

    st.markdown("### Recommended Hotels")
    for hotel in hotels:
        if isinstance(hotel, dict):
            near_places = hotel.get("near_places", [])
            near_places_text = ", ".join(near_places) if near_places else "Selected itinerary areas"
            st.markdown(
                f"""
                <div class="section-card">
                    <div class="mini-title">{hotel.get("area", "Recommended Area")}</div>
                    <div style="font-size:1.08rem; font-weight:800; margin-bottom:0.35rem;">{hotel.get("name", "Hotel")}</div>
                    <div style="color:var(--muted); margin-bottom:0.35rem;">
                        <strong>Price range:</strong> {hotel.get("price_range", "Budget matched")}
                    </div>
                    <div style="color:var(--muted); margin-bottom:0.35rem;">
                        <strong>Near:</strong> {near_places_text}
                    </div>
                    <div style="line-height:1.65;">{hotel.get("why_it_matches", "")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            with st.container(border=True):
                st.markdown(f"- {hotel}")


def render_budget_section(breakdown: dict) -> None:
    if not breakdown:
        return
    st.markdown("### Budget Breakdown")
    columns = st.columns(2)
    entries = list(breakdown.items())
    for index, (key, value) in enumerate(entries):
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{key}**")
                st.markdown(f"### {value}")


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
            render_hotel_section(plan.get("recommended_hotels", []))
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
                <div class="mini-title">Planning Flow</div>
                <div style="font-size:1.1rem; font-weight:800;">Create a travel brief, then review a polished itinerary.</div>
                <div style="margin-top:0.45rem; color:inherit; opacity:0.82; line-height:1.7;">
                    Use the sidebar to define the trip. The planner turns those inputs into a structured
                    result that feels easier to scan, compare, and present.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="glass-card" style="padding:1.1rem 1.2rem; margin-bottom:1rem;">
                <div class="mini-title">Design Notes</div>
                <div class="chip-row">
                    <span class="chip">Elegant spacing</span>
                    <span class="chip">Coherent light mode</span>
                    <span class="chip">Focused tabs</span>
                    <span class="chip">Premium export</span>
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
