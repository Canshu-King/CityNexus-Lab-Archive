import bbox from '@turf/bbox';
import type { Feature, FeatureCollection, Geometry } from 'geojson';

export function fitBoundsForFeatures(
  features: Array<Feature<Geometry>>,
): [number, number, number, number] | null {
  if (features.length === 0) return null;
  const collection: FeatureCollection = {
    type: 'FeatureCollection',
    features,
  };
  return bbox(collection) as [number, number, number, number];
}
