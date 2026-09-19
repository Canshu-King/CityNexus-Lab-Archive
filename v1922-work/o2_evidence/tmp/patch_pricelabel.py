from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/features/stay/StayExplorer.tsx")
s = p.read_text(encoding="utf-8")

old = '''  if (minor === null || minor === undefined) {
    return zh ? "价格未知（供应商未提供）" : "Price unknown (not provided)";
  }
  return `${money(minor, currency, locale)} · ${currency || "CNY"}`;'''
new = '''  // A missing OR zero amount is not a price.  OSM carries no rate, so a live
  // stay arrives as 0; printing "CNY 0.00" would read as a free room.
  if (minor === null || minor === undefined || minor <= 0) {
    return zh
      ? "价格未知（供应商未提供房价）"
      : "Price unknown (no provider rate)";
  }
  return `${money(minor, currency, locale)} · ${currency || "CNY"}`;'''
assert s.count(old) == 1, "priceLabel anchor"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("priceLabel patched")
