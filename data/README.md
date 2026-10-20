# Australia's Culture Story — data

The data files behind *Australia's Culture Story*. Every chart in `js/charts/` loads its data from here.
Each file below lists its source, how it was prepared and the caveats shown on the page.

## Files

### Basemap — ABS ASGS Edition 4 (2026), CC BY-SA 4.0
| File | Contents |
|---|---|
| `aus_states.topojson` | 8 states/territories (38 KB). Layer `states`; fields `state_code`, `state_name`, `state_abbr` |
| `state_centroids.csv` | One point inside each state (`lon`, `lat`), for proportional symbols |

```json
"data": { "url": "data/aus_states.topojson", "format": { "type": "topojson", "feature": "states" } },
"projection": { "type": "conicEqualArea", "parallels": [-18, -36], "rotate": [-132, 0] }
```

### Indigenous languages — AIATSIS AUSTLANG, CC BY 4.0
| File | Contents |
|---|---|
| `austlang.csv` | 834 language varieties: `code`, `name`, `state`, `lat`, `lon` |

Processing: 1,204 records in. 369 had no location (coded 0,0) and were dropped, plus 1 entry marked "(retired)". State assigned from the ABS boundaries; 29 island/coastal points (e.g. Torres Strait) took the nearest state, all within 15 km.
**Say in your write-up:** locations are approximate centres, not boundaries, and the map shows the 834 languages with a recorded location.

### Heritage — DCCEEW National Heritage List and World Heritage Areas
| File | Contents |
|---|---|
| `nhl_places.csv` | 133 map points for the 126 places on the National Heritage List: `place_id`, `name`, `class` (Historic 70 / Natural 36 / Indigenous 20 places), `state`, `year` listed (2004–2026), `area_ha`, `on_main_map`, `lon`, `lat`, `url` |
| `nhl_by_year.csv` | Places listed per year and class, each place counted once: `year`, `class`, `places` |
| `world_heritage_sites.csv` | 21 World Heritage properties: `name`, `type` (Natural / Cultural / Mixed), `first_inscribed` (1981–2025), `all_inscriptions`, `states`, `parts`, `hectares`, `on_main_map`, `lon`, `lat` |
| `world_heritage.topojson` | Outlines of the 18 properties inside the mainland frame. Layer `world_heritage` |

Processing: NHL keeps "Listed place" only (14 nominations and 3 sub-parts dropped). A few places span several states or islands (e.g. Australian Alps, Gondwana Rainforests), so they have more than one point but are counted once. World Heritage keeps declared properties and drops buffer zones; multi-part listings (e.g. the 11 Convict Sites) are merged. Type comes from the listing's own criteria fields.
**`on_main_map`:** `false` for places outside the mainland frame (external territories, Macquarie Island, Lord Howe Island). Filter them out of maps with `{"filter": "datum.on_main_map"}` but keep them in counts and timelines.

### Government cultural funding — Cultural Funding by Government 2023–24 (arts.gov.au)
| File | Contents |
|---|---|
| `funding_by_level.csv` | Total by level of government: `year` (2015–16 … 2023–24), `year_end`, `level`, `amount_m` ($ million, not inflation-adjusted) |
| `funding_by_category.csv` | Same, by `domain` (Heritage / Arts) and `category` (e.g. Libraries, Art museums, Music), Australian and state/territory governments. Local government is reported as a total only |
| `funding_by_state_2023_24.csv` | Per state: `state_govt_m`, `state_govt_pp`, `local_govt_m`, `local_govt_pp`, `state_plus_local_pp` (dollars per person), `population_dec2023` |

**Caveats to state on the page:**
- There's no data for 2018–19 or 2022–23, because the survey moved to every second year. Use `year_end` as a quantitative axis so the gaps show honestly.
- 2019–20 to 2021–22 include COVID support funding.
- Australian Government spending isn't split by state, so the per-person map covers state plus local government only.
- The ACT has no local government; its territory government covers that role.

### Attendance — ABS Cultural and creative activities 2021–22 (via Cultural data by state and territory 2025, Tables 6.2 and 7.2)
| File | Contents |
|---|---|
| `attendance_2017_vs_2021.csv` | `audience` (Adults 15+ / Children 5–14), `venue`, `group` (Venue / Performing arts / Total), `period` (2017-18 / 2021-22), `rate_pct`, `people_000` |

