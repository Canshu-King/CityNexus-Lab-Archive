export type LngLat = [number, number];

export interface JourneyMapActivity {
  id: string;
  semanticKey: string;
  name: string;
  coordinate: LngLat;
  status: 'PLANNED' | 'ACTIVE' | 'COMPLETED' | 'SKIPPED';
  protectedCommitment: boolean;
}

export interface JourneyRouteLayer {
  id: string;
  kind: 'ACTIVE_PLAN' | 'OLD_PLAN' | 'PROPOSED_PLAN';
  geojson: GeoJSON.Feature<GeoJSON.LineString>;
}

export interface JourneyMapModel {
  activities: JourneyMapActivity[];
  routes: JourneyRouteLayer[];
  eventCoordinate?: LngLat;
}
