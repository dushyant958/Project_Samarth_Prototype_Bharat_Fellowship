# 🌾 Project Samarth - Intelligent Agricultural Q&A System

An end-to-end intelligent Q&A system built on data.gov.in agricultural and meteorological datasets. Ask complex natural language questions and get comprehensive, cited answers with beautiful visualizations.

## 🚀 Features

- **Natural Language Processing**: Ask questions in plain English
- **Multi-Source Integration**: Combines rainfall and crop production data
- **Smart Citation System**: Every claim is backed by data source citations
- **Advanced Visualizations**: Interactive charts using Plotly
- **Feasibility Checking**: System identifies impossible queries and suggests alternatives
- **Cross-Domain Analysis**: Correlates climate patterns with agricultural output

## 📁 Project Structure

```
project-samarth/
│
├── data/                          # Place your CSV files here
│   ├── Sub_Division_IMD_2017.csv
│   ├── Crop_Maize_Area_in_Hectares_Production_in_Tonnes_Yield_in_Kgs_Hectare.csv
│   ├── Crop_Ragi_Area_in_Hectares_Production_in_Tonnes_Yield_in_Kgs_Hectare.csv
│   ├── Crop_Rice_Area_in_Hectares_Production_in_Tonnes_Yield_in_Kgs_Hectare.csv
│   └── District_Wise_Area_Production_Yield_Value_Spice_Crops.csv
│
├── app.py                         # Main Streamlit application
├── parser.py                      # Query parser with feasibility checking
├── data_loader.py                 # Dataset loading and classification
├── analyzer.py                    # Data analysis and querying logic
├── answer_generator.py            # Natural language answer generation
├── visualizer.py                  # Advanced visualization creation
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your Data

Place all CSV files in a `data/` folder in the project root:

```bash
mkdir data
# Copy your CSV files into data/
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📊 Available Datasets

### Rainfall Data
- **File**: `Sub_Division_IMD_2017.csv`
- **Records**: 4,188
- **Time Range**: 1901-2017
- **Granularity**: 36 subdivisions (state/region level)
- **Metrics**: Monthly and annual rainfall in mm

### Crop Production Data
- **Files**: 
  - `Crop_Maize_Area_in_Hectares_Production_in_Tonnes_Yield_in_Kgs_Hectare.csv` (31 districts)
  - `Crop_Ragi_Area_in_Hectares_Production_in_Tonnes_Yield_in_Kgs_Hectare.csv` (31 districts)
  - `Crop_Rice_Area_in_Hectares_Production_in_Tonnes_Yield_in_Kgs_Hectare.csv` (31 districts)
- **Granularity**: District level (Karnataka)
- **Seasons**: Kharif, Rabi, Summer, All Seasons
- **Metrics**: Area (hectares), Production (tonnes), Yield (kg/hectare)
- **Limitation**: Snapshot data (no year column)

### Spice Production Data
- **File**: `District_Wise_Area_Production_Yield_Value_Spice_Crops.csv`
- **Records**: 30 districts
- **Metrics**: Area, Production, Value (aggregated spices)

## ✅ Sample Questions That WORK

### 🔝 Ranking Queries

1. **"Which 5 subdivisions have the highest rainfall from 2010 to 2017?"**
   - ✅ Works: Rainfall data has years
   - Output: Top 5 regions with average rainfall, range, data points

2. **"Top 10 districts by maize production"**
   - ✅ Works: District-level crop data available
   - Output: Ranked list with production volumes, area, efficiency

3. **"Which district has the lowest ragi production?"**
   - ✅ Works: Ranking query on snapshot data
   - Output: Bottom performer with comparison

### 📊 Comparison Queries

4. **"Compare maize production across all districts in Karnataka"**
   - ✅ Works: All districts in same dataset
   - Output: Comparative bar charts, production rankings

5. **"Compare kharif versus rabi season rice production"**
   - ✅ Works: Seasonal columns exist
   - Output: Season-wise comparison, insights on dominant season

6. **"Compare rainfall in Punjab and Kerala from 1990 to 2017"**
   - ✅ Works: Both subdivisions exist with year data
   - Output: Average rainfall, variability, time-period analysis

### 🔗 Correlation Queries

7. **"Correlate rainfall in Karnataka with maize production"**
   - ⚠️ Partial: Requires state-district mapping
   - Output: Fuzzy-matched regions, correlation coefficient if matches found

8. **"Relationship between rainfall and rice yields"**
   - ⚠️ Partial: Geographic matching may be limited
   - Output: Best-effort correlation with available matched pairs

### 📋 Policy Recommendation Queries

9. **"Recommend drought-resistant crops for low-rainfall regions"**
   - ✅ Works: Classifies regions by rainfall (<800mm)
   - Output: List of low-rainfall subdivisions, policy suggestions

10. **"Which regions should focus on water-intensive crops based on rainfall?"**
    - ✅ Works: Identifies high-rainfall areas (>1500mm)
    - Output: High-rainfall regions, crop recommendations

11. **"Best practices from top-performing districts for maize"**
    - ✅ Works: Identifies top performers
    - Output: Case study suggestions, performance metrics

### 🔍 Identification Queries

12. **"Which district has the highest rice production?"**
    - ✅ Works: Simple ranking
    - Output: Top district with detailed metrics

13. **"Find the district with maximum spice production value"**
    - ✅ Works: Spice data has value column
    - Output: Top performer by value metric

## ❌ Questions That DON'T WORK (and why)

