"""National Heritage List and World Heritage Areas -> small web files.

Usage:  python prepare_heritage.py raw/National_Heritage_List_Australia.geojson \
                                   raw/Australia_World_Heritage_Areas.geojson data
Needs:  pip install pandas shapely ; npm i -g mapshaper (for the outline file)
Steps:
  NHL: keep STATUS == "Listed place" (drops nominations and "within listed place" sub-parts).
       One point per polygon part (a point guaranteed inside the shape). Places that span
       several states/islands keep each part; nhl_by_year.csv counts each place once (by PLACE_ID).
  WHA: keep STATUS == "Declared property" (drops buffer zones). Merge parts of one property
       (e.g. the 11 Australian Convict Sites) into one record. Type comes from the listing's
       own criteria fields: natural only / cultural only / both = Mixed.
  on_main_map = false for places outside the mainland map frame (external territories,
       Macquarie Island, Lord Howe Island); filter them out of maps, keep them in counts.
"""
import sys, re, json, subprocess, tempfile, os
import pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

nhl_src, wha_src, out = sys.argv[1], sys.argv[2], sys.argv[3]
inside = lambda lon, lat: (-44.5 <= lat <= -9) and (112 <= lon <= 154.5)
tf = lambda b: "true" if b else "false"   # Vega reads lowercase booleans

# ---- National Heritage List ----
rows = []
for f in json.load(open(nhl_src))["features"]:
    p = f["properties"]
    if p["STATUS"] != "Listed place":
        continue
    pt = shape(f["geometry"]).representative_point()
    rows.append({"place_id": p["PLACE_ID"], "name": p["NAME"], "class": p["CLASS"], "state": p["STATE"],
                 "year": int(p["REGISTER_DATE"][:4]), "area_ha": round(p["AREA_HA"] or 0),
                 "on_main_map": tf(inside(pt.x, pt.y)), "lon": round(pt.x, 4), "lat": round(pt.y, 4),
                 "url": p["URL"]})
nhl = pd.DataFrame(rows).sort_values(["year", "name"])
nhl.to_csv(f"{out}/nhl_places.csv", index=False)
(nhl.drop_duplicates("place_id").groupby(["year", "class"]).size()
    .reset_index(name="places").to_csv(f"{out}/nhl_by_year.csv", index=False))

# ---- World Heritage Areas ----
groups = {}
for f in json.load(open(wha_src))["features"]:
    if f["properties"]["STATUS"] == "Declared property":
        groups.setdefault(f["properties"]["PLACE_ID"], []).append(f)
sites, feats = [], []
for pid, fs in groups.items():
    names = {re.sub(r"\s*\(.*\)\s*$", "", f["properties"]["NAME"]).strip() for f in fs}
    years = sorted({int(y) for f in fs for y in str(f["properties"]["INSCRIBED"]).split(",") if y.strip().isdigit()})
    nat = any(f["properties"]["NATURAL"] for f in fs)
    cul = any(f["properties"]["CULTURAL"] for f in fs)
    geom = unary_union([shape(f["geometry"]).buffer(0) for f in fs])
    pt = geom.representative_point()
    r = {"place_id": pid, "name": min(names, key=len),
         "type": "Mixed" if nat and cul else ("Natural" if nat else "Cultural"),
         "first_inscribed": years[0], "all_inscriptions": ";".join(map(str, years)),
         "states": "/".join(sorted({f["properties"]["STATE"] for f in fs})), "parts": len(fs),
         "hectares": round(sum(f["properties"]["HECTARES"] or 0 for f in fs)),
         "on_main_map": tf(inside(pt.x, pt.y)), "lon": round(pt.x, 4), "lat": round(pt.y, 4)}
    sites.append(r)
    if r["on_main_map"] == "true":
        feats.append({"type": "Feature", "geometry": mapping(geom),
                      "properties": {k: r[k] for k in ["place_id", "name", "type", "first_inscribed", "states", "hectares"]}})
pd.DataFrame(sites).sort_values("first_inscribed").to_csv(f"{out}/world_heritage_sites.csv", index=False)

tmp = os.path.join(tempfile.mkdtemp(), "wha.geojson")
json.dump({"type": "FeatureCollection", "features": feats}, open(tmp, "w"))
subprocess.run(["mapshaper", tmp, "-simplify", "0.6%", "keep-shapes", "-filter-islands", "min-vertices=4",
                "-rename-layers", "world_heritage", "-o", "format=topojson", "quantization=1e5",
                f"{out}/world_heritage.topojson"], check=True)
print(f"NHL: {len(nhl)} parts, {nhl.place_id.nunique()} places. WHA: {len(sites)} properties")
