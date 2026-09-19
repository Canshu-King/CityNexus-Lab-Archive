from pathlib import Path

target = Path("D:/moodle/CityNexus/backend/app/planning/anchor_schedule.py")
src = target.read_text(encoding="utf-8")
block = Path("D:/moodle/_v1922_work/new_block.py").read_text(encoding="utf-8")

start = src.find("def _merge_anchors(")
end = src.find("def anchor_assignment_for_activities(")
assert start != -1 and end != -1 and start < end, (start, end)
new_src = src[:start] + block.rstrip("\n") + "\n\n\n" + src[end:]
target.write_text(new_src, encoding="utf-8", newline="\n")
import ast
ast.parse(new_src)
print("替换完成，语法 ok；新行数:", len(new_src.splitlines()))
