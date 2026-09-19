import json, urllib.request
BASE="http://127.0.0.1:8010/api/v1"
def req(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE+path, data=data, method=method, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

def trial(name, **kw):
    t=req("/travelers","POST",{"display_name":"u","locale":"zh-CN","timezone":kw.get("tz","Asia/Shanghai")})
    tid=t[1]["id"]
    body={"traveler_id":tid,"title":name,"city_code":kw.get("city","CN-TIANJIN"),
      "timezone":kw.get("tz","Asia/Shanghai"),"start_at":kw["start"],"end_at":kw["end"],
      "budget":{"amount_minor":kw.get("budget",120000),"currency":kw.get("cur","CNY")},
      "stay_budget":{"amount_minor":kw.get("stay",70000),"currency":kw.get("cur","CNY")},
      "party_size":kw.get("party",2),"occupancy":{"adults":kw.get("party",2),"rooms":1},
      "arrival_anchor":{"at":kw["start"],"location":kw.get("arr","X Station")},
      "departure_anchor":{"at":kw["end"],"location":kw.get("dep","X Airport")}}
    j=req("/journeys","POST",body)
    if j[0]!=201: return name, "JOURNEY_"+str(j[0]), 0
    jid=j[1]["id"]
    s=req(f"/journeys/{jid}/stay-options/generate","POST",{})
    if s[0]!=200: return name, "GEN_"+str(s[0]), 0
    ex=req(f"/journeys/{jid}/experience")
    n=len(ex[1].get("options",[])) if ex[0]==200 else -1
    return name, "OK", n

cases = [
 ("demo-baseline",      dict(start="2026-10-09T18:00:00+08:00", end="2026-10-11T15:00:00+08:00")),
 ("midnight-start",     dict(start="2026-10-09T00:00:00+08:00", end="2026-10-11T15:00:00+08:00")),
 ("sep-dates",          dict(start="2026-09-20T18:00:00+08:00", end="2026-09-22T15:00:00+08:00")),
 ("same-day-window",    dict(start="2026-10-09T18:00:00+08:00", end="2026-10-10T15:00:00+08:00")),
 ("4-day",              dict(start="2026-10-09T18:00:00+08:00", end="2026-10-13T15:00:00+08:00")),
 ("low-budget",         dict(start="2026-10-09T18:00:00+08:00", end="2026-10-11T15:00:00+08:00", budget=30000, stay=15000)),
 ("high-budget",        dict(start="2026-10-09T18:00:00+08:00", end="2026-10-11T15:00:00+08:00", budget=500000, stay=300000)),
 ("fuzhou",             dict(start="2026-10-09T18:00:00+08:00", end="2026-10-11T15:00:00+08:00", city="CN-FUZHOU", arr="福州站", dep="福州长乐机场")),
 ("beijing",            dict(start="2026-10-09T18:00:00+08:00", end="2026-10-11T15:00:00+08:00", city="CN-BEIJING", arr="北京南站", dep="首都机场")),
 ("wuyuan-county",      dict(start="2026-10-09T18:00:00+08:00", end="2026-10-11T15:00:00+08:00", city="CN-婺源", arr="婺源站", dep="婺源站")),
 ("london",             dict(start="2026-10-09T18:00:00+00:00", end="2026-10-11T15:00:00+00:00", city="GB-LONDON", tz="Europe/London", cur="GBP", budget=120000, stay=70000, arr="Paddington", dep="Heathrow")),
 ("tokyo",              dict(start="2026-10-09T18:00:00+09:00", end="2026-10-11T15:00:00+09:00", city="JP-TOKYO", tz="Asia/Tokyo", cur="JPY", budget=60000, stay=30000, arr="东京站", dep="羽田机场")),
 ("party-4",            dict(start="2026-10-09T18:00:00+08:00", end="2026-10-11T15:00:00+08:00", party=4)),
 ("party-1",            dict(start="2026-10-09T18:00:00+08:00", end="2026-10-11T15:00:00+08:00", party=1)),
]
for name, kw in cases:
    try:
        print("%-18s %-10s options=%s" % trial(name, **kw))
    except Exception as e:
        print("%-18s EXC %s" % (name, e))
