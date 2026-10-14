"""Turn the two Cultural Data Online workbooks into small, long-format CSVs.

Usage:
  python prepare_funding_attendance.py <cultural-funding-by-government-2023-24-australia.xlsx> \
                                       <cultural-data-by-state-and-territory-2025-australia.xlsx> <out_dir>

Sources (arts.gov.au, Cultural Data Online):
  - Cultural Funding by Government 2023-24 (Tables 2, 6, 15, 16)
  - Cultural data by state and territory 2025 (Tables 6.2 and 7.2, from ABS Cultural and creative activities 2021-22)
Rows are located by their label text, never by hard-coded row numbers.
"""
import sys, re
import openpyxl
import pandas as pd

FUND, STATE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

def rows(path, sheet):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
    return [list(r) for r in ws.iter_rows(values_only=True)]

def clean(s):
    return re.sub(r"\(.*?\)", "", str(s)).replace("–", "-").strip() if s is not None else ""

def year_end(label):  # "2023-24" -> 2024
    a, b = clean(label).split("-")[:2]
    return int(a[:2] + b[-2:])

STATES = ["New South Wales", "Victoria", "Queensland", "South Australia", "Western Australia",
          "Tasmania", "Northern Territory", "Australian Capital Territory"]
ABBR = dict(zip(STATES, ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]))

# ---------- Table 2: expenditure by level of government and category, all years ----------
t2 = rows(FUND, "Table_2")
hdr = next(r for r in t2 if any(clean(c).startswith("2015-16") for c in r if c))
year_cols = {i: clean(c) for i, c in enumerate(hdr) if c and re.match(r"\d{4}-\d{2}", clean(c))}
LEVELS = {"Australian Government": "Australian Government",
          "State and territory government": "State and territory government",
          "Local government": "Local government"}
level = domain = None
cat_rows, total_rows = [], []
for r in t2:
    label = clean(r[0])
    if label in LEVELS and all(v is None for v in r[1:4]):
        level, domain = LEVELS[label], None
        continue
    if label in ("Heritage", "Arts"):
        domain = label
        continue
    if not level or not label:
        continue
    for i, yr in year_cols.items():
        v = r[i]
        if not isinstance(v, (int, float)):
            continue
        rec = dict(year=yr, year_end=year_end(yr), level=level, amount_m=round(float(v), 1))
        if label.startswith("Total ") and label.lower().startswith("total " + level.split()[0].lower()):
            total_rows.append(rec)
        elif label.startswith("Total"):
            continue  # Total Heritage / Total Arts subtotals: derivable, so skipped
        elif domain:
            cat_rows.append(dict(rec, domain=domain, category=label))
    if label == "Total":
        break

lvl = pd.DataFrame(total_rows).drop_duplicates()
lvl.to_csv(f"{OUT}/funding_by_level.csv", index=False)

cat = pd.DataFrame(cat_rows)[["year", "year_end", "level", "domain", "category", "amount_m"]]
cat.to_csv(f"{OUT}/funding_by_category.csv", index=False)

# ---------- Table 6 (state govt) + Table 15 (local govt), 2023-24, per person by state ----------
t6 = rows(FUND, "Table_6")
h6 = next(r for r in t6 if r[1] and "Recurrent" in str(r[1]))
c_tot = next(i for i, c in enumerate(h6) if c and clean(c) == "Total")
c_pp = next(i for i, c in enumerate(h6) if c and "per person" in str(c))
st = {clean(r[0]): (r[c_tot], r[c_pp]) for r in t6 if clean(r[0]) in STATES}

t15 = rows(FUND, "Table_15")
yrow = next(r for r in t15 if any(clean(c).startswith("2015-16") for c in r if c))
mrow = t15[t15.index(yrow) + 1]
start = next(i for i, c in enumerate(yrow) if c and clean(c).startswith("2023-24"))
nxt = [i for i, c in enumerate(yrow) if c and i > start]
end = nxt[0] if nxt else len(yrow)
lc_tot = next(i for i in range(start, end) if mrow[i] and clean(mrow[i]) == "Total")
lc_pp = next(i for i in range(start, end) if mrow[i] and "per person" in str(mrow[i]))
loc = {clean(r[0]): (r[lc_tot], r[lc_pp]) for r in t15 if clean(r[0]) in STATES}

