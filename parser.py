# parser.py
import re
import json

# Dataset context for intelligent parsing
AVAILABLE_DATA_CONTEXT = """
Available Datasets:
1. RAINFALL DATA (Sub_Division_IMD_2017.csv):
   - Has: SUBDIVISION column (36 regions like "Punjab", "Kerala", "Andaman & Nicobar Islands")
   - Has: YEAR column (1901-2017)
   - Has: Monthly columns (JAN-DEC) and ANNUAL rainfall in mm
   - CAN answer: "rainfall in X from Y to Z years", "top N subdivisions by rainfall", "average rainfall"
   
2. CROP DATA (Maize/Ragi/Rice):
   - Has: District Name (31 districts in Karnataka)
   - Has: Seasonal production (Kharif, Rabi, Summer, All Seasons)
   - Has: Area (hectares), Production (tonnes), Yield (kg/hectare)
   - NO YEAR column - snapshot data only (single time point)
   - CAN answer: "district X maize production", "compare kharif vs rabi", "top districts by production"
   - CANNOT answer: "trend over years", "last N years for crops"

3. SPICE DATA (District_Wise_Area_Production_Yield_Value_Spice_Crops.csv):
   - Has: District Name, Area, Production, Value
   - NO crop type column - aggregated spice data
   - CAN answer: "total spice production by district"
"""

