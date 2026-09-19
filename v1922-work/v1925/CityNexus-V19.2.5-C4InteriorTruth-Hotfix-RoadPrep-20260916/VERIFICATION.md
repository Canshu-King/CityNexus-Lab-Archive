# Verification

Starter patch apply-check against reconstructed exact Snapshot G:
- return code: 0
- stderr: (empty)

Independent post-patch probe:
- MID_TRIP before ARRIVAL: rejected
- MID_TRIP after DEPARTURE: rejected
- role-less lock before ARRIVAL: rejected
- valid MID_TRIP inside boundaries: accepted
- valid role-less lock inside boundaries: accepted

Previous V19.2.4 F01-F04 probe remained 4/4 PASS.
