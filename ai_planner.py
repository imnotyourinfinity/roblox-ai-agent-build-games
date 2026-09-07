"""
ai_planner.py

Talks to the Google Gemini API to:
1. Turn a high-level prompt into a list of build/script tasks (planning step)
2. Generate the actual data for each task (parts to build, or Lua script source)

All responses are requested as strict JSON so they can be parsed directly
into the rbxlx builder.

NOTE: This currently uses Gemini's free tier for testing. Once the pipeline
is reliable end-to-end, consider swapping to a stronger model (e.g. Claude)
for better game/script quality - only this file needs to change.
"""

import json
import os
import google.generativeai as genai

# Free-tier-friendly model. See ai.google.dev/pricing for current limits.
MODEL = "gemini-2.5-flash"

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def _call_ai(system_prompt: str, user_prompt: str) -> dict:
    """Send a prompt to Gemini and parse the response as JSON."""
    model = genai.GenerativeModel(MODEL, system_instruction=system_prompt)
    response = model.generate_content(
        user_prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    text = response.text.strip()
    # Strip markdown code fences just in case
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def plan_game(prompt: str) -> list:
    """
    Break a high-level game idea into an ordered list of tasks.
    Each task is either a "build" task (geometry) or a "script" task (logic).
    """
    system_prompt = (
        "You are a Roblox game design planner. Given a game idea, break it down "
        "into a small ordered list of concrete tasks needed to build it. "
        "Respond with ONLY valid JSON, no markdown, no explanation. "
        "Format: "
        '{"tasks": [{"id": "task_1", "type": "build", "name": "...", '
        '"description": "..."}, {"id": "task_2", "type": "script", '
        '"name": "...", "description": "..."}]}. '
        "Keep the plan small enough to be buildable (roughly 5-15 tasks). "
        "type must be either 'build' or 'script'."
    )
    result = _call_ai(system_prompt, f"Game idea: {prompt}")
    return result["tasks"]


def generate_build_task(task: dict, prompt: str) -> list:
    """
    Generate concrete part data for a 'build' task.
    Returns a list of part dicts: name, shape, size, position, color, material, anchored.
    """
    system_prompt = (
        "You are a Roblox level builder. Given a build task, output the exact "
        "parts needed as JSON, no markdown, no explanation. "
        'Format: {"parts": [{"name": "...", "shape": "Block|Ball|Cylinder", '
        '"size": [x,y,z], "position": [x,y,z], '
        '"color": [r,g,b] (0-255 each), "material": "Plastic|Wood|Metal|...", '
        '"anchored": true}]}. '
        "Keep coordinates reasonable (within a few hundred studs of the origin) "
        "and make sure pieces for the same task don't overlap incorrectly."
    )
    user_prompt = (
        f"Overall game: {prompt}\n"
        f"Task: {task['name']} - {task['description']}"
    )
    result = _call_ai(system_prompt, user_prompt)
    return result["parts"]


def generate_script_task(task: dict, prompt: str) -> dict:
    """
    Generate a Lua script for a 'script' task.
    Returns dict: name, parent, script_type (Script|LocalScript), source.
    """
    system_prompt = (
        "You are a Roblox Lua scripter. Given a script task, output the script "
        "as JSON, no markdown, no explanation. "
        'Format: {"name": "...", "parent": "ServerScriptService|Workspace|...", '
        '"script_type": "Script|LocalScript", "source": "-- lua code here"}. '
        "Write working, idiomatic Roblox Lua. Escape newlines properly in the JSON string."
    )
    user_prompt = (
        f"Overall game: {prompt}\n"
        f"Task: {task['name']} - {task['description']}"
    )
    return _call_ai(system_prompt, user_prompt)


def fix_script(source: str, error_message: str) -> str:
    """
    Given a script's source and an error message from Roblox's output,
    ask the AI to fix it. Returns corrected Lua source.
    """
    system_prompt = (
        "You are a Roblox Lua debugger. Given broken Lua code and its error "
        "message, output ONLY the corrected Lua source code, no markdown, "
        "no explanation, no JSON wrapper - just the raw fixed code."
    )
    model = genai.GenerativeModel(MODEL, system_instruction=system_prompt)
    response = model.generate_content(f"Error: {error_message}\n\nBroken code:\n{source}")
    text = response.text.strip()
    return text.removeprefix("```lua").removeprefix("```").removesuffix("```").strip()
