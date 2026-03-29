import streamlit as st
from openai import OpenAI
import os
import requests
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from geopy.geocoders import Nominatim
import pandas as pd

# ---------- LOAD ENV ----------
load_dotenv()

# ---------- SAFE API KEY LOADING ----------
OPENROUTER_API_KEY = None
PEXELS_API_KEY = None

# Try Streamlit secrets (for deployment)
try:
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
    PEXELS_API_KEY = st.secrets["PEXELS_API_KEY"]
except:
    pass

# Fallback to .env (for local)
if not OPENROUTER_API_KEY:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not PEXELS_API_KEY:
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# FINAL CHECK
if not OPENROUTER_API_KEY:
    st.error("❌ API key not found.\n\n👉 Fix:\n1. Create .env file\n2. Or add Streamlit secrets")
    st.stop()

# ---------- CLIENT ----------
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# ---------- SESSION STATE ----------
if "result" not in st.session_state:
    st.session_state.result = None
if "destination" not in st.session_state:
    st.session_state.destination = None

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="AI Travel Planner", layout="wide")

# ---------- UI ----------
st.title("✈️ AI Travel Planner Agent")
st.markdown("### 🌍 Plan your perfect trip with AI")

col1, col2, col3 = st.columns(3)

with col1:
    destination = st.text_input("📍 Destination")

with col2:
    budget = st.number_input("💰 Budget (₹)", min_value=1000)

with col3:
    days = st.number_input("📅 Days", min_value=1)

# ---------- AI FUNCTION ----------
def generate_itinerary(destination, budget, days):
    try:
        day_format = ""
        for i in range(1, days + 1):
            day_format += f"\nDay {i}:\n- Place:\n- Place:\n"

        prompt = f"""
        Plan a {days}-day trip to {destination} within ₹{budget}.

        Format:
        {day_format}

        Include:
        Hotels
        Budget Breakdown
        Food Suggestions
        Travel Tips
        """

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=20
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---------- IMAGE ----------
def get_place_images(destination):
    try:
        if not PEXELS_API_KEY:
            return []

        url = f"https://api.pexels.com/v1/search?query={destination}&per_page=3"
        headers = {"Authorization": PEXELS_API_KEY}

        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()

        return [photo["src"]["large"] for photo in data.get("photos", [])]

    except:
        return []

def show_place_images(destination):
    st.subheader(f"📸 {destination} Highlights")

    images = get_place_images(destination)

    if not images:
        st.info("No images available")
        return

    cols = st.columns(len(images))
    for i, img in enumerate(images):
        cols[i].image(img, use_container_width=True)

# ---------- MAP ----------
def show_simple_map(destination):
    st.markdown("### 🗺️ Location Map")

    try:
        geolocator = Nominatim(user_agent="travel_app", timeout=10)
        location = geolocator.geocode(destination)

        if location:
            df = pd.DataFrame({
                "lat": [location.latitude],
                "lon": [location.longitude]
            })
            st.map(df)
        else:
            st.warning("Location not found")

    except:
        st.warning("Map loading failed")

# ---------- PDF ----------
def create_pdf(text):
    file_path = "travel_plan.pdf"
    doc = SimpleDocTemplate(file_path)

    styles = getSampleStyleSheet()
    content = []

    for line in text.split("\n"):
        content.append(Paragraph(line, styles["Normal"]))
        content.append(Spacer(1, 10))

    doc.build(content)
    return file_path

# ---------- BUTTON ----------
if st.button("✨ Generate Travel Plan"):
    if not destination:
        st.warning("⚠️ Please enter a destination")
    else:
        with st.spinner("🌍 Planning your trip..."):
            st.session_state.result = generate_itinerary(destination, budget, days)
            st.session_state.destination = destination

# ---------- OUTPUT ----------
if st.session_state.result:
    st.markdown("## 🧳 Your Travel Plan")
    st.markdown(st.session_state.result)

    show_place_images(st.session_state.destination)
    show_simple_map(st.session_state.destination)

    pdf_file = create_pdf(st.session_state.result)

    with open(pdf_file, "rb") as f:
        st.download_button("📄 Download PDF", f, "travel_plan.pdf")

    st.success("✅ Plan Generated Successfully!")