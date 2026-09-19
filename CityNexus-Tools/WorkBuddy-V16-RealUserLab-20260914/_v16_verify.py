import json, urllib.request, urllib.error
BASE="http://127.0.0.1:8010/api/v1"
def req(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE+path, data=data, method=method, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(r, timeout=180) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]

def mk(city_code, title, start, end, budget, cur, party, arr, dep):
    t=req("/travelers","POST",{"display_name":"u","locale":"zh-CN","timezone":"Asia/Shanghai"})
    tid=t[1]["id"]
    j=req("/journeys","POST",{"traveler_id":tid,"title":title,"city_code":city_code,
      "timezone":"Asia/Shanghai","start_at":start,"end_at":end,
      "budget":{"amount_minor":budget,"currency":cur},"stay_budget":{"amount_minor":budget//2,"currency":cur},
      "party_size":party,"occupancy":{"adults":party,"rooms":max(1,(party+1)//2)},
      "arrival_anchor":{"at":start,"location":arr},"departure_anchor":{"at":end,"location":dep}})
    return j[1]["id"]

def dump_plan(jid, label):
    ex = req(f"/journeys/{jid}/experience")
    opts = ex[1].get("options", [])
    print(f"--- {label}: options={len(opts)}")
    if not opts: return
    o = opts[0]
    print("    stay:", o["stay"]["property_name"], o["stay"]["room_type"])
    for d in o.get("days", []):
        ids = d.get("activities", [])
        print(f"    day {d['day']} {d.get('label')} {d.get('anchor')} {d.get('mode')} acts={len(ids)}")
    plan = ex[1].get("active_plan")
    if plan:
        for a in plan.get("activities", [])[:14]:
            print("      ", a.get("start_at"), "->", a.get("end_at"), "|", a.get("title"), "| locked", a.get("locked"))

def events(jid):
    s, b = req(f"/journeys/{jid}/events")
    return b if isinstance(b, list) else []

# ---------------- P01: late-riser couple in Fuzhou ----------------
jid = mk("CN-FUZHOU", "福州 · journey", "2026-10-09T11:30:00+08:00", "2026-10-12T19:00:00+08:00",
         600000, "CNY", 2, "福州站", "福州长乐机场")
print("journey", jid)
req(f"/journeys/{jid}/stay-options/generate","POST",{})
dump_plan(jid, "BEFORE any user message")
print("    events:", [(e['event_type'], e['severity']) for e in events(jid)])

SELF = "我和对象出来玩，晚上会折腾到很晚才睡，第二天基本 11 点才起。别给我排早上七八点的行程，早餐不用订，直接吃早午餐。"
s, r = req(f"/journeys/{jid}/agent/commands","POST",{"command":SELF,"requested_autonomy":"EXECUTE_WITHIN_BOUNDS"})
print(f"\n[agent/commands] self-description -> {s}")
print("    route:", json.dumps(r.get("route"), ensure_ascii=False) if isinstance(r,dict) else r)
print("    event_id:", r.get("event_id") if isinstance(r,dict) else None)
s2, r2 = req(f"/journeys/{jid}/guardian/mission","PUT",{"command":SELF,"requested_autonomy":"EXECUTE_WITHIN_BOUNDS"})
print(f"[guardian/mission] -> {s2}  options_regenerated={r2.get('options_regenerated') if isinstance(r2,dict) else r2}")
print("    day_rhythm:", json.dumps(r2.get("day_rhythm"), ensure_ascii=False) if isinstance(r2,dict) else None)
print("    events after self-description:", [(e['event_type'], e['severity']) for e in events(jid)])
dump_plan(jid, "AFTER rhythm learned")

# ---------------- hypothetical vs real ----------------
for msg in ["如果明天下雨会怎样？", "我想少走路。", "火车晚点三个小时，后面的行程全乱了。", "我护照丢了。", "博物馆关门了。"]:
    s3, r3 = req(f"/journeys/{jid}/agent/commands","POST",{"command":msg,"requested_autonomy":"EXECUTE_WITHIN_BOUNDS"})
    route = r3.get("route") if isinstance(r3,dict) else None
    print(f"\n[{s3}] {msg}")
    print("    intent=%s policy=%s creates_event=%s type=%s sev=%s" % (
        route.get("intent"), route.get("mutation_policy"), route.get("creates_event"),
        route.get("event_type"), route.get("severity")) if route else print("   ", str(r3)[:200]))
print("\nFINAL events:", [(e.get('event_type'), e.get('severity'), (e.get('payload_json') or '')[:60]) for e in events(jid)])

# ---------------- JPY zero-decimal ----------------
jid2 = mk("JP-TOKYO", "东京 · journey", "2026-10-09T07:10:00+09:00", "2026-10-11T20:00:00+09:00",
          3000000, "JPY", 1, "东京站", "羽田机场")
req(f"/journeys/{jid2}/stay-options/generate","POST",{})
ex = req(f"/journeys/{jid2}/experience")
o = (ex[1].get("options") or [None])[0]
if o:
    print("\nTOKYO stay total:", o["stay_total_minor"], "JPY | nightly:", o["stay"]["nightly_amount_minor"], "JPY | travel:", o["mobility_total_minor"])
    facts = ex[1].get("mobility_facts", [])
    paid = [f for f in facts if f.get("cost_amount_minor")]
    if paid:
        f = paid[0]
        print("TOKYO mobility fact:", f["mode"], f["cost_amount_minor"], f.get("currency"), f.get("cost_status"))