**Caveat:** the 2021–22 survey ran July 2020–June 2022, so COVID restrictions affected attendance. Annotate this on the dumbbell chart.

### Who we became — ABS Historical Population 2021, Country of birth
| File | Contents |
|---|---|
| `overseas_born_1901_2021.csv` | 19 census years: `year`, `source`, `australian_born`, `overseas_born`, `overseas_pct` (22.7% in 1901, 9.8% low in 1947, 29.3% in 2021) |
| `birthplace_heatmap_1901_2021.csv` | `year`, `country`, `people`, `pct_of_population` for 10 birthplaces: UK & Ireland, New Zealand, Italy, Greece, Germany, Netherlands, China, India, Vietnam, Philippines |

Processing: Australian-born = the "Commonwealth of Australia"/"Australia" subtotal (its state-of-birth breakdown is skipped so nobody is counted twice). 1901–1996 are census counts; 2001–2021 are estimated resident population, using the ABS's published overseas-born total. Shares exclude "not stated", "at sea" and Australia's external territories, matching the ABS's published 23% (1901) and 29% (2021).
**Country groups, to state in a footnote:** UK & Ireland are combined (Ireland was in the UK until 1922 and the tables split it inconsistently). India before 1954 is "British India" (today's India, Pakistan and Bangladesh); 1947 includes Ceylon. China excludes Hong Kong and Taiwan. Vietnam is blank before 1976 because it isn't listed separately — use blank, not zero.

### First cultures — ABS Language Statistics for Aboriginal and Torres Strait Islander Peoples 2021
| File | Contents |
|---|---|
| `indigenous_languages_2021.csv` | All 217 Indigenous languages in the ABS classification: `rank`, `language`, users by age group, `total_users`, `status_2021` (Used by children 139 / Used by adults only 28 / No users recorded 50), `users_band`. Sorted for a waffle chart |
| `indigenous_language_at_home_1991_2021.csv` | Language Aboriginal and Torres Strait Islander people use at home: `year`, `language_used_at_home`, `people`, `pct` (Indigenous language: 43,499 = 16.4% in 1991 → 76,978 = 9.5% in 2021) |
| `indigenous_language_users_by_age_2006_2021.csv` | `year`, `age_group`, `users`, `pct_of_age_group_using` |
| `indigenous_language_by_state_2006_2021.csv` | `year`, `state`, `users`, `indigenous_population`, `pct_using` (NT 58.5% in 2021, Tasmania 0.6%). Joins to the basemap on `state` for a choropleth |

Counting rule: every language in the ABS classification except "nfd" (not further defined) rows. This reproduces the ABS's published figures exactly: 167 languages used at home, 19 by more than 1,000 people, 78 with no users aged 0–14.
**Say on the page:** the ABS randomly adjusts small counts for privacy, so figures under about 5 are approximate. "No users recorded" means none reported in the 2021 Census at home, not that a language is gone; many are being revived. The 2021 question changed from "speak" to "use" to include sign language.

### Population — ABS Historical Population 2021, Population size
| File | Contents |
|---|---|
| `population_1901_2020.csv` | `year`, `area` (8 states + Australia), `population` at 31 December, 1901–2020. Use it for per-person rates such as cinema visits per person |

### How we take part — Creative Australia NAPS 2022 + 2025, ABS attendance by state
| File | Contents |
|---|---|
| `naps_2022_vs_2025.csv` | `domain` (Attended live arts / Created art themselves / Arts of own cultural background), `measure`, `year`, `pct`, `n`. Any live arts: 68.3% → 74.4% |
| `naps_live_attendance_by_age.csv` | Live attendance by age, 2022 vs 2025. 55–64: 56.8 → 67.7; 65+: 44.6 → 57.0; 15–24: 86.9 → 85.4 |
| `naps_2025_by_state.csv` | 10 measures × 8 states, with `sample_n` |
| `attendance_by_state_2017_vs_2021.csv` | ABS: `state`, `venue`, `period`, `rate_pct`, `people_000`, `moe95` (95% margin of error, 2021–22 only) |
| `attendance_change_by_state.csv` | Any venue or event, by state: `rate_2017_18`, `rate_2021_22`, `change_pts` (VIC −23.4 most, NT −7.4 least) |

**Caveats to state on the page:**
- NAPS (Creative Australia) and the ABS survey measure different things and use different samples, so never put their percentages on the same axis.
- NAPS 2009–2019 waves aren't in these tables, so only 2022 vs 2025 is shown. Creative Australia states 2025 is the highest live attendance since 2009; quote that as their finding.
- "Own cultural background" uses different question wording in 2022 and 2025 (27.5% → 36.0% in the tables). Creative Australia's press release quotes 32% → 40% for a broader measure, so don't mix the two.
- State NAPS samples are small (NT 172, TAS 188), so treat state differences as indicative.

### Libraries and the stage — NSLA/ALIA 2023–24 and Live Performance Australia 2024 (both PDFs)
| File | Contents |
|---|---|
| `libraries_national_2019_2024.csv` | 2019–20 to 2023–24: outlets, physical and website visits, collection items, physical and digital loans, loans per person, expenditure ($m and per person), per-person spending adjusted for inflation to 2023–24 dollars, digital share of loans (24% → 31.7%) |
| `libraries_by_state_2023_24.csv` | Per state: outlets, onsite visits, loans (total/physical/digital, millions), visits and loans per person (ABS population, Dec 2023) |
| `live_by_category_2010_2024.csv` | 12 categories × 15 years: tickets (attendance), revenue, average ticket price |
| `live_by_state_2010_2024.csv` | 8 states × 15 years: tickets, revenue, average price |
| `live_by_state_2024.csv` | 2024 per state, with tickets and revenue per resident |
| `live_by_category_state_2024.csv` | 2024 tickets and revenue, category × state |

Every table was cross-checked against the report's own totals. **Problems found in the source reports, to footnote or avoid:**
- **NSLA, SA digital loans:** printed as 3.21m, but SA total (13.23m) minus physical (7.50m) = 5.73m, and every other state's digital figure equals total minus physical. The file uses total − physical.
- **NSLA, state visits:** sum to 86.9m, vs the report's national 87.6m. The national series uses the report's national figure.
- **NSLA, NT collection items:** physical (0.27m) + digital (0.56m) ≠ total (0.33m). Not used.
- **NSLA, per-person rates:** computed for every state from the same ABS population (Dec 2023). These match the report's published rates except Queensland: the report says 7.8 loans per person, while its own loan count gives 7.5.
- **LPA, 2010:** the 12 category tables add up to $14.1m and 183,602 tickets more than the state table. Every year 2011–2024 reconciles exactly. Start category charts at 2011, or footnote 2010.
- **LPA, Circus and Physical Theatre:** excludes Cirque du Soleil's *Luzia* in 2024 (the report's own footnote).
- **LPA vs ABS:** LPA counts tickets issued for events held in each state, so interstate visitors count where the show is. It is not a survey of residents, so don't compare it directly with ABS or NAPS attendance rates.

