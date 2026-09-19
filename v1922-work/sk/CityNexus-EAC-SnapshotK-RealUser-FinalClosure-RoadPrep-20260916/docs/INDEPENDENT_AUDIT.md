# Independent audit of Snapshot K candidate

## Confirmed progress

Independent source inspection agrees that Snapshot K candidate materially fixes:

- structural semantic-key preservation in replan paths;
- exclusion of server-owned structural Places from replacement candidates;
- mobility key normalisation;
- precise replan reason ordering;
- structural stay-role survival in the simple regression fixture;
- exact-time preservation for the tested locked activity fixture.

The package also correctly refuses to claim product readiness.

## New P0-1 — multi-day stay scheduling can place CHECK_IN after the first STAY

The new scheduler still processes **all carried activities first** and only then
places CHECK_IN / CHECK_OUT / LUGGAGE_DROP.

With a realistic multi-day carried itinerary, this can push check-in to the
second day while the first overnight remains on night one.

Independent replay of the exact submitted scheduling functions produced:

```text
ARRIVAL     2026-11-06 10:00
...
STAY        2026-11-06 22:00 -> 2026-11-07 06:00
ACTIVITY    2026-11-07 09:00 -> 10:00
CHECK_IN    2026-11-07 10:24 -> 10:44
...
```

Therefore:

`CHECK_IN before first STAY = false`

A traveller cannot spend the first night before checking in.

The existing B1 chronological test misses this because it checks only:
- chronological timestamps;
- CHECK_IN < CHECK_OUT.

It does **not** assert:
- CHECK_IN < first STAY;
- first STAY belongs to an already checked-in stay;
- CHECK_OUT follows the final STAY.

## New P0-2 — a flexible activity can overlap a locked activity

The new code preserves the locked activity's exact window, which is good.

But it does not reserve that window before scheduling earlier flexible items.

Independent replay produced:

```text
flexible activity 10:25 -> 12:25
locked activity   12:00 -> 13:00
```

The two overlap.

`_enforce_sequence()` preserves both locked truth and the already-placed
flexible activity, so the overlap survives.

The existing B2 test uses a generous fixture where the overlap does not occur;
it does not prove the scheduler can actually route flexible work around an
arbitrary locked window.

Required invariant:

- locked windows are inserted into the calendar first;
- flexible activities are scheduled only inside free windows around them;
- no overlap may survive;
- if no free window exists, return an explicit conflict rather than silently
  dropping or overlapping activity.

## B4 is improved, but the policy is still too permissive

The code still says:

CLOSURE / WEATHER with no explicit target
-> if `journey.current_activity_id` exists, use it as the affected target.

The traveller's current execution position proves where they are.
It does **not** prove that the vague statement:

“有个景点关了”

refers to the current activity.

For physical closure/weather targeting, automatic target resolution should
require one of:

- explicit affected_activity_id / affected_place_id;
- provider-linked affected entity;
- high-confidence semantic target resolution.

The current location may be a useful clarification suggestion, but it should not
be silently promoted to the closed target.

Existing pre-Snapshot tests that rely on target-less CLOSURE fixtures should be
updated to send an explicit target rather than defining product truth.

## B5 is still not acceptance-complete

The identity mismatch is plausibly improved, but the package explicitly did not
complete:

real Xiamen plan
-> choose hotel
-> reload
-> close mutable POI
-> material replan

This exact chain remains mandatory.

## Networking note

`real_city.py` now hardcodes `trust_env=False` for public discovery clients.

That solved one machine's proxy timeout, but it is risky for a China-based
traveller/developer environment where Nominatim/Overpass may require the user's
proxy path.

Prefer a provider/config setting over globally ignoring proxy environment.

Do not let one local proxy incident become permanent network policy.

## Product status

No frontend source was changed in this package.

Therefore the major consumer gaps are unchanged:
- consumer order import;
- activity detail;
- useful Copilot;
- reference-quality mobile UI;
- full same-Xiamen visible-UI run;
- physical Xiaomi test.

Independent verdict:

`BLOCKED_FOR_REAL_USER_TRIAL`