t16 = rows(FUND, "Table_16")
pop = {clean(r[0]): r[1] for r in t16 if clean(r[0]) in STATES}

out = []
for s in STATES:
    sg_m, sg_pp = st[s]
    lg_m, lg_pp = loc.get(s, (None, None))
    out.append(dict(state=s, state_abbr=ABBR[s], population_dec2023=pop[s],
                    state_govt_m=round(sg_m, 1), state_govt_pp=round(sg_pp, 2),
                    local_govt_m=None if lg_m is None else round(lg_m, 1),
                    local_govt_pp=None if lg_pp is None else round(lg_pp, 2),
                    state_plus_local_pp=round(sg_pp + (lg_pp or 0), 2),
                    note="ACT has no local government; ACT Government funds local services such as libraries" if s == "Australian Capital Territory" else ""))
pd.DataFrame(out).to_csv(f"{OUT}/funding_by_state_2023_24.csv", index=False)

# ---------- Tables 7.2 (adults) and 6.2 (children): attendance 2017-18 vs 2021-22 ----------
CANON = {"libraries or archives": "Libraries and archives", "libraries and archives": "Libraries and archives",
         "art galleries": "Art galleries", "museums": "Museums", "cinemas": "Cinemas",
         "live music concerts or performances": "Live music", "live music concerts and performances": "Live music",
         "musicals or operas": "Musicals and operas", "musicals and operas": "Musicals and operas",
         "theatre performances": "Theatre", "dance performances": "Dance",
         "other performing arts": "Other performing arts",
         "total attending at least one performing arts event": "Any performing arts event",
         "total attending at least one venue or event": "Any venue or event"}
GROUP = {"Libraries and archives": "Venue", "Art galleries": "Venue", "Museums": "Venue", "Cinemas": "Venue",
         "Any performing arts event": "Total", "Any venue or event": "Total"}

def attendance(sheet, audience):
    t = rows(STATE, sheet)
    yr = next(r for r in t if r[1] and "2017" in str(r[1]))
    meas = t[t.index(yr) + 1]
    # find the ATTENDANCE RATE and ESTIMATES columns for each year
    cols = {}
    cur_year = None
    year_at = {i: clean(c) for i, c in enumerate(yr) if c}
    for i, m in enumerate(meas):
        if i in year_at:
            cur_year = year_at[i]
        if m and "ATTENDANCE RATE" in str(m) and "RSE" not in str(m):
            if cur_year and cur_year not in [k[0] for k in cols if k[1] == "rate"]:
                cols[(cur_year, "rate")] = i
        if m and "ESTIMATES" in str(m) and "RSE" not in str(m):
            if cur_year and cur_year not in [k[0] for k in cols if k[1] == "est"]:
                cols[(cur_year, "est")] = i
    # Children's table lays years side by side inside each measure block
    if len(cols) < 4:
        cols = {}
        blocks = [i for i, m in enumerate(meas) if m]
        for b in blocks:
            name = str(meas[b])
            if "RSE" in name:
                continue
            kind = "rate" if "RATE" in name else "est"
            for j in (b, b + 1):
                cols[(clean(yr[j]), kind)] = j
    recs = []
    for r in t:
        key = clean(r[0]).lower()
        if key in CANON:
            v = CANON[key]
            for period in ("2017-18", "2021-22"):
                recs.append(dict(audience=audience, venue=v, group=GROUP.get(v, "Performing arts"), period=period,
                                 rate_pct=r[cols[(period, "rate")]], people_000=r[cols[(period, "est")]]))
    return recs

att = pd.DataFrame(attendance("7.2 Cultural Attendance", "Adults (15+)") +
                   attendance("6.2 Cultural Attendance", "Children (5-14)"))
att.to_csv(f"{OUT}/attendance_2017_vs_2021.csv", index=False)
print("wrote funding_by_level, funding_by_category, funding_by_state_2023_24, attendance_2017_vs_2021")
