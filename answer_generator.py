# answer_generator.py
import json
from datetime import datetime
import pandas as pd
import numpy as np

class AnswerGenerator:
    """Generates natural language answers with proper citations."""
    
    def __init__(self, parsed_query, rainfall_results, crop_results, citation_tracker):
        self.parsed = parsed_query
        self.rainfall = rainfall_results
        self.crops = crop_results
        self.citations = citation_tracker
        self.answer_parts = []
        
    def generate(self):
        """Main entry point to generate complete answer."""
        action = self.parsed.get('action', 'compare')
        
        self._add_header()
        
        if action == 'top':
            self._generate_ranking_answer(ascending=False)
        elif action == 'bottom':
            self._generate_ranking_answer(ascending=True)
        elif action == 'compare':
            self._generate_comparison_answer()
        elif action == 'correlate':
            self._generate_correlation_answer()
        elif action == 'recommend':
            self._generate_recommendation_answer()
        elif action == 'trend':
            self._generate_trend_answer()
        elif action == 'identify':
            self._generate_identification_answer()
        else:
            self._generate_comparison_answer()
        
        self._add_data_quality_note()
        self._add_citations()
        
        return "\n\n".join(self.answer_parts)
    
    def _add_header(self):
        """Generate intelligent header."""
        action = self.parsed.get('action', 'compare')
        locations = self.parsed.get('locations', [])
        crops = self.parsed.get('crops', [])
        
        header = "### "
        
        if action == 'top':
            header += f"Top {self.parsed.get('limit', 5)} "
            if self.rainfall:
                header += "Regions by Rainfall"
            elif self.crops:
                header += "Districts by Crop Production"
        elif action == 'bottom':
            header += f"Bottom {self.parsed.get('limit', 5)} "
            if self.rainfall:
                header += "Regions by Rainfall"
            elif self.crops:
                header += "Districts by Crop Production"
        elif action == 'compare':
            if locations and locations != ['all']:
                header += f"Comparative Analysis: {' vs '.join(locations[:3])}"
            elif crops:
                header += f"Crop Production Analysis: {', '.join([c.title() for c in crops[:3]])}"
            else:
                header += "Agricultural Data Analysis"
        elif action == 'correlate':
            header += "Correlation Analysis: Rainfall and Crop Production"
        elif action == 'recommend':
            header += "Policy Recommendations Based on Agricultural Data"
        elif action == 'trend':
            header += "Trend Analysis"
        else:
            header += "Agricultural Data Insights"
        
        self.answer_parts.append(header)
    
    def _generate_ranking_answer(self, ascending=False):
        """Generate ranking answers."""
        limit = self.parsed.get('limit', 5)
        direction = "lowest" if ascending else "highest"
        
        if self.rainfall:
            sorted_rain = sorted(
                self.rainfall.items(), 
                key=lambda x: x[1]['rainfall_avg'],
                reverse=not ascending
            )[:limit]
            
            self.answer_parts.append(
                f"Based on the analysis of historical rainfall data spanning multiple decades, "
                f"I've identified the {limit} subdivisions with the {direction} average annual rainfall. "
                f"This ranking is derived from comprehensive meteorological records:"
            )
            
            for rank, (loc, stats) in enumerate(sorted_rain, 1):
                years_info = stats.get('years', 'Multiple years')
                data_pts = stats.get('data_points', 0)
                
                entry = (
                    f"\n**{rank}. {loc}**  \n"
                    f"- Average Annual Rainfall: **{stats['rainfall_avg']:.1f} mm**  \n"
                    f"- Range: {stats['rainfall_min']:.1f} mm to {stats['rainfall_max']:.1f} mm  \n"
                    f"- Data Coverage: {years_info} ({data_pts} observations)  \n"
                    f"- Source: `{stats['source']}`"
                )
                self.answer_parts.append(entry)
        
        if self.crops:
            sorted_crops = sorted(
                self.crops.items(),
                key=lambda x: x[1]['production_total'],
                reverse=not ascending
            )[:limit]
            
            if self.rainfall:
                self.answer_parts.append(f"\n#### Crop Production Rankings")
            
            self.answer_parts.append(
                f"Analyzing district-level agricultural production data, here are the {limit} districts "
                f"with the {direction} crop production volumes:"
            )
            
            for rank, (key, stats) in enumerate(sorted_crops, 1):
                area_info = f"{stats['area']:.1f} hectares" if stats.get('area') else "Area data unavailable"
                
                entry = (
                    f"\n**{rank}. {stats['location']} - {stats['crop'].title()}**  \n"
                    f"- Total Production: **{stats['production_total']:.0f} tonnes**  \n"
                    f"- Average Production: {stats['production_avg']:.0f} tonnes  \n"
                    f"- Cultivated Area: {area_info}  \n"
                    f"- Source: `{stats['source']}`"
                )
                self.answer_parts.append(entry)
    
    def _generate_comparison_answer(self):
        """Generate comparison answers."""
        if self.rainfall and not self.crops:
            self.answer_parts.append(
                "I've analyzed the rainfall patterns across the specified regions. "
                "Here's a detailed comparison of precipitation levels:"
            )
            
            for loc, stats in self.rainfall.items():
                entry = (
                    f"\n**{loc}**  \n"
                    f"- Average Annual Rainfall: **{stats['rainfall_avg']:.1f} mm**  \n"
                    f"- Minimum Recorded: {stats['rainfall_min']:.1f} mm  \n"
                    f"- Maximum Recorded: {stats['rainfall_max']:.1f} mm  \n"
                    f"- Observations: {stats.get('data_points', 0)} data points spanning {stats.get('years', 'multiple years')}  \n"
                    f"- Data Source: `{stats['source']}`"
                )
                self.answer_parts.append(entry)
                
                avg_rain = stats['rainfall_avg']
                if avg_rain < 800:
                    self.answer_parts.append(
                        f"  → *Classification*: Low-rainfall region. Suitable for drought-resistant crops."
                    )
                elif avg_rain > 1500:
                    self.answer_parts.append(
                        f"  → *Classification*: High-rainfall region. Optimal for water-intensive crops like rice."
                    )
                else:
                    self.answer_parts.append(
                        f"  → *Classification*: Moderate-rainfall region. Suitable for diverse crop cultivation."
                    )
        
        elif self.crops and not self.rainfall:
            self.answer_parts.append(
                "Here's a comprehensive comparison of crop production across districts. "
                "The data represents current agricultural output:"
            )
            
            for key, stats in self.crops.items():
                entry = (
                    f"\n**{stats['location']} - {stats['crop'].title()}**  \n"
                    f"- Total Production: **{stats['production_total']:.0f} tonnes**  \n"
                    f"- Average Yield: {stats['production_avg']:.0f} tonnes  \n"
                )
                
                if stats.get('area'):
                    productivity = stats['production_total'] / stats['area']
                    entry += f"- Cultivated Area: {stats['area']:.1f} hectares  \n"
                    entry += f"- Productivity: {productivity:.2f} tonnes/hectare  \n"
                
                entry += f"- Data Source: `{stats['source']}`"
                self.answer_parts.append(entry)
        
        else:
            self._generate_cross_domain_analysis()
    
    def _generate_cross_domain_analysis(self):
        """Generate integrated rainfall-crop analysis."""
        self.answer_parts.append(
            "I've performed a cross-domain analysis integrating meteorological and agricultural data. "
            "This analysis reveals the relationship between rainfall patterns and crop production:"
        )
        
        matched_pairs = []
        for rain_loc, rain_stats in self.rainfall.items():
            for crop_key, crop_stats in self.crops.items():
                rain_lower = rain_loc.lower()
                crop_lower = crop_stats['location'].lower()
                
                if rain_lower in crop_lower or crop_lower in rain_lower or \
                   any(part in crop_lower for part in rain_lower.split()):
                    matched_pairs.append((rain_loc, rain_stats, crop_stats))
        
        if matched_pairs:
            for rain_loc, rain_stats, crop_stats in matched_pairs:
                entry = (
                    f"\n**Region: {rain_loc} / {crop_stats['location']}**  \n"
                    f"- Rainfall: {rain_stats['rainfall_avg']:.1f} mm/year (Range: {rain_stats['rainfall_min']:.1f}-{rain_stats['rainfall_max']:.1f} mm) "
                    f"[Source: `{rain_stats['source']}`]  \n"
                    f"- {crop_stats['crop'].title()} Production: {crop_stats['production_total']:.0f} tonnes "
                    f"[Source: `{crop_stats['source']}`]  \n"
                )
                
                rain_avg = rain_stats['rainfall_avg']
                prod = crop_stats['production_total']
                
                if rain_avg > 1200 and prod > 50000:
                    entry += f"  → *Insight*: High rainfall supports strong {crop_stats['crop']} production."
                elif rain_avg < 800 and prod < 10000:
                    entry += f"  → *Insight*: Low rainfall may be limiting {crop_stats['crop']} yields."
                else:
                    entry += f"  → *Insight*: Production levels appear suitable for the rainfall conditions."
                
                self.answer_parts.append(entry)
        else:
            self.answer_parts.append(
                "\n*Note*: Direct geographic matching between rainfall subdivisions and crop districts "
                "could not be established. The data shows:\n"
            )
            self.answer_parts.append("**Rainfall Data:**")
            for loc, stats in list(self.rainfall.items())[:3]:
                self.answer_parts.append(f"- {loc}: {stats['rainfall_avg']:.1f} mm/year")
            
            self.answer_parts.append("\n**Crop Production Data:**")
            for key, stats in list(self.crops.items())[:3]:
                self.answer_parts.append(
                    f"- {stats['location']}: {stats['crop'].title()} - {stats['production_total']:.0f} tonnes"
                )
    
    def _generate_correlation_answer(self):
        """Generate correlation analysis."""
        if not (self.rainfall and self.crops):
            self.answer_parts.append(
                "Correlation analysis requires both rainfall and crop production data. "
                "The current query returned data from only one domain."
            )
            return
        
        self.answer_parts.append(
            "I've conducted a correlation analysis to identify relationships between "
            "rainfall patterns and agricultural production:"
        )
        
        matched_data = []
        for rain_loc, rain_stats in self.rainfall.items():
            for crop_key, crop_stats in self.crops.items():
                if rain_loc.lower() in crop_stats['location'].lower() or \
                   crop_stats['location'].lower() in rain_loc.lower():
                    matched_data.append({
                        'location': rain_loc,
                        'rainfall': rain_stats['rainfall_avg'],
                        'production': crop_stats['production_total'],
                        'crop': crop_stats['crop']
                    })
        
        if len(matched_data) >= 3:
            df = pd.DataFrame(matched_data)
            correlation = df['rainfall'].corr(df['production'])
            
            self.answer_parts.append(
                f"\n**Correlation Coefficient: {correlation:.3f}**\n"
            )
            
            if abs(correlation) > 0.7:
                strength = "strong"
            elif abs(correlation) > 0.4:
                strength = "moderate"
            else:
                strength = "weak"
            
            direction = "positive" if correlation > 0 else "negative"
            
            self.answer_parts.append(
                f"The analysis reveals a **{strength} {direction} correlation** between rainfall "
                f"and crop production across {len(matched_data)} matched locations."
            )
            
            if correlation > 0.5:
                self.answer_parts.append(
                    "\n*Interpretation*: Higher rainfall is associated with increased crop production, "
                    "suggesting water availability is a key limiting factor for agricultural output."
                )
            elif correlation < -0.5:
                self.answer_parts.append(
                    "\n*Interpretation*: Higher rainfall is associated with decreased production, "
                    "which may indicate flooding issues or waterlogging affecting crop growth."
                )
            else:
                self.answer_parts.append(
                    "\n*Interpretation*: The relationship between rainfall and production is not strongly linear, "
                    "suggesting other factors (soil quality, farming practices, crop variety) play significant roles."
                )
        else:
            self.answer_parts.append(
                f"\nInsufficient matched data points ({len(matched_data)}) for robust correlation analysis. "
                "Correlation requires at least 3 location pairs."
            )
    
    def _generate_recommendation_answer(self):
        """Generate policy recommendations."""
        self.answer_parts.append(
            "Based on comprehensive analysis of available agricultural and meteorological data, "
            "here are data-backed policy recommendations:"
        )
        
        if self.rainfall:
            low_rain = [(loc, s) for loc, s in self.rainfall.items() if s['rainfall_avg'] < 800]
            high_rain = [(loc, s) for loc, s in self.rainfall.items() if s['rainfall_avg'] > 1500]
            
            if low_rain:
                self.answer_parts.append(
                    f"\n**Recommendation 1: Drought-Resistant Crop Promotion**  \n"
                    f"*Target Regions*: {len(low_rain)} low-rainfall subdivisions identified  \n"
                    f"*Evidence*: Average rainfall below 800mm/year in:"
                )
                for loc, stats in low_rain[:5]:
                    self.answer_parts.append(f"  - {loc}: {stats['rainfall_avg']:.0f} mm/year")
                
                self.answer_parts.append(
                    f"\n*Proposed Action*: Incentivize cultivation of millets (ragi, jowar) and pulses "
                    f"that thrive in low-water conditions. Provide subsidies for drip irrigation infrastructure."
                )
            
            if high_rain:
                self.answer_parts.append(
                    f"\n**Recommendation 2: Water-Intensive Crop Optimization**  \n"
                    f"*Target Regions*: {len(high_rain)} high-rainfall subdivisions identified  \n"
                    f"*Evidence*: Average rainfall above 1500mm/year in:"
                )
                for loc, stats in high_rain[:5]:
                    self.answer_parts.append(f"  - {loc}: {stats['rainfall_avg']:.0f} mm/year")
                
                self.answer_parts.append(
                    f"\n*Proposed Action*: Maximize paddy (rice) cultivation and explore water-intensive "
                    f"cash crops. Invest in flood management to prevent waterlogging."
                )
        
        if self.crops:
            sorted_crops = sorted(self.crops.items(), key=lambda x: x[1]['production_total'], reverse=True)
            
            if len(sorted_crops) >= 2:
                top_district = sorted_crops[0][1]['location']
                top_crop = sorted_crops[0][1]['crop']
                top_prod = sorted_crops[0][1]['production_total']
                
                self.answer_parts.append(
                    f"\n**Recommendation 3: Best Practice Replication**  \n"
                    f"*Evidence*: {top_district} achieves highest {top_crop} production ({top_prod:.0f} tonnes)  \n"
                    f"*Proposed Action*: Conduct case study of {top_district}'s farming practices, "
                    f"seed varieties, and soil management. Disseminate learnings through agricultural extension programs."
                )
    
    def _generate_trend_answer(self):
        """Generate trend analysis."""
        if not self.rainfall:
            self.answer_parts.append(
                "Trend analysis requires time-series data. Crop datasets contain snapshot data without "
                "temporal information, making trend analysis unavailable."
            )
            return
        
        self.answer_parts.append(
            "I've analyzed long-term rainfall trends using historical meteorological data:"
        )
        
        for loc, stats in self.rainfall.items():
            entry = (
                f"\n**{loc}**  \n"
                f"- Historical Average: {stats['rainfall_avg']:.1f} mm/year  \n"
                f"- Variability Range: {stats['rainfall_min']:.1f} mm (minimum) to {stats['rainfall_max']:.1f} mm (maximum)  \n"
                f"- Coefficient of Variation: {((stats['rainfall_max'] - stats['rainfall_min']) / stats['rainfall_avg'] * 100):.1f}%  \n"
                f"- Data Period: {stats.get('years', 'Long-term record')}  \n"
                f"- Source: `{stats['source']}`"
            )
            self.answer_parts.append(entry)
    
    def _generate_identification_answer(self):
        """Generate identification answers."""
        if self.crops:
            sorted_crops = sorted(self.crops.items(), key=lambda x: x[1]['production_total'], reverse=True)
            
            if sorted_crops:
                top = sorted_crops[0][1]
                self.answer_parts.append(
                    f"Based on the analysis of district-level production data, "
                    f"**{top['location']}** has been identified as the district with the highest "
                    f"{top['crop']} production."
                )
                
                self.answer_parts.append(
                    f"\n**Production Details:**  \n"
                    f"- Total Production: **{top['production_total']:.0f} tonnes**  \n"
                    f"- Average Yield: {top['production_avg']:.0f} tonnes  \n"
                )
                
                if top.get('area'):
                    self.answer_parts.append(f"- Cultivated Area: {top['area']:.1f} hectares")
                
                self.answer_parts.append(f"- Data Source: `{top['source']}`")
                
                if len(sorted_crops) > 1:
                    bottom = sorted_crops[-1][1]
                    self.answer_parts.append(
                        f"\n*For comparison*, **{bottom['location']}** has the lowest production "
                        f"at {bottom['production_total']:.0f} tonnes."
                    )
    
    def _add_data_quality_note(self):
        """Add data quality note."""
        self.answer_parts.append("\n---\n")
        self.answer_parts.append("### Data Quality & Limitations")
        
        notes = []
        
        if self.rainfall:
            notes.append(
                "Rainfall data spans historical records (1901-2017) from India Meteorological Department, "
                "providing robust long-term climate patterns."
            )
        
        if self.crops:
            notes.append(
                "Crop production data represents snapshot measurements without year information. "
                "Temporal trends for crops cannot be established with current datasets."
            )
        
        if self.rainfall and self.crops:
            notes.append(
                "Geographic mismatches exist: rainfall data uses state-level subdivisions while "
                "crop data uses district-level granularity. Cross-referencing required fuzzy matching."
            )
        
        notes.append(
            f"Analysis completed on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}. "
            f"Data sourced from data.gov.in public datasets."
        )
        
        for note in notes:
            self.answer_parts.append(f"- {note}")
    
    def _add_citations(self):
        """Add citations."""
        self.answer_parts.append("\n---\n")
        self.answer_parts.append("### 📚 Data Sources & Citations")
        self.answer_parts.append(self.citations.formatted())