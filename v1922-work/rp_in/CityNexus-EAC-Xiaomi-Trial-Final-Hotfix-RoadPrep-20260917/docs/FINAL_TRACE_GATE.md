# Final trace gate

A final trace is accepted only if:

1. generated after the last relevant source modification;
2. one Xiamen journey_id throughout;
3. candidate plan ids recorded;
4. plan selection is a visible UI action;
5. hotel selection is a visible UI action;
6. booking confirmation is a visible UI action;
7. Copilot answer is captured after the final Copilot fix;
8. replan has a material before/after diff;
9. accept is a visible UI action;
10. final Trips/Live/backend state comparison uses a defined mapping.

Do not write "consistent" without specifying:
- which entity set;
- which filters;
- expected cardinality/mapping.

Stay truth:
- must contain actual check-in/check-out timestamps or explicitly explain absence;
- `undefined` cannot be a PASS value.
