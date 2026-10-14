"""ABS Indigenous language statistics 2021 + Historical Population (size) -> small CSVs.

Usage:  python prepare_languages_population.py raw/Language_speakers.xlsx raw/population_size_and_growth.xlsx data
Needs:  pip install pandas openpyxl

Sources:
  Language Statistics for Aboriginal and Torres Strait Islander Peoples, 2021 (ABS, released 25 Oct 2022)
    Table 1.1  Language used at home, Aboriginal and Torres Strait Islander people, Census 1991-2021
    Table 1.3.4 Each Indigenous language by age group of users, Census 2021
    Table 1.4  Users of an Indigenous language by age, Census 2006-2021
    Table 1.5  Language used at home by state/territory, Census 2006-2021
  Historical Population, 2021 (ABS), Population size and growth, Table 1 (31 December each year)

Language counting rule: every language in the ABS classification except the 'nfd' (not further
defined) rows. With this rule the 2021 data reproduces the ABS's published figures: 167 languages
used at home, 19 of them by more than 1,000 people, and 78 with no users aged 0-14
(50 of those 78 had no recorded users of any age).
ABS randomly adjusts small cells for confidentiality, so very small counts (e.g. 0-5) are approximate.
"""
import sys, re
import openpyxl
import pandas as pd

LANG, POP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

def sheet(path, name):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    return [list(r) for r in wb[name].iter_rows(values_only=True)]

def num(x):
    return x if isinstance(x, (int, float)) else None

STATES = ["New South Wales", "Victoria", "Queensland", "South Australia", "Western Australia",
          "Tasmania", "Northern Territory", "Australian Capital Territory"]

# ---- Table 1.1: language used at home, 1991-2021 ----
t = sheet(LANG, "1.1 Census 1991-2021")
yr_row = next(r for r in t if r[1] == 1991 or str(r[1]).startswith("1991"))
years = {i: int(str(c)[:4]) for i, c in enumerate(yr_row) if c and re.match(r"\d{4}", str(c))}
count_start = next(i for i, r in enumerate(t) if r[1] == "COUNT")
out = []
for r in t[count_start + 1:]:
    if r[0] is None or r[0] == "Total" or r[1] == "PROPORTION (%)":
        break
    for i, y in years.items():
        out.append(dict(year=y, language_used_at_home=r[0].strip(), people=num(r[i])))
d = pd.DataFrame(out)
tot = d.groupby("year").people.sum()
d["pct"] = (100 * d.people / d.year.map(tot)).round(1)
d.to_csv(f"{OUT}/indigenous_language_at_home_1991_2021.csv", index=False)

# ---- Table 1.3.4: each language by age, 2021 ----
t = sheet(LANG, "1.3.4 Census 2021")
hdr = next(r for r in t if r[1] and "Children" in str(r[1]))
cols = {"children_0_14": 1, "young_adults_15_24": 2, "adults_25_44": 3, "adults_45_64": 4, "adults_65_plus": 5, "total_users": 6}
assert "Total" in str(hdr[6])
rows = []
for r in t:
    if not r[0] or num(r[1]) is None:
        continue
    name = str(r[0]).strip()
    if name.upper().startswith("TOTAL") or "nfd" in name:
        continue
    rec = {"language": name, **{k: int(r[i]) for k, i in cols.items()}}
    rec["status_2021"] = ("No users recorded" if rec["total_users"] == 0 else
                          "Used by adults only" if rec["children_0_14"] == 0 else "Used by children")
    u = rec["total_users"]
    rec["users_band"] = ("None" if u == 0 else "Under 10" if u < 10 else "10-99" if u < 100 else
                         "100-999" if u < 1000 else "1,000 or more")
    rows.append(rec)
langs = pd.DataFrame(rows)
order = {"Used by children": 0, "Used by adults only": 1, "No users recorded": 2}
langs = langs.sort_values(["status_2021", "total_users"], key=lambda s: s.map(order) if s.name == "status_2021" else -s)
langs.insert(0, "rank", range(1, len(langs) + 1))
langs.to_csv(f"{OUT}/indigenous_languages_2021.csv", index=False)

# ---- Table 1.4: users by age group, 2006-2021 ----
t = sheet(LANG, "1.4 Census 2006-2021")
yr_row = next(r for r in t if r[1] == 2006 or str(r[1]).startswith("2006"))
years = {i: int(str(c)[:4]) for i, c in enumerate(yr_row) if c and re.match(r"\d{4}", str(c))}
sections = {"COUNT": "users", "PROPORTION OF AGE GROUP (%)": "pct_of_age_group_using"}
cur, recs = None, {}
for r in t:
    if r[1] in sections:
        cur = sections[r[1]]
        continue
    if r[1] and str(r[1]).startswith("AGE DISTRIBUTION"):
        cur = None
    if cur and r[0] and "years" in str(r[0]) and "Median" not in str(r[0]):
        for i, y in years.items():
            recs.setdefault((y, r[0].strip()), {})[cur] = num(r[i])
age = pd.DataFrame([dict(year=y, age_group=a, **v) for (y, a), v in recs.items()])
age.to_csv(f"{OUT}/indigenous_language_users_by_age_2006_2021.csv", index=False)

# ---- Table 1.5: by state, 2006-2021 ----
t = sheet(LANG, "1.5 Census 2006-2021")
yr_row, st_row = t[5], t[6]
cur_year, colmap = None, {}
for i in range(1, len(st_row)):
    if yr_row[i] and re.match(r"\d{4}", str(yr_row[i])):
        cur_year = int(str(yr_row[i])[:4])
    s = re.sub(r"\(.*?\)", "", str(st_row[i] or "")).strip()
    if s in STATES:
        colmap[i] = (cur_year, s)
get = lambda label: next(r for r in t if r[0] and str(r[0]).strip() == label)
lang_row, total_row = get("Australian Indigenous language"), get("Total")
st = pd.DataFrame([dict(year=y, state=s, users=lang_row[i], indigenous_population=total_row[i],
                        pct_using=round(100 * lang_row[i] / total_row[i], 1)) for i, (y, s) in colmap.items()])
st.to_csv(f"{OUT}/indigenous_language_by_state_2006_2021.csv", index=False)

# ---- Population, 31 December, 1901-2020 ----
t = sheet(POP, "Table 1")
hdr = next(r for r in t if r[0] == "Sex")
yearcols = {i: int(c) for i, c in enumerate(hdr) if isinstance(c, int) and c >= 1901}
abbr = {"NSW": "New South Wales", "Vic.": "Victoria", "Qld": "Queensland", "SA": "South Australia",
        "WA": "Western Australia", "Tas.": "Tasmania", "NT": "Northern Territory", "ACT": "Australian Capital Territory",
        "Australia": "Australia"}
pop = []
for r in t:
    if r[0] == "Person" and r[1]:
        area = abbr.get(re.sub(r"\(.*?\)", "", r[1]).strip())
        for i, y in yearcols.items():
            if num(r[i]) is not None:
                pop.append(dict(year=y, area=area, population=int(r[i])))
pd.DataFrame(pop).to_csv(f"{OUT}/population_1901_2020.csv", index=False)

print(d[d.language_used_at_home == "Australian Indigenous language"][["year", "people", "pct"]].to_string(index=False))
print(langs.status_2021.value_counts().to_dict(), "| used:", (langs.total_users > 0).sum(),
      "| >1000 users:", (langs.total_users > 1000).sum())
