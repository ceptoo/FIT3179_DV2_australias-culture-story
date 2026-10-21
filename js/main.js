// Embeds every chart. To add a chart: put its .vg.json in js/charts/ and add one line below.
// Vega-Lite charts use "width": "container", so they fill their grid column and resize with it.
const opts = { actions: false, renderer: "svg" };

const charts = {
  "#chart-01": "js/charts/01_languages_map.vg.json",
  "#chart-02": "js/charts/02_languages_waffle.vg.json",
  "#chart-02b": "js/charts/02b_languages_connected.vg.json",
  "#chart-03": "js/charts/03_heritage_map.vg.json",
  "#chart-04": "js/charts/04_heritage_by_year.vg.json",
  "#chart-05": "js/charts/05_birthplace_heatmap.vg.json",
  "#chart-06": "js/charts/06_overseas_born_line.vg.json",
  "#chart-08": "js/charts/08_attendance_dumbbell.vg.json",
  "#chart-08b": "js/charts/08b_attendance_change_map.vg.json",
  "#chart-07a": "js/charts/07a_naps_artforms.vg.json",
  "#chart-07b": "js/charts/07b_naps_age_slope.vg.json",
  "#chart-09a": "js/charts/09a_library_loans.vg.json",
  "#chart-09b": "js/charts/09b_library_index.vg.json",
  "#chart-10": "js/charts/10_live_streamgraph.vg.json",
  "#chart-11": "js/charts/11_live_symbol_map.vg.json",
  "#chart-13": "js/charts/13_funding_choropleth.vg.json",
  "#chart-14": "js/charts/14_funding_treemap.vg.json",
};

async function embed(el, url) {
  const spec = await (await fetch(url)).json();
  // Full Vega specs (the treemap) have no "container" width, so size them to their column.
  // Their autosize is "fit", so this width includes the title, legend and padding.
  if (spec.$schema.includes("/vega/")) {
    spec.width = Math.max(320, document.querySelector(el).clientWidth);
    // On narrow screens the one-row legend is too wide, so wrap it into two columns.
    if (spec.width < 640 && spec.legends) spec.legends.forEach((l) => (l.columns = 2));
  }
  return vegaEmbed(el, spec, opts);
}

// Vega measures text when it draws, so wait for the web font first; otherwise labels are sized
// for the fallback font and get clipped once Source Sans 3 arrives.
const fontsReady = Promise.all([
  document.fonts.load('400 12px "Source Sans 3"'),
  document.fonts.load('600 12px "Source Sans 3"'),
]).catch(() => {});

fontsReady.then(() => {
  for (const [el, url] of Object.entries(charts)) {
    embed(el, url).catch((err) => console.error(url, err));
  }
});
