import { useEffect, useRef, useState } from "react";
import maplibregl, { type FlyToOptions } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useT } from "../i18n";
import { fitBoundsOptions, mapCameraOptions, motionDuration } from "../motion";
import { testIds } from "../testids";
import type { MapCameraCommand } from "../types";

const ROUTE: GeoJSON.Feature<GeoJSON.LineString> = {
  type: "Feature",
  properties: { provenance: "recorded-fixture://route-rain-001" },
  geometry: {
    type: "LineString",
    coordinates: [
      [117.2005, 39.1168],
      [117.2051, 39.1211],
      [117.2108, 39.1264],
      [117.2163, 39.1322],
      [117.2224, 39.1375],
    ],
  },
};

const STOPS: Array<{ name: string; coordinate: [number, number]; protected?: boolean }> = [
  { name: "Wudadao", coordinate: [117.2005, 39.1168] },
  { name: "Haihe cruise · C4", coordinate: [117.2108, 39.1264], protected: true },
  { name: "Ancient Culture Street", coordinate: [117.2163, 39.1322] },
  { name: "Tianjin Museum", coordinate: [117.2224, 39.1375] },
];

const CAMERA: MapCameraCommand = {
  center: [117.211, 39.127],
  zoom: 13.2,
  duration_token: "map",
  animate: true,
};

export function MapCanvas() {
  const t = useT();
  const host = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [ready, setReady] = useState(false);
  const [fallback, setFallback] = useState(false);
  const [lastCamera, setLastCamera] = useState("idle");

  useEffect(() => {
    if (!host.current || mapRef.current) return undefined;
    let map: maplibregl.Map;
    try {
      map = new maplibregl.Map({
        container: host.current,
        style: {
          version: 8,
          sources: {
            "route-fixture": { type: "geojson", data: ROUTE },
            "stops-fixture": {
              type: "geojson",
              data: {
                type: "FeatureCollection",
                features: STOPS.map((stop) => ({
                  type: "Feature",
                  properties: { name: stop.name, protected: Boolean(stop.protected) },
                  geometry: { type: "Point", coordinates: stop.coordinate },
                })),
              } as GeoJSON.FeatureCollection,
            },
          },
          layers: [
            { id: "background", type: "background", paint: { "background-color": "#0c1b22" } },
            {
              id: "route",
              type: "line",
              source: "route-fixture",
              paint: { "line-color": "#42d3b0", "line-width": 4, "line-opacity": 0.9 },
            },
            {
              id: "stops",
              type: "circle",
              source: "stops-fixture",
              paint: {
                "circle-radius": ["case", ["get", "protected"], 8, 5],
                "circle-color": ["case", ["get", "protected"], "#f5b942", "#7bd8ff"],
                "circle-stroke-width": 2,
                "circle-stroke-color": "#08151a",
              },
            },
          ],
        },
        center: CAMERA.center,
        zoom: CAMERA.zoom,
        attributionControl: false,
      });
      mapRef.current = map;
      map.on("load", () => setReady(true));
      map.on("error", () => setFallback(true));
    } catch {
      setFallback(true);
      return undefined;
    }
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  const applyCamera = (command: MapCameraCommand, mode: "center" | "bounds") => {
    const map = mapRef.current;
    if (!map) return;
    if (mode === "center") {
      map.flyTo(mapCameraOptions(command) as FlyToOptions);
      setLastCamera(`flyTo · ${motionDuration(command.duration_token)}ms`);
    } else if (command.bounds) {
      map.fitBounds(command.bounds, fitBoundsOptions(command));
      setLastCamera(`fitBounds · ${motionDuration(command.duration_token)}ms`);
    }
  };

  return (
    <div
      className="map"
      data-testid={testIds.mapCanvas}
      data-map-ready={ready ? "true" : "false"}
      data-map-mode={fallback ? "fallback-static" : "maplibre"}
      data-camera-contract="flyTo/fitBounds"
      data-camera-duration={motionDuration("map")}
    >
      <div ref={host} className="map__host" aria-label="Recorded route map" />
      {(!ready || fallback) && (
        <div className="map__fallback">
          <svg viewBox="0 0 320 180" role="img" aria-label="Static route evidence">
            <polyline
              points="20,140 90,110 160,84 235,48 300,22"
              fill="none"
              stroke="#42d3b0"
              strokeWidth="4"
            />
            <circle cx="90" cy="110" r="7" fill="#f5b942" />
            <circle cx="160" cy="84" r="5" fill="#7bd8ff" />
            <circle cx="235" cy="48" r="5" fill="#7bd8ff" />
          </svg>
          <small>{t("map.fallback")}</small>
        </div>
      )}
      <div className="map__controls">
        <button type="button" className="btn" onClick={() => applyCamera(CAMERA, "center")}>
          {t("map.recenter")}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() =>
            applyCamera(
              {
                bounds: [
                  [117.195, 39.111],
                  [117.228, 39.142],
                ],
                duration_token: "map",
                animate: true,
              },
              "bounds",
            )
          }
        >
          {t("map.fitBounds")}
        </button>
        <span className="map__camera" data-testid="map-camera-status">
          {t("map.camera")}: {lastCamera} · {motionDuration("map")}ms
        </span>
      </div>
    </div>
  );
}
