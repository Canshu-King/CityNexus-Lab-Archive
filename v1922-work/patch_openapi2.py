"""Add the RecoveryState / Error component schemas."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/contracts/openapi.yaml")
s = P.read_text(encoding="utf-8")

old = """    ErrorEnvelope:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message, trace_id]
          properties:
            code: {type: string}
            message: {type: string}
            details: {type: object, additionalProperties: true}
            trace_id: {type: string}"""

new = """    ErrorEnvelope:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message, trace_id]
          properties:
            code: {type: string}
            message: {type: string}
            details: {type: object, additionalProperties: true}
            trace_id: {type: string}
    Error:
      $ref: '#/components/schemas/ErrorEnvelope'
    RecoveryState:
      description: >-
        Durable, governed recovery state.  Present only when a confirmed HARD
        capability (or an evidence regression) invalidated the active plan.
        The active plan is never silently mutated.
      type: object
      nullable: true
      required: [state, requires_user_decision, silent_plan_mutation]
      properties:
        state:
          type: string
          enum: [RECOVERY_REQUIRED, RECOVERY_REQUIRED_NO_ALTERNATIVE, RESOLVED]
        kind: {type: string, example: CAPABILITY_HARD_RECOVERY}
        event_id: {type: string, format: uuid}
        event_status: {type: string, enum: [DETECTED, ACKNOWLEDGED, RESOLVED]}
        capability_code: {type: string, nullable: true}
        active_plan_version_id: {type: string, format: uuid, nullable: true}
        failures: {type: array, items: {type: string}}
        candidate_plan_count: {type: integer}
        candidate_plan_ids: {type: array, items: {type: string, format: uuid}}
        requires_user_decision: {type: boolean}
        silent_plan_mutation: {type: boolean, enum: [false]}
        actions:
          type: array
          items:
            type: string
            enum: [REPLAN, ACKNOWLEDGE_NO_ALTERNATIVE]
        detected_at: {type: string, format: date-time}
        journey_status: {type: string}"""

assert old in s, "ErrorEnvelope block not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("schemas added")
