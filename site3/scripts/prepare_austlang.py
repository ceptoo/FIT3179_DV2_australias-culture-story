"""Trim the AIATSIS AUSTLANG CSV into a small Vega-Lite-ready file, with state names.

Usage:  python prepare_austlang.py raw/AustLang.csv raw/STE_2026_AUST_GDA2020.shp data/austlang.csv
Needs:  pip install pandas shapely pyshp
Steps:
  1. Keep code, name, lat, lon. Drop records with no location (coded 0,0) or outside Australia.
  2. Drop entries whose name is marked "(retired)".
  3. Find the state each point falls in (ABS ASGS 2026 boundaries). Points just offshore
     (island languages, e.g. Torres Strait) take the nearest state.
"""
import sys
import pandas as pd
import shapefile
from shapely.geometry import shape, Point

src, ste, out = sys.argv[1], sys.argv[2], sys.argv[3]
df = pd.read_csv(src, encoding="utf-8-sig")
df = df.rename(columns={"language_code": "code", "language_name": "name",
                        "approximate_latitude_of_language_variety": "lat",
                        "approximate_longitude_of_language_variety": "lon"})[["code", "name", "lat", "lon"]]
n0 = len(df)
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df = df[df["lat"].between(-44.5, -9) & df["lon"].between(112, 154.5)]
df = df[~df["name"].str.contains("(retired)", regex=False)]

polys = [(r.record["STE_NAME26"], shape(r.shape.__geo_interface__))
         for r in shapefile.Reader(ste).shapeRecords() if r.record["STE_CODE26"] in list("12345678")]

def state_of(lon, lat):
    p = Point(lon, lat)
    for name, g in polys:
        if g.contains(p):
            return name
    return min(polys, key=lambda ng: ng[1].distance(p))[0]

df["state"] = [state_of(x, y) for x, y in zip(df["lon"], df["lat"])]
df["lat"] = df["lat"].round(4)
df["lon"] = df["lon"].round(4)
df[["code", "name", "state", "lat", "lon"]].to_csv(out, index=False)
print(f"{n0} records in, {len(df)} out")
