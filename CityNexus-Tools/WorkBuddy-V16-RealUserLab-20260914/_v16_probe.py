import json, urllib.request, uuid
BASE="http://127.0.0.1:8010/api/v1"
def req(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE+path, data=data, method=method,
        headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]

t = req("/travelers","POST",{"display_name":"probe","locale":"zh-CN","timezone":"Asia/Shanghai"})
print("traveler", t[0]); tid=t[1]["id"]
j = req("/journeys","POST",{"traveler_id":tid,"title":"福州 · journey","city_code":"CN-FUZHOU",
  "timezone":"Asia/Shanghai","start_at":"2026-09-20T00:00:00+08:00","end_at":"2026-09-22T00:00:00+08:00",
  "budget":{"amount_minor":300000,"currency":"CNY"},"stay_budget":{"amount_minor":120000,"currency":"CNY"},
  "party_size":2,"occupancy":{"adults":2,"rooms":1},
  "arrival_anchor":{"at":"2026-09-20T00:00:00+08:00","location":"福州站"},
  "departure_anchor":{"at":"2026-09-22T00:00:00+08:00","location":"福州站"}})
print("journey", j[0]); jid=j[1]["id"]
print("journey keys:", sorted(j[1].keys()))
print("city_code:", j[1].get("city_code"), "| budget:", j[1].get("budget"))
print("plans:", json.dumps(req(f"/journeys/{jid}/plans"), ensure_ascii=False)[:500])
print("gen:", json.dumps(req(f"/journeys/{jid}/plans/generate","POST",{}), ensure_ascii=False)[:900])
print("open:", json.dumps(req(f"/journeys/{jid}"), ensure_ascii=False)[:1500])