### Temporal Queries on Crops

❌ **"Show rice production trend over the last decade"**
- **Why**: Crop data has NO year column (snapshot only)
- **Alternative**: "Show current rice production across all districts"

❌ **"Compare maize production in 2015 vs 2020"**
- **Why**: Crop data is single time point
- **Alternative**: "Compare current maize production across districts"

### Cross-Domain Temporal Queries

❌ **"Analyze production trend of rice in Karnataka over the last decade correlated with rainfall"**
- **Why**: No yearly crop data
- **Alternative**: "Show average rainfall in Karnataka from 2010-2017 and current rice production levels"

### Specific Crop Types in Spice Data

❌ **"Which district produces the most pepper?"**
- **Why**: Spice dataset has no crop type column
- **Alternative**: "Which district has highest total spice production?"

## 🎯 Query Rewriting Examples

The system automatically suggests alternatives for impossible queries:

**User asks**: "Show trend of ragi production over last 5 years"
- **System detects**: Temporal query on snapshot data
- **Suggests**: "Show current ragi production across all districts (snapshot data)"

**User asks**: "Compare rice in State X and State Y"
- **System detects**: State-level query for district data
- **Suggests**: "Compare rice production across districts within Karnataka"

## 🏗️ System Architecture

### 1. Query Parser (`parser.py`)
- Extracts: action, locations, crops, years, time periods
- Performs feasibility checking
- Suggests query rewrites for impossible requests

### 2. Data Loader (`data_loader.py`)
- Auto-classifies CSVs into rainfall/crop datasets
- Extracts metadata (years, null percentages, record counts)
- Builds state-district mapping (heuristic)

### 3. Analyzer (`analyzer.py`)
- `query_rainfall()`: Filters and aggregates rainfall data
- `query_crops()`: Filters and aggregates crop production data
- Citation tracking for all data usage

### 4. Answer Generator (`answer_generator.py`)
- Generates natural language explanations
- Context-aware insights (e.g., "low-rainfall region")
- Proper citations with source files

### 5. Visualizer (`visualizer.py`)
- Creates action-specific visualizations:
  - Rankings: Horizontal bar charts, variability charts
  - Comparisons: Multi-series bar charts
  - Correlations: Scatter plots with trendlines
  - Recommendations: Pie charts, treemaps

### 6. Streamlit App (`app.py`)
- User interface with question input
- Real-time parsing and analysis
- Interactive visualizations
- Report download functionality

## 🎨 Visualization Types

The system generates different charts based on query type:

| Query Type | Visualizations |
|------------|----------------|
| **Top/Bottom** | Horizontal bar chart, Variability chart, Efficiency scatter |
| **Compare** | Multi-series bar charts, Side-by-side comparisons |
| **Correlate** | Scatter plot with trendline, Correlation matrix |
| **Trend** | Box plots, Variability visualization |
| **Recommend** | Pie chart (categories), Treemap (best practices) |

## 📚 Citation System

Every data point is automatically cited:

```
[1] Sub_Division_IMD_2017.csv — rainfall stats for Punjab — points=117 — cols=[SUBDIVISION, ANNUAL] — 2024-01-15 14:30:22
[2] Crop_Maize_Area_Production.csv — production for maize in BAGALKOTE — points=1 — cols=[District Name, All Seasons_Production] — 2024-01-15 14:30:23
```

## 🔒 Data Sovereignty

- All processing happens locally
- No external API calls (can be deployed on-premise)
- Data never leaves your infrastructure
- Full compliance with data sovereignty requirements

## 🚧 Known Limitations

1. **State-District Mismatch**: Rainfall uses subdivisions, crops use districts. Requires mapping table or fuzzy matching.

2. **No Temporal Crop Data**: Crop datasets are snapshots. Cannot analyze trends over time for crops.

3. **No Crop Types in Spice Data**: Spice dataset is aggregated. Cannot query individual spice varieties.

4. **Geographic Matching**: Cross-domain queries rely on fuzzy string matching. May miss some valid location pairs.

## 🔮 Future Enhancements

- [ ] LLM-powered query parsing (OpenAI/Anthropic API)
- [ ] State-District mapping CSV for precise cross-referencing
- [ ] Time-series analysis for rainfall trends
- [ ] Export to PDF reports
- [ ] Multi-language support (Hindi, regional languages)
- [ ] Voice input for queries

## 📹 Demo Video Script

**Minute 1 (0:00-1:00)**: Dataset Overview
- Show sidebar with 5 datasets loaded
- Explain: Rainfall (1901-2017, 4K records) + Crops (31 districts, snapshot)
- Highlight: "Data directly from data.gov.in"

**Minute 2 (1:00-2:00)**: Live Demo
1. Ask: "Top 5 districts by maize production"
   - Show: Parsed query, results, bar chart
2. Ask: "Recommend crops for low-rainfall regions"
   - Show: Classification, policy recommendations
3. Show: Citations at bottom, download report button

**Wrap-up**: "Complete end-to-end prototype: data sourcing → parsing → analysis → visualization → citations"

## 🤝 Contributing

This is a hackathon prototype. Key areas for improvement:
- Better state-district mapping
- LLM integration for parsing
- More sophisticated correlation algorithms
- Additional visualizations

## 📄 License

Built for Project Samarth Challenge. Data sourced from data.gov.in under Open Government Data License.

---

**Built with**: Python, Streamlit, Pandas, Plotly
**Data Sources**: data.gov.in (Ministry of Agriculture & IMD)