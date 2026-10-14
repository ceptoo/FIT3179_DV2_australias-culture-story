"""ABS Historical Population 2021, Country of birth datacube -> overseas-born share and a
country heatmap, 1901-2021.

Usage:  python prepare_birthplace.py raw/country_of_birth.xlsx data
Needs:  pip install pandas openpyxl

Years and sources inside the workbook:
  1901-1996  Census counts (Tables 7-20). Totals include 'At sea' / 'Not stated', which have no
             row of their own, so shares use (Australian-born + overseas-born) as the denominator.
  2001-2021  Estimated resident population (Tables 22-30), five-yearly to match census years.
Australian-born = the 'Commonwealth of Australia' / 'Australia' subtotal row (its state-of-birth
breakdown rows are skipped). Overseas-born = all other country rows (2001+: the published
'Total overseas-born' row). External territories (Norfolk, Christmas, Cocos Is.) count as neither,
following the ABS's 2001+ convention. Shares = overseas / (Australian-born + overseas-born).
"""
import sys, re
import openpyxl
import pandas as pd

SRC, OUT = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)

TABLES = {7: 1901, 8: 1911, 9: 1921, 10: 1933, 11: 1947, 12: 1954, 13: 1961, 14: 1966, 15: 1971,
          16: 1976, 17: 1981, 18: 1986, 19: 1991, 20: 1996, 22: 2001, 24: 2006, 26: 2011, 28: 2016, 30: 2021}

# Australian-born subtotal row: 'Commonwealth of Australia' (1901-47) or 'Australia' (1954 on).
AUS_TOTAL = re.compile(r"^(commonwealth of australia|australia)$", re.I)
# Rows that make up that subtotal (birth state, 'Australia undefined') - skipped to avoid double counting.
AUS_PARTS = re.compile(r"^(australia( \(undefined\)| - undefined)|new south wales|victoria|queensland|south australia|"
                       r"western australia|tasmania|northern territory|australian capital territory|"
                       r"federal(ion)? capital territory)$", re.I)
# Australian external territories: ABS counts these as neither Australian- nor overseas-born.
EXT = re.compile(r"^(norfolk island.*|christmas island|cocos \(keeling\) islands?|aust e t, nec|australian a t)$", re.I)

# Country groups for the heatmap. Each regex is matched against the full row label.
GROUPS = {
    "UK & Ireland": r"^(england.*|scotland|wales|ireland.*|n('|or)thern ireland|channel islands|isle of man|"
                    r"uk and ireland, nfd|united kingdom and ireland, nfd|republic of ireland.*)$",
    "New Zealand": r"^new zealand$",
    "Italy": r"^italy$",
    "Greece": r"^greece$",
    "Germany": r"^germany.*$",
    "Netherlands": r"^netherlands$",
    "China": r"^china( \(excl.*\))?$",
    "India": r"^(british india( and ceylon)?|india)$",
    "Vietnam": r"^vie?t ?nam$",
    "Philippines": r"^philippine(s| is\.| islands)$",
}
GROUPS = {k: re.compile(v, re.I) for k, v in GROUPS.items()}

def lab(x):
    return re.sub(r"\((?:[a-z])\)$", "", str(x)).strip()  # drop footnote markers like (e)

summary, groups = [], []
for t, year in TABLES.items():
    rows = [list(r) for r in wb[f"Table {t}"].iter_rows(values_only=True)]
    hi = next(i for i, r in enumerate(rows) if r[0] and "Place of Birth" in str(r[0]))
    meas = rows[hi]
    pcol = max(i for i, m in enumerate(meas) if m and str(m).strip() == "Person")  # national 'Person' column
    aus = over = total = 0
    published_over = None
    gsum = {g: None for g in GROUPS}
    for r in rows[hi + 1:]:
        if not r[0]:
            continue
        name = lab(r[0])
        v = r[pcol] if pcol < len(r) else None
        if not isinstance(v, (int, float)):
            continue
        low = name.lower()
        if low.startswith("total overseas"):
            published_over = v
            continue
        if low.startswith("total"):
            total = v
            break
        if AUS_TOTAL.match(name):
            aus = v
        elif AUS_PARTS.match(name) or EXT.match(name):
            continue
        else:
            over += v
            for g, rx in GROUPS.items():
                if rx.match(name):
                    gsum[g] = (gsum[g] or 0) + v
    if published_over is not None:   # 2001+: use the ABS's own overseas-born total
        over = published_over
    stated = aus + over
    summary.append(dict(year=year, source="Census count" if year <= 1996 else "Estimated resident population",
                        australian_born=round(aus), overseas_born=round(over), not_stated_at_sea_or_ext_territories=round(total - stated),
                        total=round(total), overseas_pct=round(100 * over / stated, 1)))
    for g, v in gsum.items():
        groups.append(dict(year=year, country=g, people=None if v is None else round(v),
                           pct_of_population=None if v is None else round(100 * v / stated, 2)))

s = pd.DataFrame(summary)
s.to_csv(f"{OUT}/overseas_born_1901_2021.csv", index=False)
g = pd.DataFrame(groups)
g.to_csv(f"{OUT}/birthplace_heatmap_1901_2021.csv", index=False)
print(s.to_string(index=False))
print(g.pivot(index="country", columns="year", values="pct_of_population").to_string())
