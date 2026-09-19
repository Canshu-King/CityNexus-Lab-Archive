# GPT reference validation

## Original Solver checkpoint + new SRH tests

```text
SRH-01..05: 5 FAILED
```

Failures correspond to:

1. preference signal not wired;
2. V1 tries affected Activity after next C4;
3. V1 tries future affected slot with intervening mutable Activities;
4. post-gate solver rejection suppresses same heuristic semantic option;
5. heuristic complement mislabeled as post-gate fallback.

## Reference solver hardening copy

```text
SRH-01..05: 5 PASS
selected legacy solver integration tests: 15 PASS
Provider/Weather/Golden selected regression: 35 PASS
compileall: PASS
```

Ruff is not installed in this GPT container.
OR-Tools is not available and network package install failed, so real CP-SAT cannot be independently rerun here. Windows Codex must rerun the original 20 ORT gates with its installed `ortools==9.15.6755`.

## Agent policy reference

```text
10 PASS
```

This reference is intentionally pure and dependency-free. It is a semantic scaffold, not a claim that Agent runtime is already integrated into CityNexus.

## Patch check

Combined SRH reference patch:

```text
git apply --check = PASS
```

against a fresh copy of the uploaded Solver Runtime checkpoint.
