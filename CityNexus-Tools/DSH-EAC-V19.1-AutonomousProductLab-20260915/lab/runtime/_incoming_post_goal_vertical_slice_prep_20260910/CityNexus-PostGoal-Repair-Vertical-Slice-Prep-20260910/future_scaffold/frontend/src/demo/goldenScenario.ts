import { cityNexusApi, type Activity, type PlanVersion } from "../api/citynexus";
import type { JourneyTwin } from "../contracts/journeyTwin";
import type { ReplanProposal } from "../contracts/replan";

export interface GoldenScenarioSession {
  journeyId: string;
  plan: PlanVersion;
  techArt: Activity;
  riverCruise: Activity;
  twin: JourneyTwin;
}

export async function bootstrapGoldenScenario(): Promise<GoldenScenarioSession> {
  const ids = await cityNexusApi.resetDemo();
  const [plan] = await cityNexusApi.generatePlans(ids.journey_id, 1);
  if (!plan) throw new Error("No deterministic demo plan was generated");
  await cityNexusApi.selectPlan(ids.journey_id, plan.id);

  const riverCruise = plan.activities.find((item) => item.place_id === "place-river-cruise");
  const techArt = plan.activities.find((item) => item.place_id === "place-tech-art");
  if (!riverCruise || !techArt) throw new Error("Golden Scenario fixture activities are missing");

  const booking = await cityNexusApi.createBooking(ids.journey_id, riverCruise.id);
  await cityNexusApi.captureBooking(
    ids.journey_id,
    booking,
    `frontend-golden-capture-${ids.journey_id}`,
  );
  const twin = await cityNexusApi.startJourney(ids.journey_id);
  return { journeyId: ids.journey_id, plan, techArt, riverCruise, twin };
}

export async function injectClosureAndLoadCandidates(
  session: GoldenScenarioSession,
  occurredAt = "2026-10-10T13:25:00+08:00",
): Promise<ReplanProposal[]> {
  const event = await cityNexusApi.createClosureEvent(
    session.journeyId,
    session.techArt.id,
    occurredAt,
  );
  await cityNexusApi.generateReplans(session.journeyId, event.id, 3);
  const all = await cityNexusApi.listReplans(session.journeyId);
  return all.filter((item) => item.status === "PRESENTED");
}
