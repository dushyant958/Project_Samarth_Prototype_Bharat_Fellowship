# analyzer.py
import pandas as pd
import numpy as np
from datetime import datetime

class CitationTracker:
    def __init__(self):
        self.citations = []

    def add(self, dataset_name, query_type, data_points, columns_used):
        self.citations.append({
            'dataset': dataset_name,
            'query_type': query_type,
            'data_points': int(data_points),
            'columns': list(columns_used),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    def formatted(self):
        if not self.citations:
            return "No data sources used."
        out = []
        for i, c in enumerate(self.citations, 1):
            cols = ', '.join(c['columns'])
            out.append(f"[{i}] {c['dataset']} — {c['query_type']} — points={c['data_points']} — cols=[{cols}] — {c['timestamp']}")
        return "\n".join(out)

def _find_column(df, candidates):
    """
    Utility: return first column name in df that matches any candidate (case-insensitive)
    """
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        for col_lower, col_real in lower_map.items():
            if cand.lower() in col_lower:
                return col_real
    return None

def query_rainfall(parsed, datasets, citation_tracker):
    """
    Query all rainfall datasets using parsed query.
    Returns: dict keyed by location name -> stats dict
    """
    results = {}
    for ds in datasets.get('rainfall', []):
        df = ds.df.copy()
        # locate important columns
        loc_col = _find_column(df, ['subdiv', 'subdivision', 'state', 'region', 'district'])
        year_col = _find_column(df, ['year'])
        # annual column may be present or computed
        annual_col = _find_column(df, ['annual', 'annual rainfall', 'annual_mm', 'annual_rainfall', 'total'])
        # attempt to compute annual if no single annual column exists
        if annual_col is None:
            months = [c for c in df.columns if c.strip().upper() in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']]
            if months:
                df['__ANNUAL__'] = df[months].sum(axis=1)
                annual_col = '__ANNUAL__'
        if loc_col is None or annual_col is None:
            # Not a usable rainfall dataset for our purposes
            continue

        # determine candidate locations from parsed
        parsed_locs = parsed.get('locations', ['all'])
        if 'all' in [p.lower() for p in parsed_locs]:
            candidate_locs = df[loc_col].dropna().unique()
        else:
            candidate_locs = parsed_locs

        for loc in candidate_locs:
            try:
                if str(loc).lower() == 'all':
                    continue
                # fuzzy match rows where loc_col contains loc (case-insensitive)
                mask = df[loc_col].astype(str).str.lower().str.contains(str(loc).lower(), na=False)
                sel = df[mask]
                if sel.empty:
                    continue

                # optionally filter by years if requested and year_col exists
                if parsed.get('years') and year_col:
                    sel = sel[sel[year_col].astype(str).isin([str(y) for y in parsed.get('years')])]

                # apply time period filters if year_col exists
                tp = parsed.get('time_period', 'all')
                if tp.startswith('last_') and year_col:
                    max_year = pd.to_numeric(df[year_col], errors='coerce').max()
                    if not np.isnan(max_year):
                        span = int(tp.split('_')[1])
                        sel = sel[pd.to_numeric(sel[year_col], errors='coerce') >= (max_year - span + 1)]

                if sel.empty:
                    continue

                # compute stats
                annual_vals = pd.to_numeric(sel[annual_col], errors='coerce').dropna()
                if annual_vals.empty:
                    continue

                avg = float(annual_vals.mean())
                mn = float(annual_vals.min())
                mx = float(annual_vals.max())

                results[str(loc)] = {
                    'rainfall_avg': avg,
                    'rainfall_min': mn,
                    'rainfall_max': mx,
                    'data_points': int(len(annual_vals)),
                    'years': f"{sel[year_col].min()}-{sel[year_col].max()}" if year_col else "All",
                    'source': ds.name
                }

                citation_tracker.add(ds.name, f"rainfall stats for {loc}", len(annual_vals), [loc_col, annual_col] if year_col else [loc_col] )
            except Exception:
                continue
    return results

def query_crops(parsed, datasets, citation_tracker):
    """
    Query crop datasets using parsed query.
    Returns: dict keyed by "<location>_<crop>" -> stats dict
    """
    results = {}
    for ds in datasets.get('crops', []):
        df = ds.df.copy()
        # detect likely columns
        district_col = _find_column(df, ['district', 'district name'])
        state_col = _find_column(df, ['state', 'state name'])
        crop_col = _find_column(df, ['crop', 'crop name', 'crop_type'])
        production_col = _find_column(df, ['production', 'production_in', 'production_tonnes', 'production_tonnes'])
        area_col = _find_column(df, ['area', 'area_in', 'area_hectares', 'area (ha)'])
        # also accept seasonal 'All Seasons Production' patterns
        if production_col is None:
            candidates = [c for c in df.columns if 'production' in c.lower()]
            if candidates:
                production_col = candidates[0]

        if not (district_col or state_col) or production_col is None:
            # dataset cannot be used for production queries
            continue

        loc_col = district_col if district_col else state_col

        parsed_locs = parsed.get('locations', ['all'])
        if 'all' in [p.lower() for p in parsed_locs]:
            candidate_locs = df[loc_col].dropna().unique()
        else:
            candidate_locs = parsed_locs

        crops = parsed.get('crops', [])
        if not crops and crop_col:
            crops = list(df[crop_col].dropna().unique())[:10]  # sample some crops

        for loc in candidate_locs:
            for crop in crops:
                try:
                    if str(loc).lower() == 'all':
                        continue
                    mask_loc = df[loc_col].astype(str).str.lower().str.contains(str(loc).lower(), na=False)
                    if crop_col:
                        mask_crop = df[crop_col].astype(str).str.lower().str.contains(str(crop).lower(), na=False)
                        sel = df[mask_loc & mask_crop]
                    else:
                        sel = df[mask_loc]

                    if sel.empty:
                        continue

                    # production values numeric coercion
                    prod_series = pd.to_numeric(sel[production_col], errors='coerce').dropna()
                    if prod_series.empty:
                        continue

                    total_prod = float(prod_series.sum())
                    avg_prod = float(prod_series.mean())
                    area_sum = None
                    if area_col:
                        area_sum = float(pd.to_numeric(sel[area_col], errors='coerce').dropna().sum()) if not sel[area_col].dropna().empty else None

                    key = f"{str(loc)}_{str(crop)}"
                    results[key] = {
                        'location': str(loc),
                        'crop': str(crop),
                        'production_total': total_prod,
                        'production_avg': avg_prod,
                        'area': area_sum,
                        'data_points': int(len(prod_series)),
                        'source': ds.name
                    }

                    used_cols = [loc_col, production_col]
                    if crop_col:
                        used_cols.append(crop_col)
                    if area_col:
                        used_cols.append(area_col)
                    citation_tracker.add(ds.name, f"production for {crop} in {loc}", len(prod_series), used_cols)
                except Exception:
                    continue
    return results

def combine_and_analyze(parsed, rainfall_results, crop_results):
    """
    Combine results into an explanatory answer and a structured summary object.
    Returns: (text_answer:str, summary:dict)
    summary can include dataframes or lists for plotting by front-end.
    """
    action = parsed.get('action', 'compare')
    limit = parsed.get('limit', 5)
    answer_lines = []
    summary = {}

    if action in ['top', 'bottom']:
        # Rainfall ranking
        if rainfall_results:
            sorted_r = sorted(rainfall_results.items(), key=lambda x: x[1]['rainfall_avg'], reverse=(action=='top'))[:limit]
            answer_lines.append(f"### {'Top' if action=='top' else 'Bottom'} {limit} Subdivisions by Average Rainfall")
            for rank, (loc, stats) in enumerate(sorted_r, start=1):
                answer_lines.append(f"{rank}. **{loc}** — {stats['rainfall_avg']:.1f} mm/year (source: {stats['source']})")
            summary['rainfall_rank'] = sorted_r

        # Crop ranking
        if crop_results:
            sorted_c = sorted(crop_results.items(), key=lambda x: x[1]['production_total'], reverse=(action=='top'))[:limit]
            answer_lines.append(f"\n### {'Top' if action=='top' else 'Bottom'} {limit} Crop Production Regions")
            for rank, (k, stats) in enumerate(sorted_c, start=1):
                answer_lines.append(f"{rank}. **{stats['location']} - {stats['crop']}** — {stats['production_total']:.0f} tonnes (source: {stats['source']})")
            summary['crop_rank'] = sorted_c

    elif action == 'compare':
        # three cases: rainfall-only, crop-only, both
        if rainfall_results and not crop_results:
            answer_lines.append("### Rainfall Comparison")
            for loc, s in rainfall_results.items():
                answer_lines.append(f"**{loc}** — Avg: {s['rainfall_avg']:.1f} mm/year; Range: {s['rainfall_min']:.1f} - {s['rainfall_max']:.1f} (source: {s['source']})")
            summary['rainfall'] = rainfall_results

        elif crop_results and not rainfall_results:
            answer_lines.append("### Crop Production Comparison")
            for key, s in crop_results.items():
                answer_lines.append(f"**{s['location']} - {s['crop']}** — Total: {s['production_total']:.0f} tonnes; Avg: {s['production_avg']:.0f} (source: {s['source']})")
            summary['crops'] = crop_results

        else:
            answer_lines.append("### Cross-domain analysis: Rainfall vs Crop Production")
            combined = []
            for rloc, rdata in rainfall_results.items():
                for ckey, cdata in crop_results.items():
                    # locale matching heuristic
                    if rloc.lower() in cdata['location'].lower() or cdata['location'].lower() in rloc.lower():
                        combined.append((rloc, rdata, cdata))
            if combined:
                for rloc, rdata, cdata in combined:
                    answer_lines.append(f"**{rloc}** — Rainfall: {rdata['rainfall_avg']:.1f} mm/year [{rdata['source']}]; {cdata['crop'].title()} production: {cdata['production_total']:.0f} tonnes [{cdata['source']}]")
                summary['combined'] = combined
            else:
                answer_lines.append("No strong locality-level matches found between your rainfall and crop datasets. Consider providing a mapping or checking district/state names.")

    elif action == 'correlate':
        answer_lines.append("### Correlation Analysis")
        rows = []
        for rloc, rdata in rainfall_results.items():
            for ckey, cdata in crop_results.items():
                if rloc.lower() in cdata['location'].lower() or cdata['location'].lower() in rloc.lower():
                    rows.append({'rainfall': rdata['rainfall_avg'], 'production': cdata['production_total'], 'crop': cdata['crop'], 'loc': rloc})
        if rows:
            df = pd.DataFrame(rows)
            corr = df['rainfall'].corr(df['production'])
            answer_lines.append(f"Pearson correlation between rainfall and production for matched localities: {corr:.2f}")
            summary['correlation'] = float(corr)
            summary['correlation_df'] = df
        else:
            answer_lines.append("Insufficient matched locality pairs for correlation analysis.")

    elif action == 'recommend':
        answer_lines.append("### Policy Recommendations (data-backed heuristics)")
        # Classify subdivisions
        low = []
        med = []
        high = []
        for loc, s in rainfall_results.items():
            r = s['rainfall_avg']
            if r < 800:
                low.append((loc, r))
            elif r > 1500:
                high.append((loc, r))
            else:
                med.append((loc, r))

        if low:
            answer_lines.append("Low-rainfall regions (consider drought-resistant crops):")
            for loc, r in low[:10]:
                answer_lines.append(f"- {loc}: {r:.0f} mm/year")
        if high:
            answer_lines.append("High-rainfall regions (suitable for water-intensive crops):")
            for loc, r in high[:10]:
                answer_lines.append(f"- {loc}: {r:.0f} mm/year")
        if not (low or high):
            answer_lines.append("Insufficient rainfall data for regional recommendations.")

    # fallback message if nothing generated
    if not answer_lines:
        answer_lines = ["No result could be generated for the requested query. Check dataset availability and spelling of locations/crops."]

    return "\n\n".join(answer_lines), summary
