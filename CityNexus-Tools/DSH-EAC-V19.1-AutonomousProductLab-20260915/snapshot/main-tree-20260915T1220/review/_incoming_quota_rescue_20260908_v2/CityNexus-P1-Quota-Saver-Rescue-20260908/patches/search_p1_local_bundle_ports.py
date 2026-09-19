#!/usr/bin/env python3
"""Topology-safe local port search for the current P1 hard-route bundle.

This is a diagnostic/staging helper, not a promotion tool.  It searches a
small set of target-port variants for the repeatedly failing UC-06 / UC-07
cluster, generates diversified rectilinear candidate families, repairs
pairwise gaps, enforces AC-3, and finally asks the exact non-OR-Tools CSP
selector for one contact-free candidate per local route.

The three C4E1 Extend routes remain hard immutable obstacles.  A previously
validated Traveler skeleton may be supplied; matching routes are injected as
*optional candidates*, never frozen.  This retains proven good geometry while
still allowing the solver to rip it up when provider access requires that.

No authoritative YAML is modified.  A PASS is only a local witness and must be
re-integrated into a full 18-Association genus-0 search before V1/V2/V3.
"""
from __future__ import annotations

import argparse
import copy
import heapq
import itertools
import json
import math
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]

from explore_p1_disjoint_pool import (  # noqa: E402
    _candidate_pool,
    _merge_candidate,
    _repair_arc_empty_routes,
    _repair_pairwise_gaps,
)
from route_candidate_selector import (  # noqa: E402
    arc_consistency_prune,
    build_conflicts,
    find_first_solution,
    make_candidate,
    route_pair_compatibility,
)
from route_p1_negotiated_grid import build_axes, build_graph, load  # noqa: E402
from routing_geometry import route_points  # noqa: E402
from search_p1_global_port_rotations import genus, target_options  # noqa: E402

DEFAULT_PLAN = "PLAN_TRAVELER_SKELETON_PLANAR_GRID"
DEFAULT_BUNDLE = (
    "A-T-UC-06",
    "A-T-UC-07",
    "A-T-UC-11",
    "A-B-06",
    "A-PA-07",
)
VARY_ROUTE_TARGET = {
    "A-T-UC-06": "UC-06",
    "A-T-UC-07": "UC-07",
    "A-T-UC-11": "UC-11",
    "A-B-06": "UC-06",
    "A-PA-07": "UC-07",
}
TRAVELER_SOURCE_IDS = ("A-T-UC-06", "A-T-UC-07", "A-T-UC-11")
PROVIDER_SOURCE_IDS = ("A-B-06", "A-PA-07")


def _nearest_options(node, *, include_left=False, dense=False, per_side=7, current=None):
    """Return deterministic target ports without materialising all 120 lanes.

    ``dense=False`` keeps the historical 20/50/80 percent probes.  Dense mode
    samples actual 0.10-cm perimeter lanes, prioritising the current lane,
    centre, quartiles and extremes.  The full topology gate is still applied
    after combining route choices.
    """
    options = target_options(node)
    sides = ("RIGHT", "TOP", "BOTTOM", "LEFT") if include_left else ("RIGHT", "TOP", "BOTTOM")
    out = []
    for side in sides:
        side_values = [item for item in options if item[0] == side]
        if not side_values:
            continue
        if not dense:
            wanted = (0.20, 0.50, 0.80)
            picked = [min(side_values, key=lambda value: abs(float(value[1]) - target)) for target in wanted]
        else:
            targets = [0.05, 0.15, 0.25, 0.35, 0.50, 0.65, 0.75, 0.85, 0.95]
            if current is not None and current[0] == side:
                targets.insert(0, float(current[1]))
            picked = []
            for target in targets:
                item = min(side_values, key=lambda value: abs(float(value[1]) - target))
                if item not in picked:
                    picked.append(item)
            picked = picked[:max(1, int(per_side))]
        for item in picked:
            if item not in out:
                out.append(item)
    return out


