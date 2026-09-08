"""
main.py

Entry point for the Roblox AI agent.

Usage:
    python main.py "a simple obby with 10 levels and a leaderboard"
    python main.py                     <- no prompt: the AI invents its own idea

Pipeline:
0. (Optional) Idea - if no prompt is given, the AI invents its own concept
1. Plan   - break the prompt into an ordered list of build/script tasks
2. Generate - call the AI for each task's concrete data (parts or Lua)
3. Build  - assemble everything into a .rbxlx place file
4. Publish - upload the place file to Roblox via Open Cloud
"""

import sys

from ai_planner import plan_game, generate_all_builds, generate_all_scripts
from rbxlx_builder import build_place_xml
from roblox_publisher import publish_place
from idea_generator import generate_idea
from pool_manager import get_next_place


def run(prompt: str):
    print(f"Planning game: {prompt}")
    tasks = plan_game(prompt)
    print(f"Got {len(tasks)} tasks:")
    for t in tasks:
        print(f"  - [{t['type']}] {t['name']}")

    build_tasks = [t for t in tasks if t["type"] == "build"]
    script_tasks = [t for t in tasks if t["type"] == "script"]

    print(f"Generating {len(build_tasks)} build task(s) in one call...")
    all_parts = generate_all_builds(build_tasks, prompt)

    print(f"Generating {len(script_tasks)} script task(s) in one call...")
    all_scripts = generate_all_scripts(script_tasks, prompt)

    print(f"Building place file with {len(all_parts)} parts and {len(all_scripts)} scripts...")
    xml_content = build_place_xml(all_parts, all_scripts)

    with open("generated_place.rbxlx", "w", encoding="utf-8") as f:
        f.write(xml_content)
    print("Saved generated_place.rbxlx for inspection.")

    place = get_next_place()
    print(f"Publishing to Roblox (universe {place['universe_id']}, place {place['place_id']})...")
    result = publish_place(xml_content, place["universe_id"], place["place_id"])
    print(f"Done. Published version: {result.get('versionNumber')}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1].strip():
        run(sys.argv[1])
    else:
        print("No prompt given - letting the AI invent its own game idea...")
        run(generate_idea())
