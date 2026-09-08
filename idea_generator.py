"""
idea_generator.py

Lets the agent invent its own game concept instead of you supplying a
prompt each run. Picks freely from a mix of genres and avoids repeating
past ideas by checking against idea_history.json.
"""

import json
import os
import google.generativeai as genai

MODEL = "gemini-3.5-flash-lite"
HISTORY_FILE = "idea_history.json"

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

GENRE_POOL = [
    "obby/parkour", "tycoon", "simulator", "horror/escape",
    "roleplay/hangout", "battle arena", "puzzle", "racing",
    "tower defense", "adventure/exploration",
]


def _load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def _save_history(history: list):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def generate_idea() -> str:
    """
    Ask the AI to invent a fresh game concept, picking its own genre from
    the pool, avoiding anything already in idea_history.json. Returns a
    prompt string ready to feed into ai_planner.plan_game(), and records
    the new idea to history.
    """
    history = _load_history()
    past_titles = [h["title"] for h in history]

    system_prompt = (
        "You are a creative Roblox game designer. Invent ONE new game "
        "concept. Pick whichever genre fits your inspiration from this "
        "list (or blend a couple): " + ", ".join(GENRE_POOL) + ". "
        "Do not repeat any of these already-used titles/concepts: "
        + (", ".join(past_titles) if past_titles else "(none yet)") + ". "
        "Respond with ONLY valid JSON, no markdown: "
        '{"title": "short catchy game name", "genre": "...", '
        '"prompt": "a 1-3 sentence description detailed enough to build from"}'
    )

    model = genai.GenerativeModel(MODEL, system_instruction=system_prompt)
    response = model.generate_content(
        "Invent a new game concept now.",
        generation_config={"response_mime_type": "application/json"},
        request_options={"timeout": 120},
    )
    text = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    idea = json.loads(text)

    history.append({"title": idea["title"], "genre": idea["genre"]})
    _save_history(history)

    print(f"AI picked idea: [{idea['genre']}] {idea['title']}")
    return idea["prompt"]