def _source_fraction_options(node, side, current, *, dense=False, radius=3):
    """Return exact 0.10-cm source lanes around a current fraction.

    Provider actors are degree-1 in P1, so their source fractions are cheap
    geometry freedom.  Traveler fractions are also searched, with genus=0 as
    the final authority on any rotation change.
    """
    current = float(current)
    if side in ("LEFT", "RIGHT"):
        span = float(node["height"])
    else:
        span = float(node["width"])
    step = 0.10 / span
    if dense:
        # Keep the search finite but much broader than the old +/-0.20 fraction
        # heuristic.  These are physical 0.10-cm lanes, not arbitrary percent.
        deltas = range(-max(radius, 6), max(radius, 6) + 1)
    else:
        deltas = range(-radius, radius + 1)
    values = [current]
    for delta in deltas:
        value = current + delta * step
        if 0.02 <= value <= 0.98:
            values.append(value)
    return sorted(set(round(v, 12) for v in values), key=lambda v: (abs(v-current), v))


def _port_signature(route):
    return (
        route["sourceSide"], round(float(route["sourcePortFraction"]), 12),
        route["targetSide"], round(float(route["targetPortFraction"]), 12),
    )


def _skeleton_candidate(route, nodes, skeleton_by_id):
    supplied = skeleton_by_id.get(route["id"])
    if not supplied or not supplied.get("waypoints"):
        return None
    if _port_signature(route) != _port_signature(supplied):
        return None
    points = route_points(supplied, nodes)
    try:
        return make_candidate({
            "routeId": route["id"],
            "family": "validated-traveler-skeleton",
            "points": points,
            "cost": sum(abs(b[0]-a[0]) + abs(b[1]-a[1]) for a,b in zip(points, points[1:])),
            "tag": f"{route['id']}:validated-skeleton",
        })
    except ValueError:
        return None


def _variant_score(base_routes, variant_routes):
    score = 0.0
    for rid in VARY_ROUTE_TARGET:
        before = base_routes[rid]
        after = variant_routes[rid]
        if (before["targetSide"], float(before["targetPortFraction"])) != (
            after["targetSide"], float(after["targetPortFraction"])
        ):
            score += 1.0
        # Keep natural provider entry as a mild preference, never a gate.
        if rid == "A-B-06" and after["targetSide"] not in {"RIGHT", "BOTTOM"}:
            score += 0.20
        if rid == "A-PA-07" and after["targetSide"] not in {"RIGHT", "TOP"}:
            score += 0.20
        score += abs(float(after["targetPortFraction"]) - 0.5) * 0.03
    # UC-06 has two mutable Associations plus frozen EXT-07-06.  Distinct
    # target perimeter positions are mandatory and distinct sides are useful.
    a = variant_routes["A-T-UC-06"]
    b = variant_routes["A-B-06"]
    if a["targetSide"] == b["targetSide"]:
        score += 0.25
    return score


def _choice_penalty(base_routes, rid, kind, value):
    route = base_routes[rid]
    if kind == "target":
        side, fraction = value
        changed = 0.0 if (side == route["targetSide"] and abs(float(fraction)-float(route["targetPortFraction"])) < 1e-12) else 1.0
        return changed + abs(float(fraction)-float(route["targetPortFraction"])) * 0.05
    return abs(float(value)-float(route["sourcePortFraction"])) * 0.05


def _variant_dimensions(base_routes, nodes, *, vary_source, include_left, dense_targets, per_side):
    dims = []
    for rid, nid in VARY_ROUTE_TARGET.items():
        current = (base_routes[rid]["targetSide"], float(base_routes[rid]["targetPortFraction"]))
        values = _nearest_options(
            nodes[nid], include_left=include_left, dense=dense_targets,
            per_side=per_side, current=current,
        )
        if current not in values:
            values.insert(0, current)
        values = sorted(values, key=lambda v: (_choice_penalty(base_routes, rid, "target", v), v[0], float(v[1])))
        dims.append((rid, "target", values))
    if vary_source:
        for rid in (*TRAVELER_SOURCE_IDS, *PROVIDER_SOURCE_IDS):
            route = base_routes[rid]
            values = _source_fraction_options(
                nodes[route["source"]], route["sourceSide"], route["sourcePortFraction"],
                dense=dense_targets,
            )
            values = sorted(values, key=lambda v: (_choice_penalty(base_routes, rid, "source", v), float(v)))
            dims.append((rid, "source", values))
    return dims


