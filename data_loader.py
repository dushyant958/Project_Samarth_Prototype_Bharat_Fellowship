# data_loader.py
import glob
import os
import pandas as pd
from datetime import datetime

class DatasetInfo:
    def __init__(self, name, df, dtype, null_pct, years_range=None):
        self.name = name
        self.df = df
        self.type = dtype
        self.null_pct = null_pct
        self.years_range = years_range
        self.records = len(df)

def load_all_datasets(data_folder="data"):
    """
    Load CSV files from `data_folder` and classify them into rainfall or crop datasets.
    Returns: { 'rainfall': [DatasetInfo,...], 'crops': [DatasetInfo,...], 'metadata': {filename: {...}} }
    """
    datasets = {'rainfall': [], 'crops': [], 'metadata': {}}
    data_files = glob.glob(os.path.join(data_folder, "*.csv"))

    for path in data_files:
        name = os.path.basename(path)
        try:
            df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
            # normalize column names
            df.columns = df.columns.str.strip()
            null_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100

            cols_lower = ' '.join([c.lower() for c in df.columns])
            # heuristics to classify
            is_rainfall = any(k in cols_lower for k in ['rain', 'precipitation', 'annual', 'monsoon', 'subdivision', 'jan', 'feb', 'mar'])
            is_crop = any(k in cols_lower for k in ['crop', 'production', 'area', 'yield', 'district', 'kharif', 'rabi', 'all seasons'])

            years_range = None
            for col in df.columns:
                if 'year' in col.lower():
                    try:
                        years_range = f"{df[col].min()}-{df[col].max()}"
                    except Exception:
                        years_range = None
                    break

            if is_rainfall:
                info = DatasetInfo(name, df, 'rainfall', null_pct, years_range)
                datasets['rainfall'].append(info)
                datasets['metadata'][name] = {'type': 'rainfall', 'null_pct': null_pct, 'records': info.records, 'years_range': years_range}
            elif is_crop:
                info = DatasetInfo(name, df, 'crop', null_pct, years_range)
                datasets['crops'].append(info)
                datasets['metadata'][name] = {'type': 'crop', 'null_pct': null_pct, 'records': info.records, 'years_range': years_range}
            else:
                # fallback heuristics
                if any(m in cols_lower for m in ['jan', 'feb', 'mar', 'apr']):
                    info = DatasetInfo(name, df, 'rainfall', null_pct, years_range)
                    datasets['rainfall'].append(info)
                    datasets['metadata'][name] = {'type': 'rainfall', 'null_pct': null_pct, 'records': info.records, 'years_range': years_range}
                else:
                    info = DatasetInfo(name, df, 'crop', null_pct, years_range)
                    datasets['crops'].append(info)
                    datasets['metadata'][name] = {'type': 'crop', 'null_pct': null_pct, 'records': info.records, 'years_range': years_range}
        except Exception as e:
            # skip file but continue loading others
            print(f"Failed to load {name}: {e}")
            continue

    return datasets

def build_state_district_map(datasets):
    """
    Build a naive state->district mapping from crop datasets. This is heuristic and
    intended as a fallback. Replace with a proper mapping CSV for production.
    Returns: dict: { 'StateName': ['DISTRICT1', 'DISTRICT2', ...], ... }
    """
    mapping = {}
    for ds in datasets.get('crops', []):
        df = ds.df
        district_cols = [c for c in df.columns if 'district' in c.lower()]
        state_cols = [c for c in df.columns if 'state' in c.lower()]

        districts = []
        states = []
        if district_cols:
            col = district_cols[0]
            districts = [str(x).strip().upper() for x in df[col].dropna().unique()]
        if state_cols:
            col = state_cols[0]
            states = [str(x).strip().title() for x in df[col].dropna().unique()]

        inferred_state = None
        fname = ds.name.lower()
        for st in ['karnataka', 'maharashtra', 'uttar pradesh', 'tamil nadu', 'kerala', 'gujarat', 'punjab', 'bihar']:
            if st in fname:
                inferred_state = st.title()
                break

        if states:
            for s in states:
                mapping.setdefault(s, set()).update(districts if districts else [])
        elif inferred_state:
            mapping.setdefault(inferred_state, set()).update(districts if districts else [])
        else:
            mapping.setdefault('Unknown', set()).update(districts if districts else [])

    # convert sets to sorted lists
    return {k: sorted(list(v)) for k, v in mapping.items()}
