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

t=req("/travelers","POST",{"display_name":"City traveler","locale":"zh-CN","timezone":"Asia/Shanghai"})
tid=t[1]["id"]
j=req("/journeys","POST",{"traveler_id":tid,"title":"Tianjin · stay-aware weekend","city_code":"CN-TIANJIN",
  "timezone":"Asia/Shanghai","start_at":"2026-10-09T18:00:00+08:00","end_at":"2026-10-11T15:00:00+08:00",
  "budget":{"amount_minor":120000,"currency":"CNY"},"stay_budget":{"amount_minor":70000,"currency":"CNY"},
  "party_size":2,"occupancy":{"adults":2,"rooms":1},
  "arrival_anchor":{"at":"2026-10-09T18:00:00+08:00","location":"Tianjin West Station"},
  "departure_anchor":{"at":"2026-10-11T15:00:00+08:00","location":"Tianjin Binhai Airport"}})
jid=j[1]["id"]; print("journey", j[0], jid)
s=req(f"/journeys/{jid}/stay-options/generate","POST",{})
print("generate:", s[0], json.dumps(s[1], ensure_ascii=False)[:400])
so=req(f"/journeys/{jid}/stay-options")
print("stay-options:", so[0], json.dumps(so[1], ensure_ascii=False)[:300])
ex=req(f"/journeys/{jid}/experience")
d=ex[1]
print("experience keys:", sorted(d.keys()))
print("options:", len(d.get("options",[])))
for o in d.get("options",[])[:2]:
    print("  opt", o.get("id"), o.get("label"), "| stay:", (o.get("stay") or {}).get("property_name"))
    for day in o.get("days",[]):
        print("   day", day.get("day"), day.get("label"), day.get("anchor"), day.get("mode"), "acts:", len(day.get("activities",[])))
        for a in day.get("activities",[])[:10]:
            print("      ", a.get("start_at"), "->", a.get("end_at"), "|", a.get("title"), "| locked:", a.get("locked"))
