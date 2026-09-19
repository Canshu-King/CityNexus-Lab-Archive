from pathlib import Path

p = Path("D:/moodle/CityNexus/contracts/openapi.yaml")
s = p.read_text(encoding="utf-8")

anchor = """  /journeys/{journey_id}/stays/offers/capture:"""
new = """  /journeys/{journey_id}/recovery/acknowledge:
    parameters: [{$ref: '#/components/parameters/JourneyId'}]
    post:
      operationId: acknowledgeJourneyRecovery
      responses:
        '200':
          description: >-
            Governed acknowledgement of an open recovery warning.  Records that
            the traveller saw the warning; it never resolves the recovery, never
            marks an infeasible plan safe, and never lets stale evidence look
            current.  `experience_flags.needs_review` stays true until a
            revalidated feasible plan is actually selected.
          content:
            application/json:
              schema:
                type: object
                properties:
                  journey_id: {type: string, format: uuid}
                  acknowledged: {type: boolean}
                  resolved: {type: boolean, enum: [false]}
                  recovery: {$ref: '#/components/schemas/RecoveryState'}
        '404': {$ref: '#/components/responses/NotFound'}
  /journeys/{journey_id}/stays/offers/capture:"""
assert anchor in s, "stays capture anchor not found"
s = s.replace(anchor, new, 1)

# RecoveryState 增加本轮字段
old_state = """      required: [state, requires_user_decision, silent_plan_mutation]
      properties:
        state:
          type: string
          enum: [RECOVERY_REQUIRED, RECOVERY_REQUIRED_NO_ALTERNATIVE, RESOLVED]"""
new_state = """      required: [state, requires_user_decision, silent_plan_mutation]
      properties:
        state:
          type: string
          enum: [RECOVERY_REQUIRED, RECOVERY_REQUIRED_NO_ALTERNATIVE, RESOLVED]
        acknowledged: {type: boolean}
        acknowledged_at: {type: string, format: date-time, nullable: true}
        replan_attempted: {type: boolean}
        no_alternative: {type: boolean}"""
assert old_state in s, "RecoveryState block not found"
s = s.replace(old_state, new_state, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("契约已更新")