def _apply_dimension_choices(base_routes, dims, indices):
    routes = copy.deepcopy(base_routes)
    for (rid, kind, values), index in zip(dims, indices):
        value = values[index]
        if kind == "target":
            routes[rid]["targetSide"], routes[rid]["targetPortFraction"] = value
        else:
            routes[rid]["sourcePortFraction"] = value
    return routes


def _valid_unique_ports(routes):
    # No two connectors may share exactly the same target perimeter point on
    # the same UML node.  The topology auditor also rejects duplicate darts,
    # but this cheaper check avoids needless genus work.
    seen = set()
    for rid in DEFAULT_BUNDLE:
        route = routes[rid]
        key = (
            route["target"], route["targetSide"],
            round(float(route["targetPortFraction"]), 12),
        )
        if key in seen:
            return False
        seen.add(key)
    # Likewise for the three Traveler source ports.
    traveler = [routes[rid] for rid in TRAVELER_SOURCE_IDS]
    source_keys = {(r["sourceSide"], round(float(r["sourcePortFraction"]), 12)) for r in traveler}
    return len(source_keys) == len(traveler)


def _strategic_variants(
    base_routes, nodes, max_variants, vary_source=False, include_left=False,
    dense_targets=False, per_side=7, deadline=None, stats=None,
):
    """Best-first lazy enumeration of topology-safe local port variants.

    The previous implementation built and genus-checked the full Cartesian
    product *before* starting the user-visible time budget.  With source
    variation that reached 125k-275k deep copies for a request that might only
    consume 30 variants.  This heap enumerator checks the cheapest combinations
    first and stops as soon as enough genus-0 variants are collected or the
    deadline expires.
    """
    dims = _variant_dimensions(
        base_routes, nodes, vary_source=vary_source, include_left=include_left,
        dense_targets=dense_targets, per_side=per_side,
    )
    if not dims:
        return []
    start_indices = tuple(0 for _ in dims)

    def cheap_score(indices):
        return sum(
            _choice_penalty(base_routes, rid, kind, values[index])
            for (rid, kind, values), index in zip(dims, indices)
        )

    queue = [(cheap_score(start_indices), start_indices)]
    seen = {start_indices}
    rows = []
    checked = 0
    rejected_unique = 0
    rejected_topology = 0
    while queue and len(rows) < max_variants:
        if deadline is not None and time.monotonic() >= deadline:
            break
        _, indices = heapq.heappop(queue)
        checked += 1
        routes = _apply_dimension_choices(base_routes, dims, indices)
        if not _valid_unique_ports(routes):
            rejected_unique += 1
        else:
            g = genus(routes, nodes)
            if g is not None and abs(float(g)) <= 1e-9:
                rows.append((_variant_score(base_routes, routes), routes))
            else:
                rejected_topology += 1
        # Cartesian best-first neighbours.  This explores only the frontier
        # needed to obtain top-K legal variants instead of materialising all.
        for dim_index, (_, _, values) in enumerate(dims):
            next_index = indices[dim_index] + 1
            if next_index >= len(values):
                continue
            candidate = list(indices); candidate[dim_index] = next_index
            candidate = tuple(candidate)
            if candidate in seen:
                continue
            seen.add(candidate)
            heapq.heappush(queue, (cheap_score(candidate), candidate))
    rows.sort(key=lambda item: item[0])
    if stats is not None:
        stats.update({
            "dimensions": len(dims),
            "rawCombinationsChecked": checked,
            "frontierSize": len(queue),
            "uniquePortRejects": rejected_unique,
            "topologyRejects": rejected_topology,
            "acceptedVariants": len(rows),
            "denseTargets": bool(dense_targets),
            "varySource": bool(vary_source),
        })
    return rows[:max_variants]


def _domain_summary(ac3):
    return {rid: len(values) for rid, values in ac3.get("domains", {}).items()}