def fallback_parse_question(question):
    """Enhanced rule-based parser with feasibility checks."""
    q = question.strip()
    q_lower = q.lower()

    # Extended location keywords
    subdivisions = [
        'andaman & nicobar islands', 'arunachal pradesh', 'assam', 'bihar', 
        'chhattisgarh', 'coastal karnataka', 'east madhya pradesh', 'east rajasthan',
        'east uttar pradesh', 'gangetic west bengal', 'gujarat', 'haryana',
        'himachal pradesh', 'jammu & kashmir', 'jharkhand', 'karnataka',
        'kerala', 'konkan & goa', 'lakshadweep', 'madhya maharashtra',
        'marathwada', 'naga mani mizo tripura', 'north interior karnataka',
        'odisha', 'punjab', 'rayalseema', 'saurashtra & kutch', 'south interior karnataka',
        'sub himalayan west bengal & sikkim', 'tamil nadu', 'telangana',
        'uttarakhand', 'vidarbha', 'west madhya pradesh', 'west rajasthan', 'west uttar pradesh'
    ]
    
    districts = [
        'bagalkote', 'belgaum', 'bellary', 'bengaluru rural', 'bengaluru urban',
        'bidar', 'bijapur', 'chamarajanagar', 'chikkaballapur', 'chikkamagaluru',
        'chitradurga', 'dakshina kannada', 'davanagere', 'dharwad', 'gadag',
        'gulbarga', 'hassan', 'haveri', 'kodagu', 'kolar', 'koppal',
        'mandya', 'mysore', 'raichur', 'ramanagara', 'shimoga', 'tumkur',
        'udupi', 'uttara kannada', 'vijayapura', 'yadgir'
    ]
    
    locations = []
    for loc in subdivisions + districts:
        if loc in q_lower:
            locations.append(loc.title())
    
    # Crops detection
    crop_keywords = {
        'maize': ['maize', 'corn'],
        'ragi': ['ragi', 'finger millet'],
        'rice': ['rice', 'paddy'],
        'spice': ['spice', 'spices']
    }
    
    crops = []
    for crop, aliases in crop_keywords.items():
        if any(alias in q_lower for alias in aliases):
            crops.append(crop)

    # Action detection
    action = 'compare'
    
    if any(k in q_lower for k in ['top', 'highest', 'most', 'maximum', 'rank']):
        action = 'top'
    elif any(k in q_lower for k in ['bottom', 'lowest', 'least', 'minimum']):
        action = 'bottom'
    elif any(k in q_lower for k in ['trend', 'over time', 'decade', 'historical pattern']):
        action = 'trend'
    elif any(k in q_lower for k in ['correlat', 'relationship', 'affect', 'impact', 'influence']):
        action = 'correlate'
    elif any(k in q_lower for k in ['policy', 'recommend', 'suggest', 'should', 'advise']):
        action = 'recommend'
    elif any(k in q_lower for k in ['identify', 'find', 'which district', 'which state']):
        action = 'identify'
    elif any(k in q_lower for k in ['compare', 'versus', 'vs', 'difference between']):
        action = 'compare'

    # Extract numbers
    numbers = re.findall(r'\b(\d+)\b', q)
    limit = int(numbers[0]) if numbers else 5
    
    # Extract years
    years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', q)]

    # Time period
    time_period = 'all'
    if 'last 5 years' in q_lower or 'past 5 years' in q_lower:
        time_period = 'last_5'
    elif 'last 10 years' in q_lower or 'past 10 years' in q_lower or 'decade' in q_lower:
        time_period = 'last_10'
    elif 'last 20 years' in q_lower or 'past 20 years' in q_lower:
        time_period = 'last_20'
    elif 'from' in q_lower and 'to' in q_lower:
        time_period = 'range'

    # Determine data needs
    needs_rainfall = any(k in q_lower for k in ['rain', 'rainfall', 'precipitation', 'monsoon', 'annual'])
    needs_crops = any(k in q_lower for k in ['crop', 'production', 'yield', 'area', 'maize', 'ragi', 'rice', 'spice', 'district'])
    
    # Feasibility check
    feasible = True
    reasoning = ""
    rewritten_query = None
    
    if action == 'trend' and needs_crops and not needs_rainfall:
        feasible = False
        reasoning = "Crop datasets have no year column - only snapshot data available. Cannot analyze trends over time for crops."
        rewritten_query = f"Show current crop production across districts (snapshot data)"
    
    if action == 'trend' and needs_crops and needs_rainfall:
        reasoning = "Will show rainfall trends over time. Crop data is snapshot only, so will show current production alongside historical rainfall patterns."
        rewritten_query = f"Compare historical rainfall trends with current crop production levels"
    
    if locations and not needs_rainfall and not needs_crops:
        needs_rainfall = True
        needs_crops = True
        reasoning = "Querying both rainfall and crop data for comprehensive analysis"

    parsed = {
        'raw': q,
        'action': action,
        'locations': locations if locations else ['all'],
        'crops': crops if crops else [],
        'years': years,
        'limit': limit,
        'time_period': time_period,
        'needs_rainfall': needs_rainfall,
        'needs_crops': needs_crops,
        'feasible': feasible,
        'reasoning': reasoning,
        'rewritten_query': rewritten_query,
        'expected_result': _generate_expected_result(action, locations, crops, needs_rainfall, needs_crops)
    }

    return parsed


def _generate_expected_result(action, locations, crops, needs_rainfall, needs_crops):
    """Generate expected result description."""
    parts = []
    
    if action == 'top':
        parts.append(f"Rankings of top performers")
    elif action == 'bottom':
        parts.append(f"Rankings of bottom performers")
    elif action == 'compare':
        parts.append(f"Comparative analysis")
    elif action == 'correlate':
        parts.append(f"Correlation analysis between variables")
    elif action == 'trend':
        parts.append(f"Trend analysis over time")
    elif action == 'recommend':
        parts.append(f"Data-backed policy recommendations")
    
    if needs_rainfall:
        parts.append("rainfall statistics")
    if needs_crops:
        parts.append("crop production data")
    
    if locations and locations != ['all']:
        parts.append(f"for {', '.join(locations[:3])}")
    
    return " with ".join(parts)


def parse_question(question, llm_client=None, available_context=None):
    """Top-level parse function."""
    parsed = fallback_parse_question(question)
    
    # Normalize
    parsed['locations'] = [str(l).strip() for l in parsed['locations']]
    parsed['crops'] = [str(c).strip().lower() for c in parsed['crops']]
    
    return parsed