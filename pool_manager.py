"""
pool_manager.py

Manages a pool of pre-created, empty Roblox places so the agent can
publish a "new" game into an unused slot each run, without needing you to
create a place manually every time.

You create a batch of empty places once (see README), list them in
places_pool.json, and this module hands out one unused slot per run.
When the pool runs low, top it up with another batch.
"""

import json
import os

POOL_FILE = "places_pool.json"


def _load_pool() -> list:
    if not os.path.exists(POOL_FILE):
        raise FileNotFoundError(
            f"{POOL_FILE} not found. Create it with your batch of empty "
            "Roblox places - see README for the format."
        )
    with open(POOL_FILE, "r") as f:
        return json.load(f)


def _save_pool(pool: list):
    with open(POOL_FILE, "w") as f:
        json.dump(pool, f, indent=2)


def get_next_place() -> dict:
    """
    Returns the next unused place slot as {"universe_id", "place_id", "label"}
    and marks it used. Raises RuntimeError if the pool is exhausted.
    """
    pool = _load_pool()
    for slot in pool:
        if not slot.get("used", False):
            slot["used"] = True
            _save_pool(pool)
            unused_remaining = sum(1 for s in pool if not s.get("used", False))
            print(f"Using place '{slot.get('label', slot['place_id'])}' "
                  f"({unused_remaining} unused slots left after this one).")
            return slot
    raise RuntimeError(
        "No unused places left in the pool! Add more empty places to "
        f"{POOL_FILE} (create them in Studio, add their IDs, set used: false)."
    )
