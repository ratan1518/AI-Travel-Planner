import streamlit as st

from config import AppConfig, load_config
from services.ai import generate_itinerary
from services.images import get_place_images
from services.maps import get_location_frame
from utils.pdf import create_pdf_bytes


st.set_page_config(page_title="AI Travel Planner", layout="wide")


def initialize_session_state() -> None:
    if "result" not in st.session_state:
        st.session_state.result = None
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


def render_ui(config: AppConfig) -> None:
    st.title("AI Travel Planner Agent")
    st.markdown("### Plan your perfect trip with AI")

    col1, col2, col3 = st.columns(3)

    with col1:
        destination = st.text_input("Destination")

    with col2:
        budget = st.number_input("Budget (INR)", min_value=1000, step=1000)

    with col3:
        days = st.number_input("Days", min_value=1, step=1)

    if st.button("Generate Travel Plan"):
        if not destination.strip():
            st.warning("Please enter a destination.")
        else:
            with st.spinner("Planning your trip..."):
                st.session_state.result = generate_itinerary(
                    destination=destination.strip(),
                    budget=int(budget),
                    days=int(days),
                    config=config,
                )
                st.session_state.destination = destination.strip()

    if st.session_state.result:
        st.markdown("## Your Travel Plan")
        st.markdown(st.session_state.result)

        show_place_images(st.session_state.destination, config.pexels_api_key)
        show_simple_map(st.session_state.destination)

        pdf_bytes = create_pdf_bytes(st.session_state.result)
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
