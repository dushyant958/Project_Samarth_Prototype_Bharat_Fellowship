# app.py
import streamlit as st
import plotly.express as px
from data_loader import load_all_datasets, build_state_district_map
from parser import parse_question
from analyzer import query_rainfall, query_crops, combine_and_analyze, CitationTracker
from answer_generator import AnswerGenerator
from visualizer import DataVisualizer

st.set_page_config(page_title="Project Samarth - Q&A System", layout='wide', page_icon="🌾")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🌾 Project Samarth - Intelligent Agricultural Q&A System</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ask complex questions about India\'s agricultural economy and climate patterns</p>', unsafe_allow_html=True)

# Load datasets with caching
@st.cache_data
def load_data():
    """Load all datasets and return with mapping."""
    datasets = load_all_datasets()
    mapping = build_state_district_map(datasets)
    return datasets, mapping

with st.spinner("🔄 Loading datasets from data.gov.in..."):
    all_datasets, state_district_map = load_data()

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/4/41/Flag_of_India.svg/200px-Flag_of_India.svg.png", width=100)
    st.header("📊 Datasets Summary")
    
    if all_datasets['rainfall']:
        st.subheader("☔ Rainfall Datasets")
        total_rain_records = sum(ds.records for ds in all_datasets['rainfall'])
        st.metric("Total Records", f"{total_rain_records:,}")
        with st.expander("View Details"):
            for ds in all_datasets['rainfall']:
                st.write(f"📄 **{ds.name}**")
                st.write(f"- Records: {ds.records:,}")
                st.write(f"- Years: {ds.years_range or 'N/A'}")
                st.write(f"- Null %: {ds.null_pct:.1f}%")
    
    if all_datasets['crops']:
        st.subheader("🌾 Crop Datasets")
        total_crop_records = sum(ds.records for ds in all_datasets['crops'])
        st.metric("Total Records", f"{total_crop_records:,}")
        with st.expander("View Details"):
            for ds in all_datasets['crops']:
                st.write(f"📄 **{ds.name}**")
                st.write(f"- Records: {ds.records}")
                st.write(f"- Null %: {ds.null_pct:.1f}%")
    
    st.divider()
    st.markdown("### 💡 Tips")
    st.markdown("""
    - Use **specific locations** (e.g., "Karnataka", "Punjab")
    - Mention **crop names** (maize, ragi, rice)
    - For rankings, specify **numbers** (e.g., "top 5")
    - Ask about **rainfall patterns** or **production data**
    """)
    
    st.divider()
    st.markdown("### ⚙️ System Status")
    st.success("✅ All systems operational")
    st.info(f"📁 {len(all_datasets['rainfall'])} rainfall datasets loaded")
    st.info(f"📁 {len(all_datasets['crops'])} crop datasets loaded")

# Main content area
st.markdown("---")

