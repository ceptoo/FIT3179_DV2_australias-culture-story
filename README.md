# Australia's Culture Story

A narrative data visualisation of how Australia's culture has changed: Indigenous languages, national heritage, migration, arts participation, libraries, live performance and government cultural funding.

**Author:** Wern Zhong Lei
**Unit:** FIT3179 Data Visualisation 2, Monash University, October 2026
**Live page:** served by GitHub Pages from this repository's root (`index.html`)

## Structure

| Path | Contents |
|---|---|
| `index.html` | The single-page story |
| `css/style.css` | Layout (12-column grid) and typography |
| `js/main.js` | Embeds every chart with vega-embed |
| `js/charts/*.vg.json` | One Vega-Lite (or Vega, for the treemap) specification per chart |
| `data/` | The prepared CSV and TopoJSON files the charts load (about 270 KB); see `data/README.md` for sources and processing |
| `sketch.pdf` | The hand-drawn design sketch |

## Charts

| # | Chart | Idiom |
|---|---|---|
| 01 | Indigenous languages | Dot map with state filter |
| 02 | Languages passed to children | Waffle chart |
| 02b | Speakers vs share | Connected scatterplot |
| 03 | National Heritage places | Dot map over World Heritage areas, with type filter |
| 04 | Listings per year | Stacked bar chart |
| 05 | Birthplaces 1901–2021 | Heatmap |
| 06 | Born overseas | Line chart |
| 07a | Arts participation 2022 vs 2025 | Dumbbell chart with dropdown |
| 07b | Attendance by age | Slope chart |
| 08 | Venue attendance before and during COVID | Dumbbell chart |
| 08b | Fall in attendance by state | Choropleth map |
| 09a | Library loans | Stacked bar chart |
| 09b | Library loans, visits and spending | Indexed line chart |
| 10 | Live performance tickets | Streamgraph |
| 11 | Tickets by state | Proportional symbol map |
| 13 | Cultural spending per person | Choropleth map |
| 14 | Where funding went | Treemap |

## Data sources

AIATSIS (AUSTLANG); ABS (Language Statistics for Aboriginal and Torres Strait Islander Peoples 2021, Historical Population 2021, Cultural and creative activities 2021–22, ASGS boundaries); DCCEEW (National Heritage List, World Heritage Areas); Office for the Arts (Cultural data by state and territory 2025, Cultural Funding by Government 2023–24); Creative Australia (National Arts Participation Survey 2022 and 2025); NSLA and ALIA (Australian Public Libraries Statistical Report 2023–24); Live Performance Australia (2024 Attendance and Revenue Report). Full links are in the page footer.

## AI acknowledgement

Claude (Anthropic) assisted with finding datasets, preparing data files, drafting chart specifications and editing text. All data, charts and text were checked by the author.
