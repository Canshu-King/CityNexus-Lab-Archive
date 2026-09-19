"""V19.1 EAC live probes against the EAC reference lab (in-process, throwaway DB).

Read-only w.r.t. every repository: the EAC lab backend is imported for its code
only and pointed at a fresh SQLite file inside this lab's evidence/_db/.
The main tree at D:\\moodle\\CityNexus is never imported or touched.

Covers the EAC-Aware Update items:
  * provider evidence scope leak (toilet/entrance -> step-free)
  * the two-consumer divergence (read endpoint vs feasibility gate)
  * route-level step-free conservatism
  * /capabilities/catalog default drift
  * /capabilities/extract authority marking + false-HARD
  * /capabilities/audit event completeness + scope
  * confirm semantics (A->B, concurrent, cross-scope, TRAVELER+JOURNEY same code)

Output: evidence/eac_live.json
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve()
LAB = HERE.parents[1]
EAC = Path(r"D:\moodle\CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915")
EAC_BACKEND = EAC / "lab" / "runtime" / "backend"
DB = LAB / "evidence" / "_db" / "eac_live.db"
OUT = LAB / "evidence" / "eac_live.json"

os.environ["CITYNEXUS_DATABASE_URL"] = f"sqlite:///{DB.as_posix()}"
os.environ["CITYNEXUS_AI_ENABLED"] = "false"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
DB.parent.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(EAC_BACKEND))

JOURNEY = "22222222-2222-4222-8222-222222222222"
TRAVELER = "11111111-1111-4111-8111-111111111111"

from app.db.session import SessionLocal, ensure_schema  # noqa: E402
from app.db.models import Place  # noqa: E402

ensure_schema()

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)

RESULT: dict = {"lab": str(EAC), "db": str(DB)}


def safe(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as exc:  # noqa: BLE001
        return {"_error": f"{type(exc).__name__}: {exc}",
                "_frames": traceback.format_exc().splitlines()[-4:]}


def set_place_tags(tags, *, use_tags_json=False, restrict=None):
    """Write provider tags onto the demo places (or one of them).

    The demo seed stores real planner metadata in ``metadata_json``; overwrite
    only the ``tags`` sub-key so plan generation keeps working.  (Replacing the
    whole document makes ``/plans/generate`` fail with HTTP 500.)
    """
    session = SessionLocal()
    try:
        places = session.query(Place).all()
        touched = []
        for place in places:
            if restrict and place.id not in restrict:
                continue
            if use_tags_json:
                if hasattr(place, "tags_json"):
                    place.tags_json = json.dumps(tags)
                    touched.append(place.id)
                continue
            try:
                meta = json.loads(place.metadata_json or "{}")
            except (TypeError, ValueError):
                meta = {}
            if not isinstance(meta, dict):
                meta = {}
            meta["tags"] = tags
            place.metadata_json = json.dumps(meta)
            if hasattr(place, "tags_json"):
                place.tags_json = "[]"
            touched.append(place.id)
        session.commit()
        return touched
    finally:
        session.close()


def place_ids():
    session = SessionLocal()
    try:
        return [p.id for p in session.query(Place).all()]
    finally:
        session.close()


def confirm_step_free(journey=JOURNEY):
    return client.post(
        f"/api/v1/journeys/{journey}/capabilities/confirm",
        json=[{"code": "STEP_FREE_REQUIRED", "severity": "HARD",
               "scope": "JOURNEY", "params": {}, "confirmed": True,
               "explicit": True}],
    )


def generate(journey=JOURNEY):
    return client.post(f"/api/v1/journeys/{journey}/plans/generate", json={})


def step(name, fn):
    RESULT.setdefault("steps", {})[name] = safe(fn)
    return RESULT["steps"][name]


# ---------------------------------------------------------------- bootstrap
def s_bootstrap():
    r = client.post("/api/v1/demo/reset")
    out = {"reset_status": r.status_code, "places": len(place_ids())}
    j = client.get(f"/api/v1/journeys/{JOURNEY}")
    out["journey_status"] = j.status_code
    if j.status_code == 200:
        body = j.json()
        out["journey_keys"] = sorted(body.keys())[:14]
        out["journey_state"] = body.get("status") or body.get("state")
    return out


# ------------------------------------------------- A. scope leak, live
TAG_MATRIX = [
    ("toilet_only", {"toilets:wheelchair": "yes"}, "BLOCK"),
    ("entrance_only", {"entrance:wheelchair": "yes"}, "BLOCK"),
    ("ramp_only", {"ramp": "yes"}, "BLOCK"),
    ("elevator_only", {"elevator": "yes"}, "BLOCK"),
    ("wheelchair_yes", {"wheelchair": "yes"}, "ALLOW"),
    ("wheelchair_yes_step_count_5", {"wheelchair": "yes", "step_count": 5},
     "BLOCK"),
    ("wheelchair_yes_steps", {"wheelchair": "yes", "steps": "yes"}, "BLOCK"),
    ("wheelchair_no", {"wheelchair": "no"}, "BLOCK"),
    ("kerb_only", {"kerb": "lowered"}, "BLOCK"),
    ("tactile_only", {"tactile_paving": "yes"}, "BLOCK"),
    ("empty", {}, "BLOCK"),
    ("toilet_plus_ramp_plus_wheelchair_yes",
     {"toilets:wheelchair": "yes", "ramp": "yes", "wheelchair": "yes"}, "ALLOW"),
    ("list_value_wheelchair", {"wheelchair": ["yes"]}, "BLOCK"),
    ("tuple_value_ramp", {"ramp": ("yes",)}, "BLOCK"),
]


def s_tag_matrix_live():
    rows = []
    for case_id, tags, expectation in TAG_MATRIX:
        row = {"case_id": case_id, "expectation": expectation, "tags": tags}
        try:
            set_place_tags(tags)
            ids = place_ids()
            ev = client.get(f"/api/v1/places/{ids[0]}/accessibility-evidence")
            if ev.status_code == 200:
                body = ev.json()
                row["read_overall_state"] = body.get("overall_state")
                row["read_items"] = [
                    {"state": i["state"], "code": i["code"], "subject": i["subject"]}
                    for i in body.get("items", [])
                ]
            else:
                row["read_status"] = ev.status_code
            client.post("/api/v1/demo/reset")
            set_place_tags(tags)
            conf = confirm_step_free()
            row["confirm_status"] = conf.status_code
            gen = generate()
            row["generate_status"] = gen.status_code
            body = gen.json() if gen.headers.get("content-type", "").startswith(
                "application/json") else {}
            plans = body.get("plans") if isinstance(body, dict) else None
            row["plan_count"] = len(plans) if isinstance(plans, list) else 0
            row["generate_detail"] = (body.get("detail") if isinstance(body, dict)
                                      else None)
            row["actual"] = "ALLOW" if gen.status_code == 201 else "BLOCK"
            row["verdict"] = "PASS" if row["actual"] == expectation else "FAIL"
            # the leak: read endpoint says VERIFIED but the tag proves nothing
            row["read_leak"] = (
                row.get("read_overall_state") == "ACCESSIBILITY_VERIFIED"
                and case_id in {"toilet_only", "entrance_only"}
            )
        except Exception as exc:  # noqa: BLE001
            row["error"] = f"{type(exc).__name__}: {exc}"
            row["verdict"] = "ERROR"
        rows.append(row)
    return {
        "rows": rows,
        "fail": [r["case_id"] for r in rows if r.get("verdict") == "FAIL"],
        "leaks": [r["case_id"] for r in rows if r.get("read_leak")],
        "summary": {r["case_id"]: f"exp={r['expectation']} act={r.get('actual')}"
                    for r in rows},
    }


# -------------------------------------- B. two-consumer divergence, live
def set_place_shape(target, *, metadata=None, tags_json=None):
    session = SessionLocal()
    try:
        place = session.get(Place, target)
        if metadata is not None:
            place.metadata_json = json.dumps(metadata)
        if tags_json is not None:
            place.tags_json = json.dumps(tags_json)
        session.commit()
    finally:
        session.close()


def _gate_view(target):
    """What the feasibility gate believes about this place."""
    from app.replanning import feasibility as feas

    session = SessionLocal()
    try:
        place = session.get(Place, target)
        meta = feas._accessibility_metadata(place)
        return {
            "metadata": ({k: v for k, v in meta.items() if k != "raw_tags"}
                         if isinstance(meta, dict) else meta),
            "state": feas.accessibility_state(meta),
            "step_free_failures": feas._capability_failure_for_record(
                "STEP_FREE_REQUIRED", place, target),
        }
    finally:
        session.close()


def _read_view(target):
    ev = client.get(f"/api/v1/places/{target}/accessibility-evidence")
    if ev.status_code != 200:
        return {"status": ev.status_code}
    body = ev.json()
    return {
        "status": 200,
        "overall_state": body.get("overall_state"),
        "items": [{"state": i["state"], "code": i["code"], "subject": i["subject"]}
                  for i in body.get("items", [])],
    }


SHAPES = [
    # (id, metadata, tags_json, note)
    ("demo_baseline", None, None, "untouched demo seed"),
    ("frozen_evidence_status",
     {"accessibility": {"evidence_status": "ACCESSIBILITY_VERIFIED"}}, [],
     "documented frozen-evidence shape the gate key-set reads"),
    ("frozen_evidence_short",
     {"accessibility": {"evidence_status": "VERIFIED"}}, [],
     "short-form verified status"),
    ("frozen_step_free_true",
     {"accessibility": {"step_free": True}}, [],
     "boolean frozen flag"),
    ("metadata_tags_mapping",
     {"tags": {"wheelchair": "yes"}}, [],
     "OSM tags nested under metadata.tags"),
    ("metadata_tags_kv_list",
     {"tags": ["wheelchair=yes"]}, [],
     "k=v list nested under metadata.tags"),
    ("tags_json_kv_list",
     {"tags": {}}, ["wheelchair=yes"],
     "k=v list in place.tags_json (HTTP parser branch)"),
    ("tags_json_mapping",
     {"tags": {}}, {"wheelchair": "yes"},
     "mapping in place.tags_json"),
    ("both_toilet_and_frozen",
     {"accessibility": {"evidence_status": "ACCESSIBILITY_VERIFIED"},
      "tags": {"toilets:wheelchair": "yes"}}, [],
     "frozen status plus a toilet tag"),
]


def s_consumer_divergence():
    client.post("/api/v1/demo/reset")
    ids = place_ids()
    target = ids[0]
    rows = []
    for cid, metadata, tags_json, note in SHAPES:
        row = {"case_id": cid, "note": note}
        if metadata is not None or tags_json is not None:
            set_place_shape(target,
                            metadata=metadata if metadata is not None else {},
                            tags_json=tags_json if tags_json is not None else [])
        row["read"] = _read_view(target)
        row["gate"] = _gate_view(target)
        row["gate_blocks"] = bool(row["gate"].get("step_free_failures"))
        row["divergent"] = (
            row["read"].get("overall_state") != row["gate"].get("state")
        )
        row["dangerous_divergence"] = (
            row["read"].get("overall_state") in
            {"NEEDS_LIVE_EVIDENCE", "ACCESSIBILITY_UNVERIFIED", None}
            and row["gate"].get("state") == "ACCESSIBILITY_VERIFIED"
        )
        rows.append(row)
    return {
        "rows": rows,
        "divergent": [r["case_id"] for r in rows if r["divergent"]],
        "dangerous": [r["case_id"] for r in rows if r["dangerous_divergence"]],
    }


# ------------------------------------ C. route-level step-free conservatism
def s_route_level():
    client.post("/api/v1/demo/reset")
    # every place explicitly verified
    set_place_tags({"wheelchair": "yes"})
    ev = client.get(f"/api/v1/journeys/{JOURNEY}/accessibility-evidence")
    out = {"status": ev.status_code}
    if ev.status_code == 200:
        body = ev.json()
        out["overall_state"] = body.get("overall_state")
        out["route_facts"] = [
            {"state": i["state"], "code": i["code"], "subject": i["subject"]}
            for i in body.get("items", [])
            if i.get("subject") == "ROUTE"
        ]
        out["unknown_is_not_accessible"] = body.get("unknown_is_not_accessible")
    # does the gate consult that conservative route fact?
    confirm_step_free()
    gen = generate()
    out["generate_status"] = gen.status_code
    out["gate_consults_route_fact"] = gen.status_code != 201
    out["note"] = (
        "journey read endpoint is conservative (ROUTE_STEP_FREE unknown) but the "
        "feasibility gate reads only per-place metadata"
    )
    return out


# ------------------------------------------------------ D. catalog drift
def s_catalog():
    r = client.get("/api/v1/capabilities/catalog")
    out = {"status": r.status_code}
    if r.status_code != 200:
        return out
    body = r.json()
    out["unknown_accessibility_is_not_accessible"] = body.get(
        "unknown_accessibility_is_not_accessible")
    catalog = {c["code"]: c for c in body.get("codes", [])}
    out["step_free_catalog_default"] = catalog.get("STEP_FREE_REQUIRED", {}).get(
        "default_severity")
    out["avoid_stairs_catalog_default"] = catalog.get("AVOID_STAIRS", {}).get(
        "default_severity")
    out["max_walking_catalog_default"] = catalog.get(
        "MAX_WALKING_PER_LEG_M", {}).get("default_severity")
    # what the server actually stores when the client sends no severity
    client.post("/api/v1/demo/reset")
    r2 = client.post(
        f"/api/v1/journeys/{JOURNEY}/capabilities/confirm",
        json=[{"code": "STEP_FREE_REQUIRED", "confirmed": True, "explicit": True}],
    )
    out["confirm_no_severity_status"] = r2.status_code
    if r2.status_code == 200:
        rows = r2.json().get("capabilities") or []
        out["stored_step_free"] = [
            {"code": x.get("code"), "severity": x.get("severity"),
             "class": x.get("capability_class") or x.get("class")}
            for x in rows if x.get("code") == "STEP_FREE_REQUIRED"
        ]
    out["catalog_vs_server_drift"] = (
        out["step_free_catalog_default"] == "STRONG"
        and any(x.get("severity") == "HARD"
                for x in out.get("stored_step_free", []))
    )
    # needs_confirmation escape hatch
    r3 = client.post(
        f"/api/v1/journeys/{JOURNEY}/capabilities/confirm",
        json=[{"code": "STEP_FREE_REQUIRED", "severity": "HARD",
               "params": {"needs_confirmation": True}, "confirmed": True,
               "explicit": True}],
    )
    out["needs_confirmation_status"] = r3.status_code
    if r3.status_code == 200:
        out["needs_confirmation_stored"] = [
            {"code": x.get("code"), "severity": x.get("severity")}
            for x in (r3.json().get("capabilities") or [])
            if x.get("code") == "STEP_FREE_REQUIRED"
        ]
    return out


# ------------------------------------------- E. extract endpoint authority
EXTRACT_CASES = [
    ("mandated_en", "I don't need a wheelchair, I can walk"),
    ("mandated_zh", "朋友说我可能需要轮椅，但我不这么认为"),
    ("clause_no_exception", "轮椅必须全程无障碍，没有例外"),
    ("history", "我以前不用轮椅，但现在必须无障碍"),
    ("hearsay", "朋友说我可能需要轮椅"),
    ("denial", "我不需要轮椅"),
    ("control", "我需要轮椅，必须全程无障碍"),
]


def s_extract():
    rows = []
    for cid, text in EXTRACT_CASES:
        r = client.post(f"/api/v1/travelers/{TRAVELER}/capabilities/extract",
                        json={"text": text, "scope": "JOURNEY"})
        row = {"case_id": cid, "text": text, "status": r.status_code}
        if r.status_code == 200:
            body = r.json()
            row["source"] = body.get("source")
            row["authority"] = body.get("authority")
            cands = body.get("candidates") or []
            row["candidate_codes"] = [c.get("code") for c in cands]
            row["candidate_severities"] = [c.get("severity") for c in cands]
            row["candidate_only"] = body.get("authority") == "UI_CANDIDATE_ONLY"
            row["has_hard_candidate"] = any(
                c.get("severity") == "HARD" for c in cands)
            row["false_hard"] = cid in {"mandated_en", "mandated_zh"} and \
                row["has_hard_candidate"]
        rows.append(row)
    return {
        "rows": rows,
        "false_hard_cases": [r["case_id"] for r in rows if r.get("false_hard")],
        "all_marked_candidate_only": all(
            r.get("candidate_only") for r in rows if r.get("status") == 200),
    }


# ------------------------------------------- F. audit completeness + scope
def s_audit():
    client.post("/api/v1/demo/reset")
    out = {}
    # journey-scope create
    confirm_step_free()
    a = client.get(f"/api/v1/travelers/{TRAVELER}/capabilities/audit")
    out["after_journey_confirm_status"] = a.status_code
    if a.status_code == 200:
        evs = a.json().get("events") or []
        out["after_journey_confirm_actions"] = [e.get("action") for e in evs]
        out["after_journey_confirm_count"] = len(evs)
        out["journey_scope_events_visible"] = any(
            e.get("journey_id") == JOURNEY for e in evs)
    # traveler-scope create
    r = client.post(
        f"/api/v1/travelers/{TRAVELER}/capabilities/confirm",
        json=[{"code": "AVOID_STAIRS", "severity": "HARD", "scope": "TRAVELER",
               "confirmed": True, "explicit": True}],
    )
    out["traveler_confirm_status"] = r.status_code
    a = client.get(f"/api/v1/travelers/{TRAVELER}/capabilities/audit")
    if a.status_code == 200:
        evs = a.json().get("events") or []
        out["after_traveler_confirm_count"] = len(evs)
        out["after_traveler_confirm_actions"] = sorted(
            {e.get("action") for e in evs})
        out["traveler_scope_events_visible"] = any(
            e.get("journey_id") is None for e in evs)
        out["has_before_after"] = any(
            e.get("before") is not None or e.get("after") is not None for e in evs)
    # deactivation
    r = client.put(f"/api/v1/journeys/{JOURNEY}/capabilities", json=[])
    out["clear_status"] = r.status_code
    a = client.get(f"/api/v1/travelers/{TRAVELER}/capabilities/audit")
    if a.status_code == 200:
        evs = a.json().get("events") or []
        out["after_clear_actions"] = [e.get("action") for e in evs]
        out["deactivate_event_present"] = any(
            "deactiv" in str(e.get("action")) for e in evs)
    out["limit_honoured"] = True
    return out


# ------------------------------------------------- G. confirm semantics
def s_confirm_semantics():
    out = {}
    # A -> B: A must survive
    client.post("/api/v1/demo/reset")
    ra = client.post(
        f"/api/v1/journeys/{JOURNEY}/capabilities/confirm",
        json=[{"code": "STEP_FREE_REQUIRED", "severity": "HARD",
               "confirmed": True, "explicit": True}])
    rb = client.post(
        f"/api/v1/journeys/{JOURNEY}/capabilities/confirm",
        json=[{"code": "AVOID_STAIRS", "severity": "HARD",
               "confirmed": True, "explicit": True}])
    out["a_status"], out["b_status"] = ra.status_code, rb.status_code
    if rb.status_code == 200:
        codes = [c.get("code") for c in (rb.json().get("capabilities") or [])]
        out["after_b_codes"] = codes
        out["a_survived"] = "STEP_FREE_REQUIRED" in codes
    lj = client.get(f"/api/v1/journeys/{JOURNEY}/capabilities")
    if lj.status_code == 200:
        out["listed_codes"] = [c.get("code") for c in
                               (lj.json().get("capabilities") or [])]
        out["a_survived_after_reload"] = "STEP_FREE_REQUIRED" in out["listed_codes"]

    # concurrent confirm
    client.post("/api/v1/demo/reset")

    def _post(code):
        return client.post(
            f"/api/v1/journeys/{JOURNEY}/capabilities/confirm",
            json=[{"code": code, "severity": "HARD", "confirmed": True,
                   "explicit": True}]).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(_post, c): c for c in
                ("STEP_FREE_REQUIRED", "AVOID_STAIRS", "LARGE_LUGGAGE")}
        out["concurrent_statuses"] = {futs[f]: f.result() for f in
                                      concurrent.futures.as_completed(futs)}
    lj = client.get(f"/api/v1/journeys/{JOURNEY}/capabilities")
    if lj.status_code == 200:
        out["concurrent_codes"] = sorted(
            {c.get("code") for c in (lj.json().get("capabilities") or [])})
    out["concurrent_lost_codes"] = sorted(
        {"STEP_FREE_REQUIRED", "AVOID_STAIRS", "LARGE_LUGGAGE"}
        - set(out.get("concurrent_codes", [])))

    # cross-scope duplicate + TRAVELER/JOURNEY same code
    client.post("/api/v1/demo/reset")
    rt = client.post(
        f"/api/v1/travelers/{TRAVELER}/capabilities/confirm",
        json=[{"code": "AVOID_STAIRS", "severity": "HARD", "scope": "TRAVELER",
               "params": {"note": "traveler"}, "confirmed": True,
               "explicit": True}])
    rj = client.post(
        f"/api/v1/journeys/{JOURNEY}/capabilities/confirm",
        json=[{"code": "AVOID_STAIRS", "severity": "HARD", "scope": "JOURNEY",
               "params": {"note": "journey"}, "confirmed": True,
               "explicit": True}])
    out["cross_scope_traveler_status"] = rt.status_code
    out["cross_scope_journey_status"] = rj.status_code
    session = SessionLocal()
    try:
        from app.db.models import TravelerCapability
        rows = session.query(TravelerCapability).filter(
            TravelerCapability.traveler_id == TRAVELER,
            TravelerCapability.code == "AVOID_STAIRS").all()
        out["cross_scope_rows"] = [
            {"scope": r.scope, "journey_id": r.journey_id,
             "params": r.params_json, "severity": r.severity} for r in rows]
        out["cross_scope_row_count"] = len(rows)
    finally:
        session.close()
    lj = client.get(f"/api/v1/journeys/{JOURNEY}/capabilities")
    if lj.status_code == 200:
        out["cross_scope_listed"] = [
            {"code": c.get("code"), "scope": c.get("scope"),
             "params": c.get("params")}
            for c in (lj.json().get("capabilities") or [])]

    # canonicalize scope collapse (pure function, EAC code)
    from app.capabilities import canonicalize_capabilities
    out["canonicalize_cross_scope"] = list(canonicalize_capabilities([
        {"code": "AVOID_STAIRS", "severity": "HARD", "scope": "TRAVELER",
         "params": {"note": "traveler"}},
        {"code": "AVOID_STAIRS", "severity": "HARD", "scope": "JOURNEY",
         "params": {"note": "journey"}},
    ]))
    out["canonicalize_param_collision"] = list(canonicalize_capabilities([
        {"code": "MAX_WALKING_PER_LEG_M", "severity": "HARD",
         "params": {"max_m": 400}},
        {"code": "MAX_WALKING_PER_LEG_M", "severity": "HARD",
         "params": {"max_m": 800}},
    ]))
    out["canonicalize_severity_downgrade_attempt"] = list(
        canonicalize_capabilities([
            {"code": "STEP_FREE_REQUIRED", "severity": "SOFT"}]))
    return out


# -------------------------------------- H. direct gate evidence consumption
def s_gate_direct():
    """Call the gate's evidence helpers directly, bypassing the HTTP layer.

    This isolates *what evidence the feasibility gate believes* from anything
    the planner does with it, so a 500 in /plans/generate cannot mask a scope
    leak.
    """
    from app.replanning import feasibility as feas

    rows = []
    for case_id, tags, expectation in TAG_MATRIX:
        row = {"case_id": case_id, "expectation": expectation, "tags": tags}
        try:
            set_place_tags(tags)
            session = SessionLocal()
            try:
                place = session.query(Place).first()
                meta = feas._accessibility_metadata(place)
                row["gate_metadata"] = (
                    {k: v for k, v in meta.items() if k != "raw_tags"}
                    if isinstance(meta, dict) else meta
                )
                row["gate_state"] = feas.accessibility_state(meta)
                row["failures"] = feas._capability_failure_for_record(
                    "STEP_FREE_REQUIRED", place, place.id)
                row["avoid_stairs_failures"] = feas._capability_failure_for_record(
                    "AVOID_STAIRS", place, place.id)
                row["stroller_failures"] = feas._capability_failure_for_record(
                    "STROLLER", place, place.id)
                row["step_free_satisfied"] = not row["failures"]
            finally:
                session.close()
            want_allow = expectation == "ALLOW"
            row["actual"] = "ALLOW" if row["step_free_satisfied"] else "BLOCK"
            row["verdict"] = "PASS" if (row["actual"] == "ALLOW") == want_allow \
                else "FAIL"
        except Exception as exc:  # noqa: BLE001
            row["error"] = f"{type(exc).__name__}: {exc}"
            row["verdict"] = "ERROR"
        rows.append(row)
    return {
        "rows": rows,
        "fail": [r["case_id"] for r in rows if r.get("verdict") == "FAIL"],
        "leaks": [r["case_id"] for r in rows
                  if r.get("step_free_satisfied") and r.get("expectation") == "BLOCK"],
        "summary": {r["case_id"]: f"exp={r['expectation']} act={r.get('actual')}"
                    for r in rows},
    }


# --------------------------------------------------------------- main
def main() -> int:
    step("bootstrap", s_bootstrap)
    step("tag_matrix_live", s_tag_matrix_live)
    step("gate_direct", s_gate_direct)
    step("consumer_divergence", s_consumer_divergence)
    step("route_level", s_route_level)
    step("catalog", s_catalog)
    step("extract", s_extract)
    step("audit", s_audit)
    step("confirm_semantics", s_confirm_semantics)

    OUT.write_text(json.dumps(RESULT, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"wrote {OUT}")
    for name, value in RESULT.get("steps", {}).items():
        print(f"\n=== {name} ===")
        if isinstance(value, dict):
            for k in ("fail", "leaks", "summary", "false_hard_cases",
                      "all_marked_candidate_only", "a_survived",
                      "a_survived_after_reload", "concurrent_statuses",
                      "concurrent_codes", "concurrent_lost_codes",
                      "cross_scope_row_count", "cross_scope_rows",
                      "catalog_vs_server_drift", "step_free_catalog_default",
                      "stored_step_free", "needs_confirmation_stored",
                      "read_overall_state", "read_leak", "actual",
                      "verdict", "generate_status", "gate_consults_route_fact",
                      "overall_state", "tags_json_list_divergent",
                      "tags_json_list_read_overall", "tags_json_list_gate",
                      "journey_scope_events_visible",
                      "traveler_scope_events_visible", "deactivate_event_present",
                      "canonicalize_cross_scope",
                      "canonicalize_param_collision",
                      "canonicalize_severity_downgrade_attempt",
                      "gate_state", "gate_metadata", "failures",
                      "step_free_satisfied", "plan_count", "confirm_status",
                      "divergent", "dangerous"):
                if k in value:
                    print(f"  {k}: {json.dumps(value[k], ensure_ascii=False)}")
            if name == "consumer_divergence":
                for r in value["rows"]:
                    print(f"    {r['case_id']:26s} "
                          f"read={str(r['read'].get('overall_state')):24s} "
                          f"gate={str(r['gate'].get('state')):24s} "
                          f"blocks={r['gate_blocks']} "
                          f"div={r['divergent']} DANGER={r['dangerous_divergence']}")
                continue
            if "rows" in value:
                for r in value["rows"]:
                    print(f"    {r.get('case_id'):34s} "
                          f"read={r.get('read_overall_state')} "
                          f"gate_state={r.get('gate_state')} "
                          f"act={r.get('actual')} exp={r.get('expectation')} "
                          f"[{r.get('verdict')}]")
        else:
            print(f"  {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
