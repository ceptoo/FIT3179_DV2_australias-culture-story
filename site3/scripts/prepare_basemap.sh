#!/usr/bin/env bash
# ABS ASGS Edition 4 (2026) States and Territories -> 38 KB TopoJSON + state centroids.
# Needs: npm i -g mapshaper
# Usage: bash prepare_basemap.sh raw/STE_2026_AUST_GDA2020.shp data
# Keeps the 8 states/territories (drops Other Territories and Outside Australia),
# removes islands under 50 km2, simplifies to 0.2% of vertices.
set -e
SHP="$1"; OUT="${2:-data}"
mapshaper "$SHP" -filter '+STE_CODE26 <= 8' -filter-islands min-area=50km2 \
  -simplify 0.2% keep-shapes \
  -each 'state_code=STE_CODE26, state_name=STE_NAME26, state_abbr={"1":"NSW","2":"VIC","3":"QLD","4":"SA","5":"WA","6":"TAS","7":"NT","8":"ACT"}[STE_CODE26]' \
  -filter-fields state_code,state_name,state_abbr -rename-layers states \
  -o format=topojson quantization=1e5 "$OUT/aus_states.topojson"
mapshaper "$OUT/aus_states.topojson" -points inner \
  -each 'lon=+this.x.toFixed(4), lat=+this.y.toFixed(4)' -o format=csv "$OUT/state_centroids.csv"
