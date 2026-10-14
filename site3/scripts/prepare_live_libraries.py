"""Live performance (LPA 2024 report) + public libraries (NSLA 2023-24 report) -> CSVs.

Usage:  python prepare_live_libraries.py raw/2024_LPA_Attendance_and_Revenue_Report.pdf \
                                         raw/NSLA_Public_Libraries_Statistical_Report_2023_24.pdf \
                                         raw/cultural-funding-by-government-2023-24-australia.xlsx data
Needs:  pdftotext (poppler-utils), pip install pandas openpyxl

Tables are read from the PDFs' text layer (pdftotext -layout). Every table is checked against the
report's own totals; the script stops if any check fails, so nothing is silently mis-read.
  LPA  p.27 2024 attendance & revenue by category x state
       p.29-30 revenue / attendance by state, 2010-2024
       category chapters: national revenue / attendance / ticket price by category, 2010-2024
  NSLA section 1 national five-year series (2019-20 to 2023-24); section 2 state tables 2023-24
Population for per-person rates: ABS ERP Dec 2023, from Cultural Funding by Government 2023-24 Table 16.
"""
import sys, re, subprocess
import openpyxl
import pandas as pd

LPA_PDF, NSLA_PDF, FUND, OUT = sys.argv[1:5]
text = lambda pdf: subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
num = lambda s: float(s.replace("$", "").replace(",", "").replace("*", "").replace("m", ""))
STATES8 = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]
NAMES = {"NSW": "New South Wales", "VIC": "Victoria", "QLD": "Queensland", "SA": "South Australia",
         "WA": "Western Australia", "TAS": "Tasmania", "NT": "Northern Territory", "ACT": "Australian Capital Territory"}

def check(cond, msg):
    if not cond:
        sys.exit("CHECK FAILED: " + msg)

# =============================== LPA ===============================
lpa = text(LPA_PDF).splitlines()

def section(lines, start_pat, end_pat):
    i = next(k for k, l in enumerate(lines) if re.search(start_pat, l))
    j = next(k for k in range(i + 1, len(lines)) if re.search(end_pat, lines[k]))
    return lines[i:j]

# --- state x year, 2010-2024 (revenue p.29, attendance p.30) ---
def state_years(title):
    blk = section(lpa, rf"^\s*{title} by State/Territory\s+2010 → 2024", r"Analysis")
    blk = [l for l in blk if re.match(r"^\s+20\d\d\s", l)]
    rows = []
    for l in blk:
        toks = re.findall(r"\$?[\d,]+\*{0,2}", l)
        year, vals = int(toks[0]), [num(t) for t in toks[1:]]
        check(len(vals) == 9, f"{title} {year}: expected 8 states + total, got {len(vals)}")
        check(abs(sum(vals[:8]) - vals[8]) <= 8, f"{title} {year}: states don't add to total")
        rows += [dict(year=year, state=NAMES[s], state_abbr=s, value=v) for s, v in zip(STATES8, vals[:8])]
    check(len(rows) == 15 * 8, f"{title}: expected 2010-2024")
    return pd.DataFrame(rows)

# the second occurrence of each heading is the table page (first is the chart page)
def nth_section(title, n=2):
    idx = [k for k, l in enumerate(lpa) if re.search(rf"^\s*{title} by State/Territory\s+2010 → 2024", l)]
    return idx[n - 1]
rev_i, att_i = nth_section("Revenue"), nth_section("Attendance")
def years_from(i):
    out = []
    for l in lpa[i + 1:i + 40]:
        if re.match(r"^\s+20\d\d\s", l):
            out.append(l)
        if "Analysis" in l and out:
            break
    return out
def parse_state_years(lines, title):
    rows = []
    for l in lines:
        toks = re.findall(r"\$?[\d,]+\*{0,2}", l)
        year, vals = int(toks[0]), [num(t) for t in toks[1:]]
        check(len(vals) == 9, f"{title} {year}: got {len(vals)} values")
        check(abs(sum(vals[:8]) - vals[8]) <= 8, f"{title} {year}: states don't add to total")
        rows += [dict(year=year, state=NAMES[s], state_abbr=s, **{title: v}) for s, v in zip(STATES8, vals[:8])]
    check(len(rows) == 120, f"{title}: expected 15 years x 8 states")
    return pd.DataFrame(rows)
rev = parse_state_years(years_from(rev_i), "revenue")
att = parse_state_years(years_from(att_i), "attendance")
sy = rev.merge(att, on=["year", "state", "state_abbr"])
sy["avg_ticket_price"] = (sy.revenue / sy.attendance).round(2)
sy.to_csv(f"{OUT}/live_by_state_2010_2024.csv", index=False)

