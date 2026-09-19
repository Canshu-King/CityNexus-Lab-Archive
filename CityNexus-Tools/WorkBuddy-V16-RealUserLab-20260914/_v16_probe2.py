import json, urllib.request
BASE="http://127.0.0.1:8010/api/v1"
def req(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE+path, data=data, method=method, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]

def mk(city_code, city_name, tz, cur, budget, days=2, wake="00:00"):
    t=req("/travelers","POST",{"display_name":"u","locale":"zh-CN","timezone":tz})
    tid=t[1]["id"]
    start=f"2026-09-20T{wake}:00+08:00"
    j=req("/journeys","POST",{"traveler_id":tid,"title":f"{city_name} · journey","city_code":city_code,
      "timezone":tz,"start_at":start,"end_at":f"2026-09-{20+days}T00:00:00+08:00",
      "budget":{"amount_minor":budget,"currency":cur},"stay_budget":{"amount_minor":budget//2,"currency":cur},
      "party_size":2,"occupancy":{"adults":2,"rooms":1},
      "arrival_anchor":{"at":start,"location":city_name+"站"},
      "departure_anchor":{"at":f"2026-09-{20+days}T00:00:00+08:00","location":city_name+"站"}})
    return tid, j[1]["id"]

for cc, cn in [("CN-TIANJIN","天津"), ("CN-FUZHOU","福州"), ("CN-婺源","婺源")]:
    tid, jid = mk(cc, cn, "Asia/Shanghai", "CNY", 300000)
    s = req(f"/journeys/{jid}/stay-options/generate","POST",{"query":f"{cn} stay-aware journey"})
    print(f"\n===== {cc} ({cn}) generate -> {s[0]}")
    if s[0]==200:
        opts = s[1].get("options") or s[1]
        if isinstance(opts, dict): opts = opts.get("options", [])
        print("  options:", len(opts))
        if opts:
            o = opts[0]
            print("  keys:", sorted(o.keys()))
            print("  stay:", json.dumps(o.get("stay"), ensure_ascii=False)[:200])
            for d in o.get("days", [])[:2]:
                print("   day", d.get("day"), d.get("label"), d.get("anchor"), d.get("mode"))
                for a in d.get("activities", [])[:8]:
                    print("     ", a.get("start_at"), a.get("end_at"), a.get("title"), "| loc:", a.get("location"), "| locked:", a.get("locked"))
    else:
        print("  ERR", s[1][:300])
    print("  experience:", json.dumps(req(f"/journeys/{jid}/experience"), ensure_ascii=False)[:200])