def search(*, plan, skeleton, variants, samples, pair_rounds, pair_samples,
           pair_fixed, arc_rounds, arc_samples, arc_bundles, seed, seconds,
           checkpoint=None, vary_source=False, include_left=False,
           dense_targets=False, target_lanes_per_side=7):
    start = time.monotonic()
    deadline = start + max(0.001, float(seconds))
    sem, original, nodes, base_routes, overrides, frozen, mutable = load(plan)
    skeleton_by_id = {}
    if skeleton:
        document = yaml.safe_load(Path(skeleton).read_text(encoding="utf-8")) or {}
        skeleton_by_id = {item.get("id"): item for item in document.get("routes", [])}

    variant_stats = {}
    variant_rows = _strategic_variants(
        base_routes, nodes, variants,
        vary_source=vary_source, include_left=include_left,
        dense_targets=dense_targets, per_side=target_lanes_per_side,
        deadline=deadline, stats=variant_stats,
    )
    attempts = []
    best = None

    def write_checkpoint():
        if checkpoint is None:
            return
        payload = {
            "status": "RUNNING",
            "scope": "LOCAL_5_ROUTE_DIAGNOSTIC",
            "plan": plan,
            "bundle": list(DEFAULT_BUNDLE),
            "testedVariants": len(attempts),
            "elapsedSeconds": time.monotonic() - start,
            "variantGeneration": variant_stats,
            "bestAttempt": best[1] if best else None,
            "attempts": attempts,
        }
        Path(checkpoint).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    for index, (port_score, routes) in enumerate(variant_rows, 1):
        if time.monotonic() >= deadline:
            break
        local_routes = [routes[rid] for rid in DEFAULT_BUNDLE]
        xs, ys = build_axes(sem, local_routes, nodes, frozen)
        ix, iy, allowed = build_graph(xs, ys, nodes, frozen)
        pools = {}
        for rid in DEFAULT_BUNDLE:
            route_seed = seed + index * 100003 + sum(ord(ch) for ch in rid) * 101
            bucket = _candidate_pool(
                routes[rid], nodes, xs, ys, ix, iy, allowed, samples, route_seed,
            )
            skeleton_candidate = _skeleton_candidate(routes[rid], nodes, skeleton_by_id)
            if skeleton_candidate is not None:
                _merge_candidate(bucket, skeleton_candidate)
            pools[rid] = bucket

        pair_history = _repair_pairwise_gaps(
            pools=pools, routes=local_routes, nodes=nodes, xs=xs, ys=ys,
            frozen=frozen, rounds=pair_rounds, synth_samples=pair_samples,
            fixed_limit=pair_fixed, seed=seed + index * 7919,
        )
        conflicts = build_conflicts(pools)
        pair_rows = route_pair_compatibility(pools, conflicts=conflicts)
        impossible = [
            [row["routeA"], row["routeB"]]
            for row in pair_rows if row["compatiblePairs"] == 0
        ]
        ac3 = arc_consistency_prune(pools, conflicts=conflicts)
        arc_history = []
        if not impossible and ac3["status"] != "PASS" and arc_rounds > 0:
            arc_history = _repair_arc_empty_routes(
                pools=pools, routes=local_routes, nodes=nodes, xs=xs, ys=ys,
                frozen=frozen, rounds=arc_rounds, synth_samples=arc_samples,
                bundle_limit=arc_bundles, seed=seed + index * 104729,
            )
            conflicts = build_conflicts(pools)
            ac3 = arc_consistency_prune(pools, conflicts=conflicts)

        attempt = {
            "index": index,
            "portScore": port_score,
            "orientableGenus": 0.0,
            "portOverrides": {
                rid: {
                    "sourcePortFraction": routes[rid]["sourcePortFraction"],
                    "targetSide": routes[rid]["targetSide"],
                    "targetPortFraction": routes[rid]["targetPortFraction"],
                }
                for rid in DEFAULT_BUNDLE
            },
            "candidateCounts": {rid: len(pools[rid]) for rid in DEFAULT_BUNDLE},
            "impossibleRoutePairs": impossible,
            "ac3Status": ac3["status"],
            "ac3EmptyRoutes": list(ac3.get("emptyRoutes", [])),
            "ac3DomainSizes": _domain_summary(ac3),
            "pairRepair": pair_history,
            "arcRepair": arc_history,
        }
        rank = (
            len(impossible),
            len(attempt["ac3EmptyRoutes"]),
            -sum(attempt["ac3DomainSizes"].values()),
            port_score,
        )
        if best is None or rank < best[0]:
            best = (rank, copy.deepcopy(attempt))

        if not impossible and ac3["status"] == "PASS":
            result = find_first_solution(
                ac3["domains"], conflicts=conflicts,
                time_limit_seconds=max(0.1, min(15.0, deadline - time.monotonic())),
            )
            attempt["selector"] = {
                key: value for key, value in result.items() if key != "selection"
            }
            if result["status"] == "PASS":
                attempt["selection"] = {
                    rid: {
                        "family": candidate.family,
                        "cost": candidate.cost,
                        "points": [[x / 200.0, y / 200.0] for x, y in candidate.points],
                    }
                    for rid, candidate in result["selection"].items()
                }
                attempts.append(attempt)
                payload = {
                    "status": "PASS",
                    "scope": "LOCAL_5_ROUTE_WITNESS_ONLY",
                    "plan": plan,
                    "bundle": list(DEFAULT_BUNDLE),
                    "testedVariants": index,
                    "elapsedSeconds": time.monotonic() - start,
                    "variantGeneration": variant_stats,
                    "winner": attempt,
                    "attempts": attempts,
                    "warning": "Local witness only; full 18-Association topology/V1/V2/V3 still required.",
                }
                if checkpoint is not None:
                    Path(checkpoint).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                return payload
        attempts.append(attempt)
        write_checkpoint()

    return {
        "status": "FAIL",
        "scope": "LOCAL_5_ROUTE_DIAGNOSTIC",
        "plan": plan,
        "bundle": list(DEFAULT_BUNDLE),
        "testedVariants": len(attempts),
        "elapsedSeconds": time.monotonic() - start,
        "variantGeneration": variant_stats,
        "bestAttempt": best[1] if best else None,
        "attempts": attempts,
        "nextAction": (
            "Broaden target/source port search for the AC-3-empty route(s), then regenerate bundle families; "
            "do not spend CP-SAT time on a pool that fails pairwise or AC-3 prechecks."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default=DEFAULT_PLAN)
    parser.add_argument("--traveler-skeleton", type=Path)
    parser.add_argument("--variants", type=int, default=30)
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--pair-repair-rounds", type=int, default=1)
    parser.add_argument("--pair-synth-samples", type=int, default=3)
    parser.add_argument("--pair-fixed-limit", type=int, default=3)
    parser.add_argument("--arc-repair-rounds", type=int, default=1)
    parser.add_argument("--arc-synth-samples", type=int, default=4)
    parser.add_argument("--arc-bundle-limit", type=int, default=12)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--seconds", type=float, default=120.0)
    parser.add_argument("--vary-source", action="store_true",
                        help="search Traveler plus degree-1 provider source-port fractions")
    parser.add_argument("--include-left", action="store_true",
                        help="include LEFT target-side lanes in strategic search")
    parser.add_argument("--dense-targets", action="store_true",
                        help="use broader physical 0.10-cm target/source lane sampling")
    parser.add_argument("--target-lanes-per-side", type=int, default=7,
                        help="maximum target lanes retained per side in dense mode")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    payload = search(
        plan=args.plan, skeleton=args.traveler_skeleton,
        variants=args.variants, samples=args.samples,
        pair_rounds=args.pair_repair_rounds, pair_samples=args.pair_synth_samples,
        pair_fixed=args.pair_fixed_limit,
        arc_rounds=args.arc_repair_rounds, arc_samples=args.arc_synth_samples,
        arc_bundles=args.arc_bundle_limit,
        seed=args.seed, seconds=args.seconds, checkpoint=args.json_out,
        vary_source=args.vary_source, include_left=args.include_left,
        dense_targets=args.dense_targets,
        target_lanes_per_side=args.target_lanes_per_side,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
