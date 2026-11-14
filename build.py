"""Build dist/index.html: merge data/*.json + Hofstede CSV into template.html, validating as we go.

    python3 build.py

Fails loudly if any country is missing an indicator, a weight set doesn't sum to 100,
or a dimension has no country-level source.
"""
import csv, json, pathlib, statistics

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
DIMS = ["pdi", "idv", "mas", "uai", "ltowvs", "ivr"]
# regional clusters and sub-national samples: usable as fallbacks, excluded from the variance pool
NON_COUNTRY = {"ARA", "AFE", "AFW", "BEF", "BEN", "CAF", "GEE", "SAW", "SWF", "SWG"}
WB_KEYS = ["gdp_pc", "gdp", "internet", "lpi", "corruption", "voice", "reg_quality"]

def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def hofstede():
    rows = {}
    with open(DATA / "hofstede_6d_2015.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            rows[r["ctr"]] = {d: (None if r[d] == "#NULL!" else float(r[d])) for d in DIMS}
            rows[r["ctr"]]["label"] = r["country"]
    variances = {d: statistics.pvariance([v[d] for k, v in rows.items()
                                          if k not in NON_COUNTRY and v[d] is not None]) for d in DIMS}
    return rows, variances

def main():
    countries, wb, trade, industries = (load(n) for n in
                                        ["countries.json", "worldbank.json", "trade.json", "industries.json"])
    sources = load("sources.json")
    pair_notes = load("pair_notes.json")
    hof, variances = hofstede()
    errors = []

    for iso, c in countries.items():
        own, fb = hof.get(c["hof"]), hof.get(c["hof_fallback"]) if c["hof_fallback"] else None
        if own is None:
            errors.append(f"{iso}: Hofstede code {c['hof']} not in dataset")
            continue
        vals, from_cluster = {}, []
        for d in DIMS:
            if own[d] is not None:
                vals[d] = own[d]
            elif fb and fb[d] is not None:
                vals[d] = fb[d]
                from_cluster.append(d)
        c["hofstede"] = vals
        c["hofstede_label"] = own["label"]
        c["hofstede_cluster"] = {"label": fb["label"], "dims": from_cluster} if from_cluster else None
        if len(vals) < 4:
            errors.append(f"{iso}: only {len(vals)} Hofstede dimensions")
        for k in WB_KEYS:
            if k not in wb.get(iso, {}):
                errors.append(f"{iso}: missing World Bank indicator {k}")
        c["wb"] = wb[iso]

    for k, ind in industries.items():
        if sum(ind["weights"].values()) != 100:
            errors.append(f"industry {k}: weights do not sum to 100")
    for d in "CAGE":
        if not any(s["dim"] == d for s in sources.values()):
            errors.append(f"dimension {d}: no country-level source")

    if errors:
        raise SystemExit("Build failed:\n  " + "\n  ".join(errors))

    payload = dict(countries=countries, variances=variances, trade=trade, industries=industries,
                   sources=sources, pair_notes=pair_notes, hofstede_dims=DIMS)
    html = (ROOT / "template.html").read_text(encoding="utf-8")
    html = html.replace("/*__DATA__*/null", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "index.html").write_text(html, encoding="utf-8")
    print(f"Built dist/index.html: {len(countries)} countries, {len(industries)} industries, "
          f"{len(sources)} sources, {len(html) // 1024} KB")

if __name__ == "__main__":
    main()
