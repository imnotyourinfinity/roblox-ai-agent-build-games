"""
main.py

Entry point for the Roblox AI agent.

Usage:
    python main.py "a simple obby with 10 levels and a leaderboard"

Pipeline:
1. Plan   - break the prompt into an ordered list of build/script tasks
2. Generate - call the AI for each task's concrete data (parts or Lua)
3. Build  - assemble everything into a .rbxlx place file
4. Publish - upload the place file to Roblox via Open Cloud
"""

import sys

from ai_planner import plan_game, generate_build_task, generate_script_task
from rbxlx_builder import build_place_xml
from roblox_publisher import publish_place


def run(prompt: str):
    print(f"Planning game: {prompt}")
    tasks = plan_game(prompt)
    print(f"Got {len(tasks)} tasks:")
    for t in tasks:
        print(f"  - [{t['type']}] {t['name']}")

    all_parts = []
    all_scripts = []

    for task in tasks:
        print(f"Generating: {task['name']} ({task['type']})")
        if task["type"] == "build":
            parts = generate_build_task(task, prompt)
            all_parts.extend(parts)
        elif task["type"] == "script":
            script = generate_script_task(task, prompt)
            all_scripts.append(script)
        else:
            print(f"  Unknown task type '{task['type']}', skipping.")

    print(f"Building place file with {len(all_parts)} parts and {len(all_scripts)} scripts...")
    xml_content = build_place_xml(all_parts, all_scripts)

    print("Publishing to Roblox...")
    result = publish_place(xml_content)
    print(f"Done. Published version: {result.get('versionNumber')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python main.py "your game idea here"')
        sys.exit(1)
    run(sys.argv[1])
