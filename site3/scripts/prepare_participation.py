"""Arts participation: Creative Australia NAPS 2022 + 2025, and ABS attendance by state 2017-18 vs 2021-22.

Usage:
  python prepare_participation.py <raw_b3_dir> <out_dir>
  <raw_b3_dir> must contain:
    NAPS-2022-Data-Tables.xlsx, NAPS_2025_Tables_All_Australians.xlsx, NAPS_2025_Tables_<STATE>.xlsx (x8)
    cultural_and_creative_activities_202122_tables_14_to_21.xlsx            (ABS, Table 14)
    Attendance_at_selected_cultural_venues_and_events_Australia_2017-18.xls (ABS 4114.0, Table 1)
Needs: pip install pandas openpyxl xlrd

NAPS figures are survey percentages of people aged 15+ (2022: n = 9,396; 2025: n = 9,065).
Only measures asked the same way in both years are paired. 'Own cultural background' is paired
with a caveat: the 2022 table measures "engagement ... through the arts", the 2025 table
"attended arts of own cultural background"; the wording differs, so compare with care.
State NAPS samples are small (e.g. NT n = 172, TAS and ACT also small), so state figures are indicative.
"""
import sys, os, re
import openpyxl, xlrd
import pandas as pd

RAW, OUT = sys.argv[1], sys.argv[2]

def rows(fn, sheet):
    wb = openpyxl.load_workbook(os.path.join(RAW, fn), read_only=True, data_only=True)
    return [list(r) for r in wb[sheet].iter_rows(values_only=True)]

def table(fn, sheet):
    """Return {row label: value in the 'Total' column}, plus the base n."""
    t = rows(fn, sheet)
    hdr = next(r for r in t if r[0] and str(r[0]).strip() == "Column %")
    out, n = {}, None
    for r in t[t.index(hdr) + 1:]:
        if not r[0]:
            continue
        lab = re.sub(r"\s+", " ", str(r[0])).strip()
        if lab == "Column n":
            n = r[1]
            break
        if isinstance(r[1], (int, float)):
            out[lab] = r[1]
    return out, n

# ---------------- NAPS 2022 vs 2025, national ----------------
PAIRS = {  # domain: [(label for chart, 2022 row, 2025 row)]
    "Attended live arts": ("NAPS-2022-Data-Tables.xlsx", "Table 1", "Table 1", [
        ("Any live arts event or festival", "Total", "Attend Live"),
        ("Music", "Music", "Attend music"),
        ("Festivals", "Festivals", "Attend festivals"),
        ("Visual arts and craft", "Visual arts and crafts", "Attend visual arts"),
        ("Theatre", "Theatre", "Attend theatre"),
        ("First Nations arts or festivals", "First Nations arts and festivals", "Attend First Nations arts or festivals"),
        ("Dance", "Dance", "Attend dance"),
        ("Literary events", "Literary events", "Attend literary events"),
    ]),
    "Created art themselves": ("NAPS-2022-Data-Tables.xlsx", "Table 6", "Table 5", [
        ("Music", "Music", "Create music"),
        ("Writing", "Writing", "Create writing"),
        ("Visual arts and craft", "Visual arts and craft", "Create visual arts and craft"),
        ("Dance", "Dance", "Create dance"),
        ("Theatre", "Theatre", "Create theatre"),
    ]),
    "Arts of own cultural background": ("NAPS-2022-Data-Tables.xlsx", "Table 4", "Table 3", [
        ("At least one event", "Total engagement with own cultural background", "AT LEAST ONE EVENT"),
        ("Music", "Music", "Music"),
        ("Festival or celebration", "Festival or celebration", "Festival or celebration"),
        ("Theatre", "Theatre", "Theatre"),
        ("Visual arts and craft", "Visual arts and craft", "Visual arts and craft"),
        ("Dance", "Dance", "Dance"),
        ("Book or literary events", "Book or literary events", "Book or literary events"),
    ]),
}
N25 = "NAPS_2025_Tables_All_Australians.xlsx"
recs = []
for domain, (f22, s22, s25, items) in PAIRS.items():
    t22, n22 = table(f22, s22)
    t25, n25 = table(N25, s25)
    for label, k22, k25 in items:
        recs.append(dict(domain=domain, measure=label, year=2022, pct=round(100 * t22[k22], 1), n=n22))
        recs.append(dict(domain=domain, measure=label, year=2025, pct=round(100 * t25[k25], 1), n=n25))
