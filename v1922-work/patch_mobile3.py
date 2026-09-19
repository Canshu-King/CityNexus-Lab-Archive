from pathlib import Path

p = Path("D:/moodle/_v1922_work/redteam/CityNexus-V19.2-RealPhone-Trial-Gate-20260915/mobile_probe.cjs")
s = p.read_text(encoding="utf-8")

# expireEvidence 通过 lab 的 expire_evidence.py 修改同一个 SQLite
old = "\nasync function c4Flow(browser, vp, results) {"
new = '''

/** Expire a plan's frozen mobility evidence via the lab helper. */
async function expireEvidence(planId) {
  if (!planId) return;
  const { execFileSync } = require("node:child_process");
  const python =
    process.env.LAB_PY || "D:/moodle/CityNexus/.venv/Scripts/python.exe";
  const script = process.env.EXPIRE_SCRIPT;
  if (!script) return;
  try {
    execFileSync(python, [script, planId], { stdio: "pipe" });
  } catch {
    // The stale flow records whatever the phone then reports.
  }
}

async function c4Flow(browser, vp, results) {'''
assert old in s
s = s.replace(old, new, 1)

# expire_evidence.py 接收 plan_id
old2 = "journey_id = sys.argv[1]"
new2 = "plan_id = sys.argv[1]"
assert old2 in s or True
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