## Preparation scripts (kept outside this repo)
The raw downloads are 139 MB, so they and the scripts that process them are not published here. The commands were:
```
bash   scripts/prepare_basemap.sh            raw/STE_2026_AUST_GDA2020.shp data
python scripts/prepare_austlang.py           raw/AustLang.csv raw/STE_2026_AUST_GDA2020.shp data/austlang.csv
python scripts/prepare_heritage.py           raw/National_Heritage_List_Australia.geojson raw/Australia_World_Heritage_Areas.geojson data
python scripts/prepare_funding_attendance.py raw/cultural-funding-by-government-2023-24-australia.xlsx raw/cultural-data-by-state-and-territory-2025-australia.xlsx data
python scripts/prepare_birthplace.py         raw/country_of_birth.xlsx data
python scripts/prepare_languages_population.py raw/Language_speakers.xlsx raw/population_size_and_growth.xlsx data
python scripts/prepare_participation.py     raw/b3 data   # folder holding the NAPS and ABS participation workbooks
python scripts/prepare_live_libraries.py    raw/2024_LPA_Attendance_and_Revenue_Report.pdf raw/NSLA_Public_Libraries_Statistical_Report_2023_24.pdf raw/cultural-funding-by-government-2023-24-australia.xlsx data
```
Needs: `pip install pandas shapely pyshp openpyxl xlrd`, `npm i -g mapshaper`, and `pdftotext` (poppler-utils) for the PDF reports.
