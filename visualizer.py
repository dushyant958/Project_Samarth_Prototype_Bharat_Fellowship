# visualizer.py
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class DataVisualizer:
    """Creates sophisticated visualizations for agricultural data."""
    
    def __init__(self, parsed_query, rainfall_results, crop_results, summary):
        self.parsed = parsed_query
        self.rainfall = rainfall_results
        self.crops = crop_results
        self.summary = summary
        
    def create_visualizations(self):
        """Generate visualizations based on query type."""
        figures = []
        action = self.parsed.get('action', 'compare')
        
        if action in ['top', 'bottom']:
            figures.extend(self._create_ranking_charts())
        elif action == 'compare':
            figures.extend(self._create_comparison_charts())
        elif action == 'correlate':
            figures.extend(self._create_correlation_charts())
        elif action == 'trend':
            figures.extend(self._create_trend_charts())
        elif action == 'recommend':
            figures.extend(self._create_recommendation_charts())
        else:
            figures.extend(self._create_comparison_charts())
        
        return figures
    
    def _create_ranking_charts(self):
        """Create ranking visualizations."""
        figures = []
        
        # Rainfall ranking
        if self.rainfall:
            df_rain = pd.DataFrame([
                {
                    'Location': loc,
                    'Average Rainfall (mm)': stats['rainfall_avg'],
                    'Min': stats['rainfall_min'],
                    'Max': stats['rainfall_max'],
                    'Data Points': stats['data_points']
                }
                for loc, stats in self.rainfall.items()
            ])
            
            df_rain = df_rain.sort_values('Average Rainfall (mm)', 
                                          ascending=(self.parsed.get('action') == 'bottom'))
            
            # Horizontal bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                y=df_rain['Location'],
                x=df_rain['Average Rainfall (mm)'],
                orientation='h',
                marker=dict(
                    color=df_rain['Average Rainfall (mm)'],
                    colorscale='Blues',
                    showscale=True,
                    colorbar=dict(title="Rainfall (mm)")
                ),
                text=df_rain['Average Rainfall (mm)'].round(1),
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>' +
                             'Average: %{x:.1f} mm<br>' +
                             '<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"{'Top' if self.parsed.get('action') == 'top' else 'Bottom'} {len(df_rain)} Regions by Average Rainfall",
                xaxis_title="Average Annual Rainfall (mm)",
                yaxis_title="Subdivision",
                height=max(400, len(df_rain) * 40),
                template='plotly_white',
                font=dict(size=12),
                showlegend=False
            )
            
            figures.append(('rainfall_ranking', fig))
            
            # Variability chart
            fig2 = go.Figure()
            
            for idx, row in df_rain.iterrows():
                fig2.add_trace(go.Scatter(
                    x=[row['Location'], row['Location'], row['Location']],
                    y=[row['Min'], row['Average Rainfall (mm)'], row['Max']],
                    mode='lines+markers',
                    name=row['Location'],
                    marker=dict(size=[8, 12, 8], color='steelblue'),
                    line=dict(width=2, color='steelblue'),
                    showlegend=False
                ))
            
            fig2.update_layout(
                title="Rainfall Variability Range (Min-Avg-Max)",
                xaxis_title="Region",
                yaxis_title="Rainfall (mm)",
                height=400,
                template='plotly_white'
            )
            
            figures.append(('rainfall_variability', fig2))
        
        # Crop ranking
        if self.crops:
            df_crop = pd.DataFrame([
                {
                    'Location': stats['location'],
                    'Crop': stats['crop'].title(),
                    'Production (tonnes)': stats['production_total'],
                    'Area (hectares)': stats.get('area', 0)
                }
                for key, stats in self.crops.items()
            ])
            
            df_crop = df_crop.sort_values('Production (tonnes)', 
                                          ascending=(self.parsed.get('action') == 'bottom'))
            
            # Production bar chart
            fig = px.bar(
                df_crop,
                x='Location',
                y='Production (tonnes)',
                color='Crop',
                title=f"{'Top' if self.parsed.get('action') == 'top' else 'Bottom'} Districts by Crop Production",
                text='Production (tonnes)',
                height=500
            )
            
            fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            fig.update_layout(template='plotly_white', xaxis_tickangle=-45)
            
            figures.append(('crop_production', fig))
            
            # Area vs Production scatter
            if df_crop['Area (hectares)'].sum() > 0:
                fig2 = px.scatter(
                    df_crop,
                    x='Area (hectares)',
                    y='Production (tonnes)',
                    size='Production (tonnes)',
                    color='Crop',
                    hover_name='Location',
                    title='Crop Production Efficiency: Area vs Output',
                    height=500
                )
                
                fig2.update_layout(template='plotly_white')
                figures.append(('production_efficiency', fig2))
        
        return figures
    
    def _create_comparison_charts(self):
        """Create comparison visualizations."""
        figures = []
        
        if self.rainfall and not self.crops:
            # Rainfall comparison
            df = pd.DataFrame([
                {
                    'Location': loc,
                    'Average': stats['rainfall_avg'],
                    'Min': stats['rainfall_min'],
                    'Max': stats['rainfall_max']
                }
                for loc, stats in self.rainfall.items()
            ])
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Average Rainfall',
                x=df['Location'],
                y=df['Average'],
                marker_color='steelblue'
            ))
            
            fig.update_layout(
                title='Rainfall Comparison Across Regions',
                xaxis_title='Region',
                yaxis_title='Annual Rainfall (mm)',
                template='plotly_white',
                height=500,
                xaxis_tickangle=-45
            )
            
            figures.append(('rainfall_comparison', fig))
            
        elif self.crops and not self.rainfall:
            # Crop comparison
            df = pd.DataFrame([
                {
                    'Location': stats['location'],
                    'Crop': stats['crop'].title(),
                    'Production': stats['production_total'],
                    'Area': stats.get('area', 0)
                }
                for key, stats in self.crops.items()
            ])
            
            fig = px.bar(
                df,
                x='Location',
                y='Production',
                color='Crop',
                title='Crop Production Comparison',
                height=500,
                text='Production'
            )
            
            fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            fig.update_layout(template='plotly_white', xaxis_tickangle=-45)
            
            figures.append(('crop_comparison', fig))
            
        else:
            # Cross-domain comparison
            rain_data = []
            crop_data = []
            
            for loc, stats in self.rainfall.items():
                rain_data.append({
                    'Location': loc,
                    'Value': stats['rainfall_avg'],
                    'Type': 'Rainfall (mm)'
                })
            
            for key, stats in self.crops.items():
                crop_data.append({
                    'Location': stats['location'],
                    'Value': stats['production_total'],
                    'Type': f"{stats['crop'].title()} Production (tonnes)"
                })
            
            if rain_data:
                df_rain = pd.DataFrame(rain_data)
                fig1 = px.bar(
                    df_rain,
                    x='Location',
                    y='Value',
                    title='Rainfall Distribution',
                    height=400
                )
                fig1.update_layout(template='plotly_white', xaxis_tickangle=-45)
                figures.append(('rainfall_dist', fig1))
            
            if crop_data:
                df_crop = pd.DataFrame(crop_data)
                fig2 = px.bar(
                    df_crop,
                    x='Location',
                    y='Value',
                    color='Type',
                    title='Crop Production Distribution',
                    height=400
                )
                fig2.update_layout(template='plotly_white', xaxis_tickangle=-45)
                figures.append(('crop_dist', fig2))
        
        return figures
    
    def _create_correlation_charts(self):
        """Create correlation visualizations."""
        figures = []
        
        if not (self.rainfall and self.crops):
            return figures
        
        # Match data points
        matched_data = []
        for rain_loc, rain_stats in self.rainfall.items():
            for crop_key, crop_stats in self.crops.items():
                if rain_loc.lower() in crop_stats['location'].lower() or \
                   crop_stats['location'].lower() in rain_loc.lower():
                    matched_data.append({
                        'Location': rain_loc,
                        'Rainfall': rain_stats['rainfall_avg'],
                        'Production': crop_stats['production_total'],
                        'Crop': crop_stats['crop'].title()
                    })
        
        if len(matched_data) >= 3:
            df = pd.DataFrame(matched_data)
            
            # Scatter plot with trendline
            fig = px.scatter(
                df,
                x='Rainfall',
                y='Production',
                size='Production',
                color='Crop',
                hover_name='Location',
                title='Correlation: Rainfall vs Crop Production',
                trendline='ols',
                height=600
            )
            
            fig.update_layout(
                xaxis_title='Average Annual Rainfall (mm)',
                yaxis_title='Total Production (tonnes)',
                template='plotly_white'
            )
            
            figures.append(('correlation_scatter', fig))
            
            # Correlation heatmap (if multiple crops)
            if len(df['Crop'].unique()) > 1:
                pivot = df.pivot_table(
                    values='Production',
                    index='Location',
                    columns='Crop',
                    aggfunc='mean'
                )
                
                fig2 = px.imshow(
                    pivot.corr(),
                    title='Crop Production Correlation Matrix',
                    color_continuous_scale='RdBu_r',
                    height=500
                )
                
                figures.append(('correlation_matrix', fig2))
        
        return figures
    
    def _create_trend_charts(self):
        """Create trend visualizations (mainly for rainfall)."""
        figures = []
        
        # Note: Detailed trend requires raw time-series data
        # For now, we show variability
        
        if self.rainfall:
            df = pd.DataFrame([
                {
                    'Location': loc,
                    'Average': stats['rainfall_avg'],
                    'Min': stats['rainfall_min'],
                    'Max': stats['rainfall_max'],
                    'Range': stats['rainfall_max'] - stats['rainfall_min']
                }
                for loc, stats in self.rainfall.items()
            ])
            
            # Box plot style visualization
            fig = go.Figure()
            
            for idx, row in df.iterrows():
                fig.add_trace(go.Box(
                    name=row['Location'],
                    y=[row['Min'], row['Average'], row['Max']],
                    boxmean=True,
                    marker_color='steelblue'
                ))
            
            fig.update_layout(
                title='Rainfall Variability Across Regions',
                yaxis_title='Rainfall (mm)',
                template='plotly_white',
                height=500,
                showlegend=False
            )
            
            figures.append(('rainfall_trend', fig))
        
        return figures
    
    def _create_recommendation_charts(self):
        """Create recommendation visualizations."""
        figures = []
        
        if self.rainfall:
            # Classify regions
            df = pd.DataFrame([
                {
                    'Location': loc,
                    'Rainfall': stats['rainfall_avg'],
                    'Category': 'Low (<800mm)' if stats['rainfall_avg'] < 800 
                               else 'High (>1500mm)' if stats['rainfall_avg'] > 1500 
                               else 'Moderate (800-1500mm)'
                }
                for loc, stats in self.rainfall.items()
            ])
            
            # Pie chart of categories
            category_counts = df['Category'].value_counts()
            
            fig = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title='Regional Classification by Rainfall',
                height=500,
                color_discrete_map={
                    'Low (<800mm)': '#ff9999',
                    'Moderate (800-1500mm)': '#ffcc99',
                    'High (>1500mm)': '#99ccff'
                }
            )
            
            figures.append(('rainfall_categories', fig))
            
            # Bar chart by category
            fig2 = px.bar(
                df.sort_values('Rainfall'),
                x='Location',
                y='Rainfall',
                color='Category',
                title='Rainfall Distribution by Region and Category',
                height=500
            )
            
            fig2.update_layout(template='plotly_white', xaxis_tickangle=-45)
            figures.append(('rainfall_by_category', fig2))
        
        if self.crops:
            # Production leaders
            df = pd.DataFrame([
                {
                    'District': stats['location'],
                    'Crop': stats['crop'].title(),
                    'Production': stats['production_total']
                }
                for key, stats in self.crops.items()
            ])
            
            fig = px.treemap(
                df,
                path=['Crop', 'District'],
                values='Production',
                title='Crop Production Distribution (Best Practices)',
                height=600
            )
            
            figures.append(('production_treemap', fig))
        
        return figures