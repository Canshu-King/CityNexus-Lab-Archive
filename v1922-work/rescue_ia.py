from pathlib import Path

# ---- 1) 底部导航：今天 / 行程 / 地图 / Copilot / 我的 --------------------
p = Path("D:/moodle/CityNexus/frontend/src/routes/v8Routes.ts")
s = p.read_text(encoding="utf-8")
old = '''export const mobileRoutes = [
  { key: "hub", label: "Journey", icon: "map" },
  { key: "map", label: "Map", icon: "map" },
  { key: "agent", label: "AI", icon: "spark" },
  { key: "bookings", label: "Bookings", icon: "ticket" },
  { key: "me", label: "Me", icon: "user" },
] as const;'''
new = '''// Official primary navigation (see docs/DESIGN_CORRECTIONS_REQUIRED.md §1).
// Wallet/bookings deliberately left the golden path; they now live under
// Trips ("预订与凭证") and Me ("钱包").
export const mobileRoutes = [
  { key: "hub", label: "Today", icon: "map" },
  { key: "trips", label: "Trips", icon: "calendar" },
  { key: "map", label: "Map", icon: "map" },
  { key: "agent", label: "Copilot", icon: "spark" },
  { key: "me", label: "Me", icon: "user" },
] as const;'''
assert old in s, "mobileRoutes not found"
p.write_text(s.replace(old, new, 1), encoding="utf-8", newline="\n")

# ---- 2) i18n 新增 trips 文案 -------------------------------------------
p = Path("D:/moodle/CityNexus/frontend/src/i18n/LocaleContext.tsx")
s = p.read_text(encoding="utf-8")
old_en = '''  "mobile.today": "Today",'''
new_en = '''  "nav.trips": "Trips",
  "mobile.trips": "Trips",
  "mobile.today": "Today",'''
assert old_en in s, "EN mobile.today not found"
s = s.replace(old_en, new_en, 1)
old_cn = '''  "mobile.today": "今天",'''
new_cn = '''  "nav.trips": "行程",
  "mobile.trips": "行程",
  "mobile.today": "今天",'''
assert old_cn in s, "CN mobile.today not found"
s = s.replace(old_cn, new_cn, 1)
p.write_text(s, encoding="utf-8", newline="\n")

# ---- 3) Trips 面板聚合行程 + 预订 --------------------------------------
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")
old = '''          {route === "bookings" && ('''
new = '''          {route === "trips" && (
            <>
              <Studio
                data={data}
                selected={selected}
                onNavigate={navigate}
                onRain={triggerRain}
              />
              <Bookings
                data={data}
                selected={selected}
                wallet={wallet}
                onImport={importReservation}
                busy={busy}
              />
            </>
          )}
          {route === "bookings" && ('''
assert old in s, "bookings dispatch not found"
s = s.replace(old, new, 1)

old_label = '''            <span>{t(({ hub: "mobile.today", agent: "mobile.copilot", bookings: "mobile.wallet" } as Record<string, string>)[item.key] ?? "nav." + item.key)}</span>'''
new_label = '''            <span>{t(({ hub: "mobile.today", trips: "mobile.trips", agent: "mobile.copilot", bookings: "mobile.wallet" } as Record<string, string>)[item.key] ?? "nav." + item.key)}</span>'''
assert old_label in s, "mobile label lookup not found"
s = s.replace(old_label, new_label, 1)

old_known = '''{t("nav." + (route in { hub: 1, studio: 1, stay: 1, discover: 1, live: 1, bookings: 1, intelligence: 1, twin: 1, agent: 1, authoritative: 1, map: 1, me: 1 } ? route : "hub"))}'''
new_known = '''{t("nav." + (route in { hub: 1, trips: 1, studio: 1, stay: 1, discover: 1, live: 1, bookings: 1, intelligence: 1, twin: 1, agent: 1, authoritative: 1, map: 1, me: 1 } ? route : "hub"))}'''
assert old_known in s, "known-route lookup not found"
s = s.replace(old_known, new_known, 1)
p.write_text(s, encoding="utf-8", newline="\n")

# ---- 4) 默认入口进入现代产品，Legacy 移到 /legacy -----------------------
p = Path("D:/moodle/CityNexus/frontend/src/main.tsx")
s = p.read_text(encoding="utf-8")
old = '''function App() {
  return window.location.pathname.startsWith("/v8") ? <V8Experience /> : <LegacyApp />;
}'''
new = '''function App() {
  // The default entry is the modern traveler product.  LegacyApp is retained
  // for internal/back-compat access only, behind an explicit /legacy path, so a
  // first-time user never lands on the legacy surface (see PHASE 2).
  const path = window.location.pathname;
  if (path.startsWith("/legacy")) return <LegacyApp />;
  return <V8Experience />;
}'''
assert old in s, "App entry not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("IA 改造已应用")
