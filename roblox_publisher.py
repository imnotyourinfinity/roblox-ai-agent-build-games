"""
roblox_publisher.py

Publishes a built .rbxlx place file to Roblox using the Open Cloud API.
Docs: https://create.roblox.com/docs/cloud/reference/Place

Requires:
- ROBLOX_API_KEY   (from the Creator Dashboard, with "universe-places:write" permission)
- ROBLOX_UNIVERSE_ID
- ROBLOX_PLACE_ID  (an existing empty place you created once in Studio)
"""

import os
import requests

API_KEY = os.environ["ROBLOX_API_KEY"]
UNIVERSE_ID = os.environ["ROBLOX_UNIVERSE_ID"]
PLACE_ID = os.environ["ROBLOX_PLACE_ID"]

PUBLISH_URL = (
    f"https://apis.roblox.com/universes/v1/{UNIVERSE_ID}"
    f"/places/{PLACE_ID}/versions?versionType=Published"
)


def publish_place(xml_content: str) -> dict:
    """
    Uploads the given .rbxlx XML content as a new published version
    of the target place. Returns the API's JSON response
    (includes the new versionNumber on success).
    """
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/xml",
    }
    response = requests.post(
        PUBLISH_URL,
        headers=headers,
        data=xml_content.encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()
