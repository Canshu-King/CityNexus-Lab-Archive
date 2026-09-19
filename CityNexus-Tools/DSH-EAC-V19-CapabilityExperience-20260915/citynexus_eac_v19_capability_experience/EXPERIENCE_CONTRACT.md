# Experience Contract

The UI must distinguish:

- HARD_ACCESSIBILITY_NEED
- CARE_REQUIREMENT
- PHYSICAL_LIMIT
- TRIP_CONTEXT
- SOFT_PREFERENCE
- PROTECTED_COMMITMENT

And evidence states:

- VERIFIED
- UNVERIFIED
- CONFLICT
- NEEDS_LIVE_EVIDENCE

Unknown must never be rendered as “accessible”.

Primary UX surfaces:

1. optional setup needs;
2. Copilot detected-needs confirmation;
3. Traveler Twin / profile summary;
4. planning candidate capability explanation;
5. Recovery diff;
6. mobile active-journey warnings.

Do not implement backend authority in localStorage.
