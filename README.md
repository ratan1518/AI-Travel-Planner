# AI Travel Planner

AI Travel Planner is a Streamlit-based portfolio project that generates personalized travel itineraries using LLMs, travel preferences, destination imagery, a simple map view, and PDF export.

## Why this project is useful

This project is designed to demonstrate:

- clean Python project structure
- practical LLM integration through OpenRouter
- user-personalized planning inputs
- external API usage for images and location mapping
- exportable output for a real user workflow

It is not presented as a heavy training-based ML system. Instead, it showcases applied AI product building, personalization logic, and deployment-ready engineering.

## Features

- destination, budget, and trip-duration planning
- personalized travel style selection
- companion-aware itinerary suggestions
- interest-based trip customization
- food preference input
- explanation of why the generated plan matches the selected preferences
- day-by-day structured itinerary output
- destination image gallery using Pexels
- destination map display using geopy and Streamlit
- downloadable PDF report

## Project structure

```text
project/
  streamlit_app.py
  config.py
  requirements.txt
  services/
    ai.py
    images.py
    maps.py
  utils/
    pdf.py
```

## Tech stack

- Python
- Streamlit
- OpenRouter via OpenAI SDK
- Pexels API
- geopy
- reportlab

## Setup

1. Open a terminal in:

```powershell
cd C:\Users\Lenovo\Downloads\Resume_Project\AI-Travel-Planner\project
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Create a secrets file at `project/.streamlit/secrets.toml`:

```toml
OPENROUTER_API_KEY = "your_openrouter_key"
PEXELS_API_KEY = "your_pexels_key"
APP_URL = "https://your-app-name.streamlit.app"
APP_TITLE = "AI Travel Planner"
OPENROUTER_MODEL = "openai/gpt-4o-mini"
```

4. Run the app:

```powershell
python -m streamlit run streamlit_app.py
```

## Portfolio talking points

- Built an AI-powered travel planning app with personalized itinerary generation
- Integrated LLM-based structured response generation with external image and map services
- Refactored a prototype into a modular Python application with services and utility layers
- Added PDF export and recruiter-friendly project documentation

## Recommended portfolio extras

- add 2-3 screenshots of the form, generated itinerary, and PDF export
- deploy the app on Streamlit Cloud and include the live link
- include the project link in your resume under AI or ML projects

## Future improvements

- deploy on Streamlit Cloud
- add itinerary saving/history
- add weather-aware suggestions
- add attraction cards with ratings and estimated local travel times
