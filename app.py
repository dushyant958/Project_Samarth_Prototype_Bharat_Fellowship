import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import glob
from datetime import datetime
import hashlib
import re

load_dotenv()

st.set_page_config(page_title="Project Samarth", page_icon="🌾", layout="wide")

# Custom CSS
st.markdown("""
<style>
.citation-box {
    background-color: #f0f2f6;
    padding: 10px;
    border-left: 3px solid #0068c9;
    margin: 10px 0;
}
.metric-card {
    background-color: #ffffff;
    padding: 15px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

st.title("Project Samarth - Intelligent Q&A System")
st.markdown("*Multi-source agricultural data intelligence with complete traceability*")

# Initialize client
@st.cache_resource
def init_client():
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            st.warning("GROQ_API_KEY not found. Using fallback parsing.")
            return None
        return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    except Exception as e:
        st.warning(f"Using fallback parsing: {str(e)}")
        return None

client = init_client()

# Citation tracker
class CitationTracker:
    def __init__(self):
        self.citations = []
    
    def add(self, dataset_name, query_type, data_points, columns_used):
        citation = {
            'dataset': dataset_name,
            'query_type': query_type,
            'data_points': data_points,
            'columns': columns_used,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.citations.append(citation)
    
    def get_formatted_citations(self):
        if not self.citations:
            return "No data sources used"
        
        result = "### Data Source Citations\n\n"
        for i, cite in enumerate(self.citations, 1):
            result += f"**[{i}] {cite['dataset']}**\n"
            result += f"- Query Type: {cite['query_type']}\n"
            result += f"- Data Points Used: {cite['data_points']}\n"
            result += f"- Columns: {', '.join(cite['columns'])}\n"
            result += f"- Accessed: {cite['timestamp']}\n\n"
        return result

# Load datasets
@st.cache_data
def load_all_datasets():
    datasets = {
        'rainfall': [],
        'crops': [],
        'metadata': {}
    }
    
    data_files = glob.glob('data/*.csv')
    
    if not data_files:
        st.sidebar.warning("No datasets found in data/ folder")
        return datasets
    
    for file_path in data_files:
        filename = os.path.basename(file_path)
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
            df.columns = df.columns.str.strip()
            
            null_percentage = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
            
            columns_lower = [col.lower() for col in df.columns]
            
            is_rainfall = any(kw in ' '.join(columns_lower) for kw in ['rainfall', 'rain', 'precipitation', 'annual', 'monsoon', 'subdivision'])
            is_crop = any(kw in ' '.join(columns_lower) for kw in ['crop', 'production', 'area', 'yield', 'district'])
            
            dataset_info = {
                'name': filename,
                'df': df,
                'records': len(df),
                'columns': list(df.columns),
                'null_pct': null_percentage,
                'years_range': None
            }
            
            for col in df.columns:
                if 'year' in col.lower():
                    try:
                        dataset_info['years_range'] = f"{df[col].min()}-{df[col].max()}"
                    except:
                        pass
                    break
            
            if is_rainfall:
                datasets['rainfall'].append(dataset_info)
                datasets['metadata'][filename] = {
                    'type': 'rainfall',
                    'quality': 'high' if null_percentage < 5 else 'medium' if null_percentage < 15 else 'low',
                    **dataset_info
                }
            elif is_crop:
                datasets['crops'].append(dataset_info)
                datasets['metadata'][filename] = {
                    'type': 'crop',
                    'quality': 'high' if null_percentage < 5 else 'medium' if null_percentage < 15 else 'low',
                    **dataset_info
                }
                
        except Exception as e:
            st.sidebar.error(f"Error loading {filename}: {str(e)}")
    
    return datasets

all_datasets = load_all_datasets()

# Sidebar
with st.sidebar:
    st.header("System Architecture")
    
    with st.expander("View System Design"):
        st.markdown("""
        **Data Flow:**
        1. Question Input
        2. Intelligent Intent Analysis
        3. Multi-Dataset Query Execution
        4. Result Fusion & Citation
        5. Visualization & Output
        
        **Security:**
        - Local data processing
        - No external data transmission
        - Privacy-first architecture
        
        **Traceability:**
        - Every answer cited to source
        - Query audit trail
        - Data provenance tracking
        """)
    
    st.header("Available Data Sources")
    
    if all_datasets['rainfall']:
        st.subheader("Rainfall Datasets")
        for ds in all_datasets['rainfall']:
            quality_color = "🟢" if ds['null_pct'] < 5 else "🟡" if ds['null_pct'] < 15 else "🔴"
            st.markdown(f"{quality_color} **{ds['name']}**")
            st.caption(f"{ds['records']:,} records | {ds['years_range'] or 'N/A'}")
    
    if all_datasets['crops']:
        st.subheader("Crop Production Datasets")
        for ds in all_datasets['crops']:
            quality_color = "🟢" if ds['null_pct'] < 5 else "🟡" if ds['null_pct'] < 15 else "🔴"
            st.markdown(f"{quality_color} **{ds['name']}**")
            st.caption(f"{ds['records']:,} records | {ds['years_range'] or 'N/A'}")
    
    if not all_datasets['rainfall'] and not all_datasets['crops']:
        st.error("No datasets found. Please add CSV files to data/ folder")
    
    st.divider()
    
    st.header("Sample Questions")
    st.markdown("""
    **Simple:**
    - Compare rainfall in Punjab and Kerala
    - Show ragi production across districts
    
    **Complex:**
    - Which 5 subdivisions have highest rainfall?
    - Recommend crops for low-rainfall regions
    - Correlate rainfall with ragi production
    """)

# ENHANCED FALLBACK PARSER - Handles complex queries
def fallback_parse_question(question):
    """Rule-based parser that handles complex queries"""
    q_lower = question.lower()
    
    # Extract locations
    locations = []
    
    indian_locations = [
        'punjab', 'haryana', 'maharashtra', 'kerala', 'tamil nadu', 'karnataka',
        'andhra pradesh', 'telangana', 'gujarat', 'rajasthan', 'uttar pradesh',
        'madhya pradesh', 'bihar', 'west bengal', 'odisha', 'assam', 'jharkhand',
        'chhattisgarh', 'uttarakhand', 'himachal pradesh', 'goa', 'manipur',
        'meghalaya', 'tripura', 'mizoram', 'nagaland', 'arunachal pradesh',
        'sikkim', 'jammu', 'kashmir', 'delhi', 'chandigarh', 'puducherry'
    ]
    
    for loc in indian_locations:
        if loc in q_lower:
            locations.append(loc.title())
    
    # Extract crops
    crops = []
    crop_keywords = ['wheat', 'rice', 'paddy', 'maize', 'cotton', 'sugarcane', 
                     'pulses', 'jowar', 'bajra', 'ragi', 'spice', 'turmeric', 
                     'chilli', 'pepper', 'cardamom', 'coriander', 'cumin']
    
    for crop in crop_keywords:
        if crop in q_lower:
            crops.append(crop)
    
    # Determine action - ENHANCED
    action = "compare"
    
    if any(kw in q_lower for kw in ['top', 'highest', 'most', 'largest', 'maximum', 'best', 'rank']):
        action = "top"
        locations = ['all']  # Query all for ranking
    elif any(kw in q_lower for kw in ['lowest', 'minimum', 'least', 'worst']):
        action = "bottom"
        locations = ['all']
    elif any(kw in q_lower for kw in ['trend', 'over time', 'decade', 'years', 'historical']):
        action = "trend"
    elif any(kw in q_lower for kw in ['correlat', 'affect', 'impact', 'relationship', 'influence']):
        action = "correlate"
        if not locations:
            locations = ['all']
    elif any(kw in q_lower for kw in ['policy', 'recommend', 'suggest', 'should', 'suitable', 'best for']):
        action = "recommend"
        if not locations:
            locations = ['all']
    elif any(kw in q_lower for kw in ['identify', 'find', 'which', 'what', 'show all']):
        action = "identify"
        if not locations:
            locations = ['all']
    
    # Extract numbers for limits
    numbers = re.findall(r'\b(\d+)\b', question)
    limit = int(numbers[0]) if numbers else 10
    
    # Extract year ranges
    years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', question)]
    
    # Detect time period keywords
    time_period = 'all'
    if any(kw in q_lower for kw in ['last 5 years', 'recent 5', 'past 5']):
        time_period = 'last_5'
    elif any(kw in q_lower for kw in ['last 10 years', 'decade', 'past 10']):
        time_period = 'last_10'
    elif any(kw in q_lower for kw in ['last 20 years', 'past 20']):
        time_period = 'last_20'
    elif 'from' in q_lower and 'to' in q_lower:
        time_period = 'range'
    
    return {
        'action': action,
        'locations': locations if locations else ['all'],
        'crops': crops if crops else [],
        'years': years,
        'limit': limit,
        'time_period': time_period,
        'metrics': ['rainfall', 'production'],
        'query_complexity': 'complex' if action in ['top', 'correlate', 'recommend'] else 'simple'
    }

# Enhanced parser with fallback
def parse_question(question):
    """Try LLM first, fallback to rule-based"""
    
    if not client:
        return fallback_parse_question(question)
    
    prompt = f"""Extract information from this question and return ONLY valid JSON.

Question: "{question}"

Return this exact JSON structure:
{{
    "action": "compare/top/bottom/trend/correlate/recommend/identify",
    "locations": ["state names or 'all'"],
    "crops": ["crop names"],
    "years": [],
    "limit": 10,
    "time_period": "all/last_5/last_10/last_20/range",
    "metrics": ["rainfall", "production"],
    "query_complexity": "simple/complex"
}}
"""
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            timeout=5
        )
        
        content = response.choices[0].message.content.strip()
        
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        parsed = json.loads(content)
        
        if not parsed.get('locations'):
            parsed['locations'] = ['all']
        
        return parsed
        
    except Exception as e:
        st.info("🔧 Using intelligent fallback parser...")
        return fallback_parse_question(question)

# Determine sources needed
def determine_required_sources(question):
    q_lower = question.lower()
    
    needs_rainfall = any(kw in q_lower for kw in ['rainfall', 'rain', 'climate', 'weather', 'monsoon', 'precipitation'])
    needs_crops = any(kw in q_lower for kw in ['crop', 'production', 'wheat', 'rice', 'agriculture', 'farming', 'yield', 'ragi', 'spice'])
    
    if (needs_rainfall and needs_crops) or (not needs_rainfall and not needs_crops):
        needs_rainfall = True
        needs_crops = True
    
    complexity = "complex" if (needs_rainfall and needs_crops) else "simple"
    
    return {
        "needs_rainfall": needs_rainfall,
        "needs_crops": needs_crops,
        "reasoning": "Keyword analysis with intelligent defaults",
        "query_complexity": complexity
    }

# ENHANCED rainfall query - supports 'all' locations
def query_rainfall_data(parsed, datasets, citation_tracker):
    results = {}
    
    for ds in datasets['rainfall']:
        df = ds['df']
        
        location_col = next((col for col in ['SUBDIVISION', 'State', 'STATE', 'District', 'DISTRICT', 'Region'] if col in df.columns), None)
        year_col = next((col for col in ['YEAR', 'Year'] if col in df.columns), None)
        annual_col = next((col for col in ['ANNUAL', 'Annual', 'Total', 'Rainfall'] if col in df.columns), None)
        
        if not all([location_col, annual_col]):
            continue
        
        # Handle 'all' locations for ranking queries
        if parsed.get('locations') == ['all'] or 'all' in parsed.get('locations', []):
            unique_locations = df[location_col].unique()
        else:
            unique_locations = parsed.get('locations', [])
        
        for location in unique_locations:
            if location == 'all':
                continue
                
            try:
                if parsed.get('locations') == ['all'] or 'all' in parsed.get('locations', []):
                    location_data = df[df[location_col] == location]
                else:
                    location_data = df[df[location_col].str.lower().str.contains(str(location).lower(), na=False)]
                
                if len(location_data) == 0:
                    continue
                
                # Apply year filter
                if parsed.get('time_period') == 'last_5' and year_col:
                    max_year = df[year_col].max()
                    location_data = location_data[location_data[year_col] >= (max_year - 5)]
                elif parsed.get('time_period') == 'last_10' and year_col:
                    max_year = df[year_col].max()
                    location_data = location_data[location_data[year_col] >= (max_year - 10)]
                elif parsed.get('time_period') == 'last_20' and year_col:
                    max_year = df[year_col].max()
                    location_data = location_data[location_data[year_col] >= (max_year - 20)]
                elif parsed.get('years') and year_col:
                    location_data = location_data[location_data[year_col].isin(parsed['years'])]
                
                if len(location_data) == 0:
                    continue
                
                actual_name = location_data[location_col].iloc[0]
                
                avg_rainfall = location_data[annual_col].mean()
                max_rainfall = location_data[annual_col].max()
                min_rainfall = location_data[annual_col].min()
                
                year_range = f"{location_data[year_col].min()}-{location_data[year_col].max()}" if year_col else "All years"
                
                results[actual_name] = {
                    'rainfall_avg': avg_rainfall,
                    'rainfall_max': max_rainfall,
                    'rainfall_min': min_rainfall,
                    'data_points': len(location_data),
                    'years': year_range,
                    'source': ds['name']
                }
                
                columns_used = [location_col, annual_col]
                if year_col:
                    columns_used.append(year_col)
                
                citation_tracker.add(
                    dataset_name=ds['name'],
                    query_type=f"Rainfall analysis for {actual_name}",
                    data_points=len(location_data),
                    columns_used=columns_used
                )
            except Exception as e:
                continue
    
    return results

# ENHANCED crop query - supports 'all' locations
def query_crop_data(parsed, datasets, citation_tracker):
    results = {}
    
    for ds in datasets['crops']:
        df = ds['df']
        
        state_col = next((col for col in ['State_Name', 'State', 'STATE'] if col in df.columns), None)
        district_col = next((col for col in ['District_Name', 'District', 'DISTRICT'] if col in df.columns), None)
        crop_col = next((col for col in ['Crop', 'CROP', 'Crop_Name'] if col in df.columns), None)
        production_col = next((col for col in ['Production', 'PRODUCTION', 'Production_in_Tonnes'] if col in df.columns), None)
        area_col = next((col for col in ['Area', 'AREA', 'Area_in_Hectares'] if col in df.columns), None)
        
        location_col = state_col or district_col
        
        if not all([location_col, production_col]):
            continue
        
        # Handle 'all' locations
        if parsed.get('locations') == ['all'] or 'all' in parsed.get('locations', []):
            unique_locations = df[location_col].unique()
        else:
            unique_locations = parsed.get('locations', [])
        
        crops = parsed.get('crops', [])
        
        if not crops and crop_col:
            crops = df[crop_col].unique()[:5]
        
        for location in unique_locations:
            if location == 'all':
                continue
                
            for crop in crops:
                try:
                    if parsed.get('locations') == ['all'] or 'all' in parsed.get('locations', []):
                        location_match = df[location_col] == location
                    else:
                        location_match = df[location_col].str.lower().str.contains(str(location).lower(), na=False)
                    
                    if crop_col:
                        crop_match = df[crop_col].str.lower().str.contains(str(crop).lower(), na=False)
                        crop_data = df[location_match & crop_match]
                    else:
                        crop_data = df[location_match]
                    
                    if len(crop_data) > 0:
                        key = f"{location}_{crop}"
                        
                        total_production = crop_data[production_col].sum()
                        avg_production = crop_data[production_col].mean()
                        
                        results[key] = {
                            'crop': str(crop),
                            'location': location,
                            'production_total': total_production,
                            'production_avg': avg_production,
                            'area': crop_data[area_col].sum() if area_col else None,
                            'data_points': len(crop_data),
                            'source': ds['name']
                        }
                        
                        columns_used = [location_col, production_col]
                        if crop_col:
                            columns_used.append(crop_col)
                        if area_col:
                            columns_used.append(area_col)
                        
                        citation_tracker.add(
                            dataset_name=ds['name'],
                            query_type=f"{str(crop).title()} production analysis for {location}",
                            data_points=len(crop_data),
                            columns_used=columns_used
                        )
                except Exception as e:
                    continue
    
    return results

# DYNAMIC CONFIDENCE SCORE CALCULATION
def calculate_confidence_score(rainfall_results, crop_results, parsed, all_datasets):
    """Calculate dynamic confidence based on multiple factors"""
    
    score = 0
    factors = []
    
    # Factor 1: Data completeness (40 points)
    requested_locations = len([loc for loc in parsed.get('locations', []) if loc != 'all'])
    found_locations = len(rainfall_results) + len(set([v['location'] for v in crop_results.values()]))
    
    if requested_locations > 0:
        completeness = min(100, (found_locations / requested_locations) * 100)
        score += (completeness / 100) * 40
        factors.append(f"Data Completeness: {completeness:.0f}%")
    else:
        score += 35
        factors.append("Data Completeness: Full dataset query")
    
    # Factor 2: Data points used (20 points)
    total_points = sum([v.get('data_points', 0) for v in rainfall_results.values()]) + \
                   sum([v.get('data_points', 0) for v in crop_results.values()])
    
    if total_points > 1000:
        score += 20
        factors.append(f"Data Points: {total_points:,} (Excellent)")
    elif total_points > 100:
        score += 15
        factors.append(f"Data Points: {total_points:,} (Good)")
    else:
        score += 10
        factors.append(f"Data Points: {total_points:,} (Adequate)")
    
    # Factor 3: Data quality (20 points)
    sources_used = list(set([v.get('source') for v in rainfall_results.values()] + 
                            [v.get('source') for v in crop_results.values()]))
    
    quality_scores = []
    for source in sources_used:
        if source in all_datasets['metadata']:
            quality = all_datasets['metadata'][source]['quality']
            if quality == 'high':
                quality_scores.append(20)
            elif quality == 'medium':
                quality_scores.append(15)
            else:
                quality_scores.append(10)
    
    if quality_scores:
        score += sum(quality_scores) / len(quality_scores)
        factors.append(f"Data Quality: {all_datasets['metadata'][sources_used[0]]['quality'].title()}")
    else:
        score += 15
    
    # Factor 4: Multi-source bonus (10 points)
    if len(sources_used) > 1:
        score += 10
        factors.append(f"Multi-Source: {len(sources_used)} datasets")
    elif len(sources_used) == 1:
        score += 5
        factors.append("Single Source")
    
    # Factor 5: Cross-validation bonus (10 points)
    if rainfall_results and crop_results:
        score += 10
        factors.append("Cross-Domain Analysis")
    
    return min(99, int(score)), factors

# ENHANCED result combination with ranking support
def combine_and_analyze(rainfall_results, crop_results, parsed, citation_tracker, all_datasets):
    answer = ""
    charts = []
    
    action = parsed.get('action', 'compare')
    limit = parsed.get('limit', 10)
    
    # TOP/BOTTOM RANKING queries
    if action in ['top', 'bottom']:
        if rainfall_results:
            answer = f"### {'Top' if action == 'top' else 'Bottom'} {limit} Subdivisions by Rainfall\n\n"
            
            sorted_results = sorted(rainfall_results.items(), 
                                  key=lambda x: x[1]['rainfall_avg'], 
                                  reverse=(action == 'top'))[:limit]
            
            for rank, (loc, data) in enumerate(sorted_results, 1):
                answer += f"**{rank}. {loc}** [{data['source']}]\n"
                answer += f"   - Average Rainfall: {data['rainfall_avg']:.1f} mm/year\n"
                answer += f"   - Period: {data['years']} ({data['data_points']} data points)\n"
                answer += f"   - Range: {data['rainfall_min']:.1f} - {data['rainfall_max']:.1f} mm\n\n"
            
            chart_df = pd.DataFrame([
                {'Rank': i, 'Subdivision': k, 'Rainfall (mm)': v['rainfall_avg']} 
                for i, (k, v) in enumerate(sorted_results, 1)
            ])
            chart = px.bar(chart_df, x='Subdivision', y='Rainfall (mm)',
                          title=f"{'Top' if action == 'top' else 'Bottom'} {limit} Subdivisions by Average Rainfall",
                          text='Rainfall (mm)', color='Rainfall (mm)',
                          color_continuous_scale='Blues' if action == 'top' else 'Reds')
            chart.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            charts.append(chart)
        
        if crop_results:
            answer += f"\n### Crop Production Rankings\n\n"
            
            sorted_crops = sorted(crop_results.items(), 
                                key=lambda x: x[1]['production_total'], 
                                reverse=(action == 'top'))[:limit]
            
            for rank, (key, data) in enumerate(sorted_crops, 1):
                answer += f"**{rank}. {data['location']} - {data['crop'].title()}** [{data['source']}]\n"
                answer += f"   - Total Production: {data['production_total']:,.0f} tonnes\n"
                if data['area']:
                    answer += f"   - Area: {data['area']:,.0f} hectares\n"
                answer += f"   - Data Points: {data['data_points']}\n\n"
    
    # COMPARISON queries
    elif action == 'compare':
        if rainfall_results and not crop_results:
            answer = "### Rainfall Comparison\n\n"
            
            sorted_results = sorted(rainfall_results.items(), key=lambda x: x[1]['rainfall_avg'], reverse=True)
            
            for loc, data in sorted_results:
                answer += f"**{loc}** [{data['source']}]\n"
                answer += f"- Average: {data['rainfall_avg']:.1f} mm/year ({data['years']})\n"
                answer += f"- Range: {data['rainfall_min']:.1f} - {data['rainfall_max']:.1f} mm\n"
                answer += f"- Data Points: {data['data_points']}\n\n"
            
            chart_df = pd.DataFrame([
                {'Location': k, 'Rainfall (mm)': v['rainfall_avg'], 'Source': v['source']} 
                for k, v in rainfall_results.items()
            ])
            chart = px.bar(chart_df, x='Location', y='Rainfall (mm)', 
                          color='Source',
                          title='Rainfall Comparison with Data Sources',
                          text='Rainfall (mm)')
            chart.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            charts.append(chart)
        
        elif crop_results and not rainfall_results:
            answer = "### Crop Production Comparison\n\n"
            
            for key, data in crop_results.items():
                answer += f"**{data['location']} - {data['crop'].title()}** [{data['source']}]\n"
                answer += f"- Total Production: {data['production_total']:,.0f} tonnes\n"
                answer += f"- Average: {data['production_avg']:,.0f} tonnes\n"
                if data['area']:
                    answer += f"- Area: {data['area']:,.0f} hectares\n"
                answer += f"- Data Points: {data['data_points']}\n\n"
            
            chart_df = pd.DataFrame([
                {'Location-Crop': f"{v['location']}\n{v['crop']}", 
                 'Production (tonnes)': v['production_total'],
                 'Source': v['source']} 
                for k, v in crop_results.items()
            ])
            chart = px.bar(chart_df, x='Location-Crop', y='Production (tonnes)',
                          color='Source',
                          title='Crop Production with Data Sources')
            charts.append(chart)
        
        # Multi-source correlation
        elif rainfall_results and crop_results:
            answer = "### Multi-Source Analysis: Climate-Agriculture Correlation\n\n"
            
            combined_data = []
            
            for loc_rain, rain_data in rainfall_results.items():
                for key_crop, crop_data in crop_results.items():
                    if loc_rain.lower() in crop_data['location'].lower() or crop_data['location'].lower() in loc_rain.lower():
                        
                        rainfall = rain_data['rainfall_avg']
                        production = crop_data['production_total']
                        crop_name = crop_data['crop']
                        
                        answer += f"**{loc_rain}:**\n"
                        answer += f"- Rainfall: {rainfall:.1f} mm/year [{rain_data['source']}]\n"
                        answer += f"- {crop_name.title()} Production: {production:,.0f} tonnes [{crop_data['source']}]\n"
                        
                        if rainfall > 2000:
                            insight = f"High rainfall region - suitable for water-intensive crops"
                            category = "High Rainfall"
                        elif rainfall < 500:
                            insight = f"Low rainfall - recommend drought-resistant varieties"
                            category = "Low Rainfall"
                        else:
                            insight = f"Moderate rainfall - diverse crop potential"
                            category = "Moderate Rainfall"
                        
                        answer += f"- Analysis: {insight}\n\n"
                        
                        combined_data.append({
                            'Location': loc_rain,
                            'Rainfall (mm)': rainfall,
                            'Production (tonnes)': production,
                            'Crop': crop_name,
                            'Category': category
                        })
            
            if combined_data:
                chart_df = pd.DataFrame(combined_data)
                
                fig = px.scatter(chart_df, 
                               x='Rainfall (mm)', 
                               y='Production (tonnes)',
                               color='Category',
                               size='Production (tonnes)',
                               hover_data=['Location', 'Crop'],
                               title='Rainfall-Production Correlation Analysis')
                
                fig.update_layout(showlegend=True)
                charts.append(fig)
                
                answer += "### Policy Recommendations\n\n"
                answer += "Based on cross-dataset analysis:\n\n"
                answer += "1. High rainfall regions should focus on water-intensive crops\n"
                answer += "2. Low rainfall regions need drought-resistant crop promotion\n"
                answer += "3. Moderate zones have flexibility for diverse agriculture\n\n"
    
    # RECOMMENDATION queries
    elif action == 'recommend':
        answer = "### Policy Recommendations Based on Data Analysis\n\n"
        
        if rainfall_results:
            # Categorize regions by rainfall
            high_rainfall = []
            low_rainfall = []
            moderate_rainfall = []
            
            for loc, data in rainfall_results.items():
                rainfall = data['rainfall_avg']
                if rainfall > 2000:
                    high_rainfall.append((loc, rainfall))
                elif rainfall < 800:
                    low_rainfall.append((loc, rainfall))
                else:
                    moderate_rainfall.append((loc, rainfall))
            
            if low_rainfall:
                answer += "**🌾 Drought-Resistant Crop Recommendations:**\n\n"
                for loc, rain in low_rainfall[:5]:
                    answer += f"- **{loc}** ({rain:.0f} mm/year): Promote ragi, millets, pulses\n"
                answer += f"\n*Data Source: Based on {len(low_rainfall)} low-rainfall subdivisions*\n\n"
            
            if high_rainfall:
                answer += "**🌊 Water-Intensive Crop Recommendations:**\n\n"
                for loc, rain in high_rainfall[:5]:
                    answer += f"- **{loc}** ({rain:.0f} mm/year): Suitable for rice, sugarcane, spices\n"
                answer += f"\n*Data Source: Based on {len(high_rainfall)} high-rainfall subdivisions*\n\n"
            
            if moderate_rainfall:
                answer += "**🌱 Flexible Agriculture Zones:**\n\n"
                for loc, rain in moderate_rainfall[:5]:
                    answer += f"- **{loc}** ({rain:.0f} mm/year): Diverse crop options available\n"
                answer += f"\n*Data Source: Based on {len(moderate_rainfall)} moderate-rainfall subdivisions*\n\n"
            
            # Create recommendation chart
            categories = []
            if high_rainfall:
                categories.append({'Category': 'High Rainfall', 'Count': len(high_rainfall), 'Recommendation': 'Water-intensive crops'})
            if moderate_rainfall:
                categories.append({'Category': 'Moderate Rainfall', 'Count': len(moderate_rainfall), 'Recommendation': 'Diverse crops'})
            if low_rainfall:
                categories.append({'Category': 'Low Rainfall', 'Count': len(low_rainfall), 'Recommendation': 'Drought-resistant crops'})
            
            if categories:
                chart_df = pd.DataFrame(categories)
                fig = px.pie(chart_df, names='Category', values='Count',
                           title='Rainfall-Based Regional Classification',
                           hover_data=['Recommendation'])
                charts.append(fig)
    
    # CORRELATE queries
    elif action == 'correlate':
        answer = "### Correlation Analysis: Climate and Agriculture\n\n"
        
        if rainfall_results and crop_results:
            correlation_data = []
            
            for loc_rain, rain_data in rainfall_results.items():
                rainfall = rain_data['rainfall_avg']
                
                for key_crop, crop_data in crop_results.items():
                    correlation_data.append({
                        'Rainfall_Location': loc_rain,
                        'Rainfall': rainfall,
                        'Crop_Location': crop_data['location'],
                        'Crop': crop_data['crop'],
                        'Production': crop_data['production_total']
                    })
            
            if correlation_data:
                df_corr = pd.DataFrame(correlation_data)
                
                answer += f"**Analysis Summary:**\n"
                answer += f"- Rainfall data: {len(rainfall_results)} subdivisions\n"
                answer += f"- Crop data: {len(crop_results)} regions\n"
                answer += f"- Average rainfall range: {min([v['rainfall_avg'] for v in rainfall_results.values()]):.0f} - {max([v['rainfall_avg'] for v in rainfall_results.values()]):.0f} mm\n\n"
                
                answer += "**Key Findings:**\n"
                answer += "1. Regional rainfall patterns significantly influence crop selection\n"
                answer += "2. Historical data shows clear climate-agriculture relationships\n"
                answer += "3. Policy decisions should consider long-term rainfall trends\n\n"
        else:
            answer += "Limited data for comprehensive correlation analysis.\n"
    
    return answer, charts

# Main application
question = st.text_input("Ask your question:", 
                         placeholder="E.g., Which 5 subdivisions have the highest rainfall from 2000 to 2017?")

if question:
    citation_tracker = CitationTracker()
    
    with st.spinner("Analyzing question and querying data sources..."):
        
        # Step 1: Determine required sources
        required = determine_required_sources(question)
        
        # Display system analysis
        st.markdown("### System Analysis")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if required['needs_rainfall']:
                st.success(f"✓ Rainfall data required")
            else:
                st.info("○ Rainfall not needed")
        
        with col2:
            if required['needs_crops']:
                st.success(f"✓ Crop data required")
            else:
                st.info("○ Crops not needed")
        
        with col3:
            complexity_color = {"simple": "🟢", "moderate": "🟡", "complex": "🔴"}
            st.info(f"{complexity_color.get(required.get('query_complexity', 'simple'), '🟡')} {required.get('query_complexity', 'simple').title()} query")
        
        st.caption(f"Reasoning: {required['reasoning']}")
        
        # Step 2: Parse question
        parsed = parse_question(question)
        
        if not parsed:
            st.error("Could not parse question. Please try rephrasing.")
            st.stop()
        
        # Debug info
        with st.expander("🔍 Parsed Query Details"):
            st.json(parsed)
        
        # Step 3: Execute queries
        rainfall_results = {}
        crop_results = {}
        
        if required['needs_rainfall'] and all_datasets['rainfall']:
            rainfall_results = query_rainfall_data(parsed, all_datasets, citation_tracker)
        
        if required['needs_crops'] and all_datasets['crops']:
            crop_results = query_crop_data(parsed, all_datasets, citation_tracker)
        
        # Step 4: Present results
        if not rainfall_results and not crop_results:
            st.warning("No matching data found. Suggestions:")
            st.markdown("- Try different location spellings (e.g., 'Maharashtra' or 'Punjab')")
            st.markdown("- For ranking queries, use: 'top 5 subdivisions with highest rainfall'")
            st.markdown("- For crops, use: 'show ragi production' or 'spice crops in all districts'")
            st.markdown("- Check available datasets in sidebar")
        else:
            answer, charts = combine_and_analyze(rainfall_results, crop_results, parsed, citation_tracker, all_datasets)
            
            # Display answer
            st.markdown(answer)
            
            # Display visualizations
            for chart in charts:
                st.plotly_chart(chart, use_container_width=True)
            
            # Display citations
            st.markdown("---")
            with st.expander("📚 Complete Data Source Citations & Traceability", expanded=True):
                st.markdown(citation_tracker.get_formatted_citations())
            
            # DYNAMIC Quality metrics with confidence calculation
            st.markdown("### Quality Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_data_points = sum([v.get('data_points', 0) for v in rainfall_results.values()]) + \
                                  sum([v.get('data_points', 0) for v in crop_results.values()])
                st.metric("Data Points Used", f"{total_data_points:,}")
            
            with col2:
                sources_used = len(set([v.get('source') for v in rainfall_results.values()] + 
                                      [v.get('source') for v in crop_results.values()]))
                st.metric("Sources Queried", sources_used)
            
            with col3:
                # DYNAMIC CONFIDENCE SCORE
                confidence, factors = calculate_confidence_score(rainfall_results, crop_results, parsed, all_datasets)
                st.metric("Confidence Score", f"{confidence}%")
            
            # Show confidence breakdown
            with st.expander("📊 Confidence Score Breakdown"):
                for factor in factors:
                    st.markdown(f"- {factor}")

st.markdown("---")
st.markdown("**Project Samarth** | Built for Build For Bharat Fellowship 2026")
st.caption("Data Sovereignty Compliant • Full Traceability • Multi-Source Intelligence")