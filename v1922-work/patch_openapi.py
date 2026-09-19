"""Document the V19.2.2 response schemas affected by this round."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/contracts/openapi.yaml")
s = P.read_text(encoding="utf-8")

# 1. Journey capability confirm -> durable recovery state.
old = """  /journeys/{journey_id}/capabilities/confirm:
    parameters: [{$ref: '#/components/parameters/JourneyId'}]
    post:
      operationId: confirmJourneyCapabilities
      requestBody:
        required: true
        content:
          application/json:
            schema: {type: array, items: {type: object}}
      responses:
        '200': {description: Confirmed journey capability facts}"""
new = """  /journeys/{journey_id}/capabilities/confirm:
    parameters: [{$ref: '#/components/parameters/JourneyId'}]
    post:
      operationId: confirmJourneyCapabilities
      requestBody:
        required: true
        content:
          application/json:
            schema: {type: array, items: {type: object}}
      responses:
        '200':
          description: >-
            Confirmed journey capability facts.  When a newly confirmed HARD
            capability invalidates the ACTIVE plan, `recovery` carries the
            durable governed recovery state; the active plan is never silently
            rewritten.
          content:
            application/json:
              schema:
                type: object
                properties:
                  journey_id: {type: string, format: uuid}
                  capabilities: {type: array, items: {type: object}}
                  summary: {type: object}
                  traveler_twin: {type: object}
                  active_plan_feasibility:
                    type: object
                    nullable: true
                    properties:
                      passed: {type: boolean, nullable: true}
                      failures: {type: array, items: {type: string}}
                      state:
                        type: string
                        enum: [PLAN_FEASIBLE, REPLAN_REQUIRED, NO_ACTIVE_PLAN]
                  recovery: {$ref: '#/components/schemas/RecoveryState'}"""
assert old in s, "journey capability confirm block not found"
s = s.replace(old, new, 1)

# 2. Experience -> recovery + flags.
old2 = """  /journeys/{journey_id}/experience:
    get:
      operationId: getJourneyExperience
      responses:
        '200': {description: Stay-aware Journey experience, content: {application/json: {schema: {type: object}}}}"""
new2 = """  /journeys/{journey_id}/experience:
    get:
      operationId: getJourneyExperience
      responses:
        '200':
          description: >-
            Stay-aware Journey experience.  `recovery` exposes the durable
            mid-trip HARD recovery state and `experience_flags` exposes the
            stale / re-sync condition so the phone UI can act on it.
          content:
            application/json:
              schema:
                type: object
                properties:
                  journey: {type: object}
                  trip: {type: object}
                  recovery: {$ref: '#/components/schemas/RecoveryState'}
                  experience_flags:
                    type: object
                    properties:
                      needs_review: {type: boolean}
                      recovery_required: {type: boolean}
                      staleness: {type: boolean}
                      feasibility_failures: {type: array, items: {type: string}}"""
assert old2 in s, "experience block not found"
s = s.replace(old2, new2, 1)

# 3. Start -> stale/recompose rejection is documented.
old3 = """  /journeys/{journey_id}/start:
    parameters:
      - {$ref: '#/components/parameters/JourneyId'}
    post:
      operationId: startJourney
      responses:
        '200':
          description: Journey started
          content:
            application/json:
              schema: {$ref: '#/components/schemas/JourneyTwin'}
        '409': {$ref: '#/components/responses/Conflict'}"""
new3 = """  /journeys/{journey_id}/start:
    parameters:
      - {$ref: '#/components/parameters/JourneyId'}
    post:
      operationId: startJourney
      responses:
        '200':
          description: Journey started only when the selected plan is still feasible
          content:
            application/json:
              schema: {$ref: '#/components/schemas/JourneyTwin'}
        '409':
          description: >-
            Refused.  The selected plan failed the same truth policy used by
            select/booking: `STALE_RECOMPOSE_REQUIRED` for expired or
            inconsistent frozen evidence, `START_BLOCKED_INFEASIBLE` for a hard
            constraint or accessibility conflict.  The Journey does not become
            ACTIVE.
          content:
            application/json:
              schema: {$ref: '#/components/schemas/Error'}"""
assert old3 in s, "start block not found"
s = s.replace(old3, new3, 1)

P.write_text(s, encoding="utf-8", newline="\n")
print("openapi paths updated")
