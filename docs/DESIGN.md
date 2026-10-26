# Dashboard design

The dashboard's look lives in `app/design.py`. It covers presentation only and reads no results.

- **Colours.** Ink `#17212B` (text, actual series), route teal `#0B6E69` (final forecast, navigation),
  amber `#A86500` (same hour last week), plum `#6A4FA3` (historical average). Crowding: low `#DCEDE7`,
  medium `#F3D985`, high `#B23A32`. Each cell in the crowding strip also shows a letter (L, M, H), so it
  does not rely on colour alone.
- **Type.** Newsreader for titles and the data page; Overpass for the interface, numbers and charts.
  Both use the SIL OFL 1.1 licence, are bundled in `app/fonts/`, and are embedded, so the offline demo
  looks the same. Overpass leaves out U+00B7 (the middle dot) because its glyph has zero width.
- **Layout.** The five pages appear as stops on a route line in the sidebar. Results appear as
  publication-style tables (rules above and below, tabular figures, best value in bold).
- **Theme.** `.streamlit/config.toml` (local) and `web/index.html` (public stlite build) set the same
  values. `tests/test_web.py` checks that they agree.
