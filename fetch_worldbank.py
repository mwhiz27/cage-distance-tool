"""Pull country-level World Bank indicators for the CAGE tool into data/worldbank.json.

Uses the bulk-CSV endpoint (one zip per indicator); the JSON query API was returning 502s.
Keeps the latest non-empty year for each country.
"""
import csv, io, json, urllib.request, zipfile

ISO3 = ("USA CAN MEX BRA ARG CHL COL PER GBR IRL FRA DEU ESP ITA NLD BEL AUT CHE SWE NOR DNK POL PRT "
        "RUS TUR SAU ARE QAT EGY MAR ISR ZAF NGA KEN IND CHN JPN KOR SGP IDN VNM THA PHL MYS AUS NZL").split()

INDICATORS = {
    "gdp_pc":      "NY.GDP.PCAP.CD",   # GDP per capita, current US$
    "gdp":         "NY.GDP.MKTP.CD",   # GDP, current US$
    "internet":    "IT.NET.USER.ZS",   # Individuals using the Internet, % of population
    "lpi":         "LP.LPI.OVRL.XQ",   # Logistics Performance Index, overall (1-5)
    "corruption":  "CC.EST",           # WGI Control of Corruption, estimate (-2.5..2.5)
    "voice":       "VA.EST",           # WGI Voice and Accountability, estimate
    "reg_quality": "RQ.EST",           # WGI Regulatory Quality, estimate
}

def bulk(indicator):
    url = f"https://api.worldbank.org/v2/en/indicator/{indicator}?downloadformat=csv"
    with urllib.request.urlopen(url, timeout=120) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    name = next(n for n in z.namelist() if n.startswith("API_"))
    lines = z.read(name).decode("utf-8-sig").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith('"Country Name"'))
    return list(csv.DictReader(lines[start:]))

def meta():
    """Capital city + coordinates + income group from the country endpoint."""
    url = f"https://api.worldbank.org/v2/country/{';'.join(ISO3)}?format=json&per_page=100"
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)[1]

out = {c: {} for c in ISO3}
for key, ind in INDICATORS.items():
    for row in bulk(ind):
        c = row["Country Code"]
        if c not in out:
            continue
        years = [y for y in row if y.isdigit() and row[y].strip()]
        if years:
            y = max(years)
            out[c][key] = {"value": float(row[y]), "year": int(y)}
    print(f"{key:12s} {ind:16s} {sum(key in v for v in out.values())}/{len(ISO3)}")

json.dump(out, open("data/worldbank.json", "w"), indent=1)
try:
    for c in meta():
        out[c["id"]].update(name=c["name"], capital=c["capitalCity"],
                            lat=float(c["latitude"]), lon=float(c["longitude"]))
    json.dump(out, open("data/worldbank.json", "w"), indent=1)
except Exception as e:
    print("country metadata unavailable:", e)