# --- 2024 attendance & revenue by category x state (p.26-27) ---
def cat_state(title):
    i = next(k for k, l in enumerate(lpa) if re.search(rf"^\s*{title} by Category and State/Territory\s+2024", l))
    rows = []
    for l in lpa[i + 1:i + 30]:
        m = re.match(r"^\s*([A-Za-z'’/()\- ]+?)\s{2,}((?:\$?[\d,]+|-)(?:\s+(?:\$?[\d,]+|-)){8})\s*$", l)
        if m and m.group(1).strip() != "Category":
            vals = [0 if v == "-" else num(v) for v in m.group(2).split()]
            rows.append((m.group(1).strip(), vals))
        if "Analysis" in l:
            break
    return rows
cs = []
for title, field in [("Revenue", "revenue"), ("Attendance", "attendance")]:
    rows = cat_state(title)
    total = next(v for c, v in rows if c == "Total")
    cats = [(c, v) for c, v in rows if c != "Total"]
    check(len(cats) == 12, f"2024 {title}: expected 12 categories, got {len(cats)}")
    for k in range(9):
        check(abs(sum(v[k] for _, v in cats) - total[k]) <= 12, f"2024 {title}: column {k} doesn't add up")
    for c, v in cats:
        for s, x in zip(STATES8, v[:8]):
            cs.append(dict(category=c, state_abbr=s, field=field, value=x))
cs = pd.DataFrame(cs).pivot_table(index=["category", "state_abbr"], columns="field", values="value").reset_index()
cs.insert(2, "state", cs.state_abbr.map(NAMES))
cs.to_csv(f"{OUT}/live_by_category_state_2024.csv", index=False)
cat2024 = cs.groupby("category")[["revenue", "attendance"]].sum()

# --- national history by category, 2010-2024 ---
# Each category chapter has a 15-row table (2010-2024: revenue, growth, attendance, growth, ticket price).
# Collect every complete 2010..2024 block, then identify its category by matching its 2024
# revenue and attendance to the 2024 category table (exact, unique per category).
ROW = re.compile(r"(?<![\d$,.])(20\d\d)\s+\$([\d,]+)\*?\s+\(?[\d.]+%\)?\s+([\d,]+)\*?\s+\(?[\d.]+%\)?\s+\$([\d.]+)")
blocks, cur = [], []
for l in lpa:
    m = ROW.search(l)
    if not m:
        continue
    y = int(m.group(1))
    if y == 2010:
        cur = []
    cur.append((y, num(m.group(2)), num(m.group(3)), float(m.group(4))))
    if y == 2024 and [r[0] for r in cur] == list(range(2010, 2025)):
        blocks.append(cur)
        cur = []
hist, used = [], set()
for b in blocks:
    _, r24, a24, _ = b[-1]
    match = [c for c in cat2024.index if abs(cat2024.loc[c, "revenue"] - r24) <= 5 and abs(cat2024.loc[c, "attendance"] - a24) <= 5]  # states sum to the printed total within $5 (report rounding)
    if len(match) != 1 or match[0] in used:
        continue
    used.add(match[0])
    hist += [dict(category=match[0], year=y, revenue=r, attendance=a, avg_ticket_price=p) for y, r, a, p in b]
hist = pd.DataFrame(hist)
check(len(used) == 12, f"history: matched {len(used)} of 12 categories: {sorted(used)}")
yr = hist.groupby("year")[["revenue", "attendance"]].sum()
st_yr = sy.groupby("year")[["revenue", "attendance"]].sum()
diff = (yr - st_yr)
check((diff.loc[2011:].abs() <= 30).all().all(), "category history doesn't add to state history totals (2011-2024)")
# Known inconsistency inside the LPA report: in 2010 the 12 category tables add to more than the state table.
print(f"NOTE 2010: categories exceed state totals by ${diff.loc[2010, 'revenue']:,.0f} and {diff.loc[2010, 'attendance']:,.0f} tickets (source inconsistency)")
hist.to_csv(f"{OUT}/live_by_category_2010_2024.csv", index=False)

# --- 2024 per person, with ABS population ---
wb = openpyxl.load_workbook(FUND, read_only=True, data_only=True)
pop = {str(r[0]).strip(): r[1] for r in wb["Table_16"].iter_rows(values_only=True) if r[0] and isinstance(r[1], (int, float))}
s24 = sy[sy.year == 2024].copy()
s24["population_dec2023"] = s24.state.map(pop)
s24["attendance_per_person"] = (s24.attendance / s24.population_dec2023).round(2)
s24["revenue_per_person"] = (s24.revenue / s24.population_dec2023).round(2)
s24.drop(columns="year").to_csv(f"{OUT}/live_by_state_2024.csv", index=False)

# =============================== NSLA ===============================
ns = text(NSLA_PDF).splitlines()
YEARS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]

def nat_row(label, n=5, start=0):
    """First line at/after `label` (searching up to 3 lines down) holding n numeric values."""
    for k in range(start, len(ns)):
        if label in ns[k]:
            for j in range(k, min(k + 4, len(ns))):
                vals = re.findall(r"\$?[\d,]+(?:\.\d+)?m?", ns[j].split(label)[-1] if j == k else ns[j])
                vals = [v for v in vals if re.search(r"\d", v)]
                if len(vals) >= n:
                    return [num(v) for v in vals[-n:]], k
    sys.exit(f"NSLA: '{label}' not found")

