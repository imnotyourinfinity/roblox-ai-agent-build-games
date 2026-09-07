"""
roblox_publisher.py

Publishes a built .rbxlx place file to Roblox using the Open Cloud API.
Docs: https://create.roblox.com/docs/cloud/reference/Place

Requires:
- ROBLOX_API_KEY  (from the Creator Dashboard, with "universe-places:write"
  permission, scoped to your Group's experiences)

universe_id / place_id are now passed in per-call (see pool_manager.py)
instead of being fixed - so the same key can publish into any place in
your pool.
"""

import os
import requests

API_KEY = os.environ["ROBLOX_API_KEY"]


def publish_place(xml_content: str, universe_id: str, place_id: str) -> dict:
    """
    Uploads the given .rbxlx XML content as a new published version
    of the given place. Returns the API's JSON response
    (includes the new versionNumber on success).
    """
    url = (
        f"https://apis.roblox.com/universes/v1/{universe_id}"
        f"/places/{place_id}/versions?versionType=Published"
    )
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/xml",
    }
    response = requests.post(
        url,
        headers=headers,
        data=xml_content.encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()