# total creative participation (2022 Table 6 'Total...', 2025 Table 4 'Selected')
t22, n22 = table("NAPS-2022-Data-Tables.xlsx", "Table 6")
t25, n25 = table(N25, "Table 4")
recs.append(dict(domain="Created art themselves", measure="Any creative activity", year=2022,
                 pct=round(100 * t22["Total creative participation"], 1), n=n22))
recs.append(dict(domain="Created art themselves", measure="Any creative activity", year=2025,
                 pct=round(100 * t25["Selected"], 1), n=n25))
naps = pd.DataFrame(recs)
naps.to_csv(f"{OUT}/naps_2022_vs_2025.csv", index=False)

# ---------------- NAPS live attendance by age, 2022 vs 2025 ----------------
def by_age(fn, sheet, rowlabel, year):
    t = rows(fn, sheet)
    hdr = next(r for r in t if r[0] and str(r[0]).strip() == "Column %")
    row = next(r for r in t if r[0] and str(r[0]).strip() == rowlabel)
    out = []
    for i, h in enumerate(hdr):
        lab = re.sub(r"\s+", "", str(h or "")).replace("–", "-")
        if re.match(r"^\d{2}-\d{2}$|^65\+$", lab):
            out.append(dict(year=year, age_group=lab, pct=round(100 * row[i], 1)))
    return out
age = pd.DataFrame(by_age("NAPS-2022-Data-Tables.xlsx", "Table 1", "Total", 2022) +
                   by_age(N25, "Table 1", "Attend Live", 2025))
age.to_csv(f"{OUT}/naps_live_attendance_by_age.csv", index=False)

# ---------------- NAPS 2025 by state ----------------
STATES = {"NSW": "New South Wales", "VIC": "Victoria", "QLD": "Queensland", "SA": "South Australia",
          "WA": "Western Australia", "TAS": "Tasmania", "NT": "Northern Territory", "ACT": "Australian Capital Territory"}
MEAS = [("Table 1", "Attend Live", "Any live arts event or festival"),
        ("Table 1", "Attend music", "Music"), ("Table 1", "Attend festivals", "Festivals"),
        ("Table 1", "Attend visual arts", "Visual arts and craft"), ("Table 1", "Attend theatre", "Theatre"),
        ("Table 1", "Attend First Nations arts or festivals", "First Nations arts or festivals"),
        ("Table 1", "Attend dance", "Dance"), ("Table 1", "Attend literary events", "Literary events"),
        ("Table 3", "AT LEAST ONE EVENT", "Arts of own cultural background"),
        ("Table 4", "Selected", "Created art themselves")]
st = []
for ab, name in STATES.items():
    fn = f"NAPS_2025_Tables_{ab}.xlsx"
    cache = {}
    for sheet, key, label in MEAS:
        if sheet not in cache:
            cache[sheet] = table(fn, sheet)
        t, n = cache[sheet]
        st.append(dict(state=name, state_abbr=ab, measure=label, pct=round(100 * t[key], 1), sample_n=n))
pd.DataFrame(st).to_csv(f"{OUT}/naps_2025_by_state.csv", index=False)

# ---------------- ABS attendance by state, 2017-18 vs 2021-22 ----------------
ABBR = {"NSW": "New South Wales", "Vic.": "Victoria", "Qld": "Queensland", "SA": "South Australia",
        "WA": "Western Australia", "Tas.": "Tasmania", "NT": "Northern Territory", "ACT": "Australian Capital Territory"}
SHORT = {v: k for k, v in {"NSW": "New South Wales", "VIC": "Victoria", "QLD": "Queensland", "SA": "South Australia",
         "WA": "Western Australia", "TAS": "Tasmania", "NT": "Northern Territory", "ACT": "Australian Capital Territory"}.items()}
