from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''// Alternate paths people share or type.  A deep link that lands on an unknown
// key used to render an empty content area, so refresh/share produced a blank
// page.  Map the known aliases onto real routes; anything else falls back to
// Today rather than nothing.
const ROUTE_ALIASES: Record<string, string> = {
  today: "hub",
  copilot: "agent",
  wallet: "trips",
  bookings: "trips",
  itinerary: "trips",
  stay: "trips",
  stays: "trips",
  home: "hub",
  me: "me",
};

const KNOWN_ROUTES = new Set<string>([
  ...desktopRoutes.map((r) => r.key),
  ...mobileRoutes.map((r) => r.key),
]);

function routeFromPath() {
  const raw = window.location.pathname.replace(/^\/v8\/?/, "").replace(/\/$/, "");
  if (!raw) return "hub";
  const key = raw.split("/")[0].toLowerCase();
  const alias = ROUTE_ALIASES[key];
  if (alias) return alias;
  if (KNOWN_ROUTES.has(key)) return key;
  // Never render an empty shell: an unknown path is Today.
  return "hub";'''

new = '''// Alternate paths people share or type.  A deep link that lands on an unknown
// key used to render an empty content area, so refresh/share produced a blank
// page.  Map the known aliases onto real routes; anything else falls back to
// Today rather than nothing.
//
// An alias must never shadow a route the product itself navigates to.  "stay"
// and "bookings" are real desktop routes, so aliasing them to "trips" made a
// hard refresh silently swap the surface: the traveller opened 住宿选择, then
// reloading showed the Trips workspace instead.
const ROUTE_ALIASES: Record<string, string> = {
  today: "hub",
  copilot: "agent",
  wallet: "trips",
  itinerary: "trips",
  stays: "trips",
  home: "hub",
};

const KNOWN_ROUTES = new Set<string>([
  ...desktopRoutes.map((r) => r.key),
  ...mobileRoutes.map((r) => r.key),
]);

function routeFromPath() {
  const raw = window.location.pathname.replace(/^\/v8\/?/, "").replace(/\/$/, "");
  if (!raw) return "hub";
  const key = raw.split("/")[0].toLowerCase();
  // A real route wins over an alias, otherwise refresh changes the screen.
  if (KNOWN_ROUTES.has(key)) return key;
  const alias = ROUTE_ALIASES[key];
  if (alias) return alias;
  // Never render an empty shell: an unknown path is Today.
  return "hub";'''

assert s.count(old) == 1, "route block not found"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("route precedence patched")
