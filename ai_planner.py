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
import time
import google.generativeai as genai
from google.api_core.exceptions import DeadlineExceeded, ServiceUnavailable, ResourceExhausted

# Free-tier-friendly model. See ai.google.dev/pricing for current limits.
MODEL = "gemini-3.5-flash-lite"
REQUEST_TIMEOUT = 120
MAX_RETRIES = 3

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def _call_ai(system_prompt: str, user_prompt: str) -> dict:
    """Send a prompt to Gemini and parse the response as JSON, retrying on
    transient timeouts/server errors (but not on quota errors - those need
    an actual wait, not a fast retry)."""
    model = genai.GenerativeModel(MODEL, system_instruction=system_prompt)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = model.generate_content(
                user_prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options={"timeout": REQUEST_TIMEOUT},
            )
            text = response.text.strip()
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(text)
        except (DeadlineExceeded, ServiceUnavailable) as e:
            last_error = e
            wait = 10 * attempt
            print(f"  Attempt {attempt}/{MAX_RETRIES} timed out, retrying in {wait}s...")
            time.sleep(wait)
        except ResourceExhausted:
            # Quota errors won't fix themselves with a quick retry - fail fast
            raise

    raise last_error


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


def generate_all_builds(build_tasks: list, prompt: str) -> list:
    """
    Generate concrete part data for ALL 'build' tasks in a single AI call
    (instead of one call per task) to conserve free-tier request quota.
    Returns a flat list of part dicts.
    """
    if not build_tasks:
        return []

    system_prompt = (
        "You are a Roblox level builder. Given a list of build tasks, output "
        "the exact parts needed for ALL of them combined, as JSON, no "
        "markdown, no explanation. "
        'Format: {"parts": [{"name": "...", "shape": "Block|Ball|Cylinder", '
        '"size": [x,y,z], "position": [x,y,z], '
        '"color": [r,g,b] (0-255 each), "material": "Plastic|Wood|Metal|...", '
        '"anchored": true}]}. '
        "Keep coordinates reasonable (within a few hundred studs of the "
        "origin) and make sure parts across different tasks don't overlap "
        "incorrectly with each other."
    )
    task_list_text = "\n".join(
        f"- {t['name']}: {t['description']}" for t in build_tasks
    )
    user_prompt = f"Overall game: {prompt}\n\nBuild tasks:\n{task_list_text}"

    result = _call_ai(system_prompt, user_prompt)
    return result["parts"]


def generate_all_scripts(script_tasks: list, prompt: str) -> list:
    """
    Generate Lua scripts for ALL 'script' tasks in a single AI call
    (instead of one call per task) to conserve free-tier request quota.
    Returns a list of script dicts: name, parent, script_type, source.
    """
    if not script_tasks:
        return []

    system_prompt = (
        "You are a Roblox Lua scripter. Given a list of script tasks, output "
        "ALL of the needed scripts as JSON, no markdown, no explanation. "
        'Format: {"scripts": [{"name": "...", '
        '"parent": "ServerScriptService|Workspace|...", '
        '"script_type": "Script|LocalScript", "source": "-- lua code here"}]}. '
        "Write working, idiomatic Roblox Lua, one entry per task. "
        "Escape newlines properly in the JSON strings."
    )
    task_list_text = "\n".join(
        f"- {t['name']}: {t['description']}" for t in script_tasks
    )
    user_prompt = f"Overall game: {prompt}\n\nScript tasks:\n{task_list_text}"

    result = _call_ai(system_prompt, user_prompt)
    return result["scripts"]


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
    response = model.generate_content(
        f"Error: {error_message}\n\nBroken code:\n{source}",
        request_options={"timeout": REQUEST_TIMEOUT},
    )
    text = response.text.strip()
    return text.removeprefix("```lua").removeprefix("```").removesuffix("```").strip()
