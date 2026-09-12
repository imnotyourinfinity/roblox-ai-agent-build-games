"""
rbxlx_builder.py

Builds a Roblox .rbxlx (XML place file) by INSERTING AI-generated parts and
scripts into a real, known-valid place file (template.rbxlx) - rather than
constructing the XML from scratch.

Why: Roblox's place XML format is large and strict (every instance needs
boilerplate fields like UniqueId, SecurityCapabilities, SharedString tag
references, and a full place needs every default service present, or the
Open Cloud publish endpoint rejects it with "Invalid Content stream").
Patching a real Studio-exported file guarantees all of that stays intact -
we only touch the Workspace and ServerScriptService branches.

template.rbxlx should be a blank place saved from Studio via
File > Open from File > (your downloaded copy) > Save As > Roblox XML
Place Files (*.rbxlx). If you ever need to regenerate it, repeat that.
"""

import uuid
import xml.etree.ElementTree as ET

TEMPLATE_PATH = "template.rbxlx"

# Every instance in Roblox's XML format carries this same generic set of
# base properties, regardless of class. Reused for every new Part/Script.
ZERO_HISTORY_ID = "00000000000000000000000000000000"
SHARED_EMPTY_TAGS_MD5 = "yuZpQdnvvUBOTYh1jqZ2cA=="  # matches template.rbxlx's <SharedStrings> entry

SHAPE_MAP = {"Ball": "0", "Cylinder": "2", "Block": "1"}
MATERIAL_MAP = {
    "Plastic": "256", "Wood": "512", "Metal": "1088",
    "Concrete": "816", "Grass": "1280", "Sand": "1296",
    "Neon": "288", "Glass": "1568",
}


def _new_ref() -> str:
    return "RBX" + uuid.uuid4().hex.upper()


def _new_unique_id() -> str:
    return uuid.uuid4().hex


def _sub(parent, tag, name, text):
    el = ET.SubElement(parent, tag, {"name": name})
    el.text = text
    return el


def _add_generic_instance_properties(props_el, name: str):
    """The 7 base fields every instance seems to need, in the order
    template.rbxlx uses for simple instances."""
    _sub(props_el, "BinaryString", "AttributesSerialize", "")
    _sub(props_el, "SecurityCapabilities", "Capabilities", "0")
    _sub(props_el, "bool", "DefinesCapabilities", "false")
    _sub(props_el, "UniqueId", "HistoryId", ZERO_HISTORY_ID)
    _sub(props_el, "string", "Name", name)
    _sub(props_el, "int64", "SourceAssetId", "-1")
    _sub(props_el, "SharedString", "Tags", SHARED_EMPTY_TAGS_MD5)
    _sub(props_el, "UniqueId", "UniqueId", _new_unique_id())


def _add_coordinate_frame(props_el, tag_name, pos):
    cf = ET.SubElement(props_el, "CoordinateFrame", {"name": tag_name})
    for axis, val in zip(("X", "Y", "Z"), pos):
        ET.SubElement(cf, axis).text = str(val)
    # Identity rotation matrix (axis-aligned, no rotation)
    for r in ("R00", "R01", "R02", "R10", "R11", "R12", "R20", "R21", "R22"):
        ET.SubElement(cf, r).text = "1" if r in ("R00", "R11", "R22") else "0"


def _pack_color3uint8(rgb) -> str:
    """Roblox stores Color3uint8 as one packed 32-bit int: 0xFFRRGGBB."""
    r, g, b = (max(0, min(255, int(c))) for c in rgb)
    return str((0xFF << 24) | (r << 16) | (g << 8) | b)


def _build_part_element(part: dict) -> ET.Element:
    item = ET.Element("Item", {"class": "Part", "referent": _new_ref()})
    props = ET.SubElement(item, "Properties")

    shape = SHAPE_MAP.get(part.get("shape", "Block"), "1")
    material = MATERIAL_MAP.get(part.get("material", "Plastic"), "256")
    anchored = "true" if part.get("anchored", True) else "false"
    size = part.get("size", [4, 4, 4])
    pos = part.get("position", [0, 0, 0])
    color = part.get("color", [163, 162, 165])

    _sub(props, "token", "shape", shape)
    _sub(props, "bool", "Anchored", anchored)
    _sub(props, "bool", "CanCollide", "true")
    _add_coordinate_frame(props, "CFrame", pos)
    _sub(props, "Color3uint8", "Color3uint8", _pack_color3uint8(color))
    _sub(props, "token", "Material", material)

    size_el = ET.SubElement(props, "Vector3", {"name": "size"})
    for axis, val in zip(("X", "Y", "Z"), size):
        ET.SubElement(size_el, axis).text = str(val)

    _add_generic_instance_properties(props, part.get("name", "Part"))
    return item


def _build_script_element(script: dict) -> ET.Element:
    script_class = script.get("script_type", "Script")
    item = ET.Element("Item", {"class": script_class, "referent": _new_ref()})
    props = ET.SubElement(item, "Properties")

    _sub(props, "ProtectedString", "Source", script.get("source", ""))
    _add_generic_instance_properties(props, script.get("name", "Script"))
    return item


def build_place_xml(parts: list, scripts: list) -> str:
    """
    Loads template.rbxlx, appends the given parts into Workspace and the
    given scripts into ServerScriptService (or Workspace, for LocalScripts
    that need to run client-side), and returns the resulting XML as a
    string ready to publish.
    """
    tree = ET.parse(TEMPLATE_PATH)
    root = tree.getroot()

    workspace = root.find('./Item[@class="Workspace"]')
    server_scripts_service = root.find('./Item[@class="ServerScriptService"]')
    if workspace is None or server_scripts_service is None:
        raise RuntimeError(
            f"{TEMPLATE_PATH} is missing Workspace or ServerScriptService - "
            "make sure it's a full place file exported from Studio."
        )

    for part in parts:
        workspace.append(_build_part_element(part))

    for script in scripts:
        target = workspace if script.get("parent") == "Workspace" else server_scripts_service
        target.append(_build_script_element(script))

    return ET.tostring(root, encoding="unicode")