nat = {}
for key, label in [("outlets", "Total number of library outlets"), ("physical_visits", "Library visits (physical facilities)"),
                   ("visits_per_capita", "Physical visits per capita"), ("website_visits", "Website visits  "),
                   ("collection_physical", "Physical collection items"), ("collection_digital", "Digital collection items"),
                   ("loans_physical", "Physical collection usage"), ("loans_digital", "Digital collection usage"),
                   ("loans_per_capita", "Collection usage per capita"), ("expenditure_per_capita", "Expenditure per capita  ")]:
    nat[key], _ = nat_row(label)
def money_row(anchor, n):
    k = next(i for i, l in enumerate(ns) if anchor in l)
    for j in range(k, k + 4):
        vals = re.findall(r"\$[\d,]+\.\d+m?", ns[j])
        if len(vals) >= n:
            return [num(v) for v in vals[:n]]
    sys.exit(f"NSLA: money row '{anchor}' not found")
nat["expenditure_m"] = money_row("Expenditure on public", 5)
# per-capita spending adjusted for inflation to 2023-24 dollars (2023-24 itself needs no adjustment)
nat["expenditure_per_capita_2023_24_dollars"] = money_row("adjusted for inflation to", 4) + [nat["expenditure_per_capita"][-1]]
check(nat["expenditure_m"][-1] == 1391.42, "NSLA expenditure mismatch")
lib = pd.DataFrame({"year": YEARS, **nat})
lib["year_end"] = [2020, 2021, 2022, 2023, 2024]
lib["digital_share_of_loans_pct"] = (100 * lib.loans_digital / (lib.loans_physical + lib.loans_digital)).round(1)
check(abs(lib.loans_physical.iloc[-1] + lib.loans_digital.iloc[-1] - 173956534) < 5, "NSLA loans total mismatch")
check(lib.physical_visits.iloc[0] == 84229103 and lib.physical_visits.iloc[-1] == 87577447, "NSLA visits mismatch")
lib.to_csv(f"{OUT}/libraries_national_2019_2024.csv", index=False)

# --- state table 2023-24 ---
ORDER = ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]
def state_row(label, k0=0):
    for k in range(k0, len(ns)):
        if label in ns[k]:
            for j in range(k, min(k + 4, len(ns))):
                vals = re.findall(r"[\d,]+(?:\.\d+)?m?", ns[j].replace(label, ""))
                vals = [v for v in vals if re.search(r"\d", v)]
                if len(vals) >= 9:
                    return [num(v) for v in vals[:9]]
    sys.exit(f"NSLA state: '{label}' not found")
sec2 = next(k for k, l in enumerate(ns) if "tate and territory" in l and "comparative" in ns[k + 1])
st = {"outlets": state_row("Total number of", sec2), "onsite_visits_m": state_row("Onsite visitors", sec2),
      "loans_total_m": state_row("collection", next(k for k in range(sec2, len(ns)) if ns[k].strip() == "Usage")),
      "loans_physical_m": state_row("Total physical", sec2 + 40), "loans_digital_m": state_row("Total digital", sec2 + 40)}
lst = pd.DataFrame({"state_abbr": ORDER + ["AUS"], **st})
for c in ["loans_total_m", "loans_physical_m"]:
    check(abs(lst[c].iloc[:8].sum() - lst[c].iloc[8]) < 0.06, f"NSLA state {c} doesn't add to Australia")
# Known issues in the report's state table:
#  - SA digital loans printed as 3.21m, but SA total (13.23m) - physical (7.50m) = 5.73m; every other state's
#    digital figure equals total - physical. So digital loans are derived as total - physical.
#  - State onsite visits sum to 86.88m vs the printed national 87.58m (and the national series' 87,577,447).
lst["loans_digital_m"] = (lst.loans_total_m - lst.loans_physical_m).round(2)
print(f"NOTE: state onsite visits sum to {lst.onsite_visits_m.iloc[:8].sum():.2f}m vs national {lst.onsite_visits_m.iloc[8]:.2f}m (source inconsistency)")
lst = lst.iloc[:8].copy()
lst["state_abbr"] = lst.state_abbr.replace({"TAS": "TAS", "VIC": "VIC"})
lst.insert(0, "state", lst.state_abbr.map(NAMES))
lst["population_dec2023"] = lst.state.map(pop)
lst["visits_per_person"] = (lst.onsite_visits_m * 1e6 / lst.population_dec2023).round(2)
lst["loans_per_person"] = (lst.loans_total_m * 1e6 / lst.population_dec2023).round(2)
lst.to_csv(f"{OUT}/libraries_by_state_2023_24.csv", index=False)

print(sy.groupby("year")[["revenue", "attendance"]].sum().astype(int).to_string())
print(s24[["state_abbr", "attendance", "revenue", "attendance_per_person", "revenue_per_person"]].to_string(index=False))
print(lib.to_string(index=False))
print(lst.to_string(index=False))
print("all checks passed")
