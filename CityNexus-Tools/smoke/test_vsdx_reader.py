import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from vsdx import VisioFile


TARGET = Path(r"D:\moodle\CityNexus-Tools\smoke\visioautomation-smoke.vsdx")
OUTPUT = TARGET.with_name("vsdx-reader-result.json")


def shape_record(shape):
    return {
        "id": getattr(shape, "ID", None),
        "shape_name": getattr(shape, "shape_name", None),
        "shape_type": getattr(shape, "shape_type", None),
        "text": getattr(shape, "text", None),
        "width": getattr(shape, "width", None),
        "height": getattr(shape, "height", None),
        "child_count": len(getattr(shape, "child_shapes", []) or []),
        "children": [shape_record(child) for child in (getattr(shape, "child_shapes", []) or [])],
    }


def main():
    result = {"target": str(TARGET), "reader": "vsdx 0.6.1", "ok": False}
    try:
        with VisioFile(str(TARGET)) as vis:
            pages = []
            for index in range(len(vis.pages)):
                page = vis.get_page(index)
                pages.append({
                    "index": index,
                    "name": getattr(page, "name", None),
                    "width": page.width,
                    "height": page.height,
                    "shape_count": len(page.child_shapes),
                    "shapes": [shape_record(s) for s in page.child_shapes],
                    "connect_count": len(page.connects),
                    "connects_supported": True,
                })
        with zipfile.ZipFile(TARGET) as package:
            pages_xml = ET.fromstring(package.read("visio/pages/pages.xml"))
            raw_count = len(pages_xml.findall(".//{*}Page"))
        result.update({
            "ok": len(pages) == raw_count,
            "page_count": len(pages),
            "vsdx_page_count": len(pages),
            "raw_xml_page_count": raw_count,
            "pages": pages,
        })
        if len(pages) != raw_count:
            result["error"] = "vsdx page count does not match raw pages.xml"
            return 1
    except Exception as exc:  # smoke test should emit a machine-readable failure
        result.update({"error_type": type(exc).__name__, "error": str(exc)})
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
