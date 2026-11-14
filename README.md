# CAGE Distance Analyzer

Ghemawat CAGE distance between any two of 46 countries, scored per dimension with industry-specific weights, cited country-level data, and weight sensitivity.

Live: https://mwhiz27.github.io/cage-distance-tool/

- `fetch_worldbank.py` pulls World Bank WDI/WGI/LPI indicators into `data/worldbank.json`
- `data/` holds the Hofstede 6-D dataset, curated country attributes, trade agreements/sanctions, industry weights, and sources
- `template.html` is the UI and scoring engine; `python3 build.py` validates the data and writes `dist/index.html`