# Example questions in expandable section
with st.expander("💭 **Example Questions** (Click to see what you can ask)"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔝 Ranking Queries:**")
        st.markdown("- Which 5 subdivisions have the highest rainfall from 2010 to 2017?")
        st.markdown("- Top 10 districts by maize production")
        st.markdown("- Which district has lowest ragi production?")
        
        st.markdown("**📊 Comparison Queries:**")
        st.markdown("- Compare maize production across all districts in Karnataka")
        st.markdown("- Compare rainfall in Punjab and Kerala")
        st.markdown("- Compare kharif versus rabi season rice production")
    
    with col2:
        st.markdown("**🔗 Correlation Queries:**")
        st.markdown("- Correlate rainfall with crop production in Karnataka")
        st.markdown("- Relationship between rainfall and maize yields")
        
        st.markdown("**📋 Policy Queries:**")
        st.markdown("- Recommend drought-resistant crops for low-rainfall regions")
        st.markdown("- Which regions should focus on water-intensive crops?")
        st.markdown("- Best practices from top-performing districts")

# Query input
st.markdown("### 🔍 Ask Your Question")
question = st.text_area(
    "Enter your question about agricultural data:",
    height=100,
    placeholder="Example: Which 5 districts have the highest maize production?"
)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    submit_button = st.button("🚀 Analyze", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)
with col3:
    show_debug = st.checkbox("🐛 Debug Mode", value=False)

if clear_button:
    st.rerun()

if submit_button and question:
    # Create citation tracker
    citation = CitationTracker()
    
    # Parse the question
    with st.spinner("🔍 Parsing your question..."):
        parsed = parse_question(question)
    
    # Show parsed query in debug mode
    if show_debug:
        with st.expander("🔍 Parsed Query Structure"):
            st.json(parsed)
    
    # Check feasibility
    if not parsed.get('feasible', True):
        st.warning(f"⚠️ **Query Limitation Detected:** {parsed.get('reasoning', 'Query may not be fully answerable')}")
        if parsed.get('rewritten_query'):
            st.info(f"💡 **Suggested Alternative:** {parsed['rewritten_query']}")
            if st.button("Use Suggested Query"):
                question = parsed['rewritten_query']
                st.rerun()
    
    # Determine which data sources to query
    needs_rain = parsed.get('needs_rainfall', False)
    needs_crop = parsed.get('needs_crops', False)
    
    # Query the data
    rain_res = {}
    crop_res = {}
    
    with st.spinner("📊 Querying datasets..."):
        if needs_rain and all_datasets['rainfall']:
            rain_res = query_rainfall(parsed, all_datasets, citation)
            if show_debug:
                st.write(f"🔵 Rainfall results: {len(rain_res)} locations")
        
        if needs_crop and all_datasets['crops']:
            crop_res = query_crops(parsed, all_datasets, citation)
            if show_debug:
                st.write(f"🟢 Crop results: {len(crop_res)} entries")
    
    # Check if we got results
    if not rain_res and not crop_res:
        st.error("❌ No matching data found. Please check:")
        st.markdown("""
        - Spelling of locations and crop names
        - Available datasets in the sidebar
        - Try rephrasing your question
        """)
    else:
        # Generate answer with old method for comparison
        answer_text_old, summary = combine_and_analyze(parsed, rain_res, crop_res)
        
        # Generate answer with new natural language generator
        with st.spinner("✨ Generating natural language answer..."):
            answer_generator = AnswerGenerator(parsed, rain_res, crop_res, citation)
            answer_text_new = answer_generator.generate()
        
        # Display the enhanced answer
        st.markdown("---")
        st.markdown("## 📝 Analysis Results")
        st.markdown(answer_text_new)
        
        # Create visualizations
        st.markdown("---")
        st.markdown("## 📊 Data Visualizations")
        
        with st.spinner("🎨 Creating visualizations..."):
            visualizer = DataVisualizer(parsed, rain_res, crop_res, summary)
            figures = visualizer.create_visualizations()
        
        if figures:
            # Display figures
            for name, fig in figures:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No visualizations generated for this query type.")
        
        # Show old analysis in debug mode
        if show_debug:
            with st.expander("🔧 Legacy Analysis Output"):
                st.markdown(answer_text_old)
        
        # Download option
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Prepare download data
            download_text = f"""# Project Samarth Analysis Report

## Question
{question}

## Analysis Results
{answer_text_new}

## Query Metadata
- Action: {parsed.get('action')}
- Locations: {', '.join(parsed.get('locations', []))}
- Crops: {', '.join(parsed.get('crops', []))}
- Data Sources: {len(rain_res)} rainfall, {len(crop_res)} crop entries
"""
            
            st.download_button(
                label="📥 Download Report (Markdown)",
                data=download_text,
                file_name="samarth_analysis_report.md",
                mime="text/markdown"
            )
        
        with col2:
            # Citation export
            citation_text = citation.formatted()
            st.download_button(
                label="📚 Download Citations",
                data=citation_text,
                file_name="data_citations.txt",
                mime="text/plain"
            )

elif submit_button and not question:
    st.warning("⚠️ Please enter a question to analyze.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p><strong>Project Samarth</strong> - Intelligent Q&A System over data.gov.in</p>
</div>
""", unsafe_allow_html=True)