CANON = {"libraries or archives": "Libraries and archives", "libraries and archives": "Libraries and archives",
         "art galleries": "Art galleries", "museums": "Museums",
         "cinemas": "Cinemas", "cinemas and drive-ins": "Cinemas",
         "live music concerts or performances": "Live music", "live music concerts and performances": "Live music",
         "musicals or operas": "Musicals and operas", "musicals and operas": "Musicals and operas",
         "theatre performances": "Theatre", "dance performances": "Dance", "other performing arts": "Other performing arts",
         "total attending at least one performing arts event": "Any performing arts event",
         "total attending at least one venue or event": "Any venue or event"}

def block(grid, start_label, stop_labels):
    """Rows after the section header `start_label` until a row whose first/second cell is in stop_labels."""
    out, on = [], False
    for r in grid:
        cells = [str(c).strip() if c is not None else "" for c in r]
        joined = " ".join(cells)
        if start_label in joined:
            on = True
            continue
        if on and any(s in joined for s in stop_labels):
            break
        if on:
            out.append(r)
    return out

recs = []
# 2021-22, ABS Table 14
g = rows("cultural_and_creative_activities_202122_tables_14_to_21.xlsx", "Table 14")
hdr = next(r for r in g if r[1] == "NSW")
cols = {i: ABBR[h] for i, h in enumerate(hdr) if h in ABBR}
for kind, start, stops in [("people_000", "ESTIMATE ('000)", ["ATTENDANCE RATE"]),
                           ("rate_pct", "ATTENDANCE RATE (%)", ["RSE OF ESTIMATE"]),
                           ("moe95", "95% MARGIN OF ERROR", ["Commonwealth"])]:
    for r in block(g, start, stops):
        key = str(r[0] or "").strip().lower()
        if key in CANON:
            for i, s in cols.items():
                recs.append(dict(period="2021-22", venue=CANON[key], state=s, kind=kind, value=r[i]))
# 2017-18, ABS 4114.0 Table 1
sh = xlrd.open_workbook(os.path.join(RAW, "Attendance_at_selected_cultural_venues_and_events_Australia_2017-18.xls")).sheet_by_name("Table 1")
g = [sh.row_values(i) for i in range(sh.nrows)]
hdr = next(r for r in g if r[1] == "NSW")
cols = {i: ABBR[h] for i, h in enumerate(hdr) if h in ABBR}
for kind, start, stops in [("people_000", "ESTIMATES ('000)", ["ATTENDANCE RATE"]),
                           ("rate_pct", "ATTENDANCE RATE (%)", ["Footnotes", "Commonwealth"])]:
    for r in block(g, start, stops):
        key = str(r[0] or "").strip().lower()
        if key in CANON:
            for i, s in cols.items():
                recs.append(dict(period="2017-18", venue=CANON[key], state=s, kind=kind, value=r[i]))
a = pd.DataFrame(recs).pivot_table(index=["state", "venue", "period"], columns="kind", values="value", aggfunc="first").reset_index()
a.insert(1, "state_abbr", a.state.map(SHORT))
a = a[["state", "state_abbr", "venue", "period", "rate_pct", "people_000", "moe95"]]
a.to_csv(f"{OUT}/attendance_by_state_2017_vs_2021.csv", index=False)

# wide summary for the map: change in 'any venue or event'
w = a[a.venue == "Any venue or event"].pivot(index=["state", "state_abbr"], columns="period", values="rate_pct").reset_index()
w.columns.name = None
w = w.rename(columns={"2017-18": "rate_2017_18", "2021-22": "rate_2021_22"})
w["change_pts"] = (w.rate_2021_22 - w.rate_2017_18).round(1)
w.to_csv(f"{OUT}/attendance_change_by_state.csv", index=False)

print(naps.pivot_table(index=["domain", "measure"], columns="year", values="pct").to_string())
print(age.pivot(index="age_group", columns="year", values="pct").to_string())
print(w.to_string(index=False))
