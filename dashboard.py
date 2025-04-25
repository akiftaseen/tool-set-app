import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from sqlalchemy import create_engine, func, text
import numpy as np
from config import DATABASE_URL

# Function to load data from database
def load_data():
    engine = create_engine(DATABASE_URL)
    themes_df = pd.read_sql('SELECT * FROM themes', engine)
    subthemes_df = pd.read_sql('SELECT * FROM subthemes', engine)
    categories_df = pd.read_sql('SELECT * FROM categories', engine)
    names_df = pd.read_sql('SELECT * FROM names', engine)
    name_categories_df = pd.read_sql('SELECT * FROM name_categories', engine)
    merged_df = name_categories_df.merge(names_df, left_on='name_id', right_on='id', suffixes=('_nc', '_name'))
    merged_df = merged_df.merge(categories_df, left_on='category_id', right_on='id', suffixes=('_name', '_cat'))
    merged_df = merged_df.merge(subthemes_df, left_on='subtheme_id', right_on='id', suffixes=('_cat', '_sub'))
    merged_df = merged_df.merge(themes_df, left_on='theme_id', right_on='id', suffixes=('_sub', '_theme'))
    data = merged_df[['name_name', 'name_cat', 'name_sub', 'name_theme']]
    data.columns = ['Name', 'Category', 'Subtheme', 'Theme']
    return data, themes_df, subthemes_df, categories_df, names_df, name_categories_df

# Create a color palette for consistent visualization
COLORS = {
    'primary': '#1f77b4',    # Blue
    'secondary': '#ff7f0e',  # Orange
    'success': '#2ca02c',    # Green
    'danger': '#d62728',     # Red
    'info': '#9467bd',       # Purple
    'warning': '#e6c700',    # Yellow
    'dark': '#7f7f7f',       # Gray
    'light': '#f0f0f0',      # Light Gray
    'background': '#ffffff', # White
    'text': '#333333'        # Dark Gray
}

# Custom theme for Plotly
custom_theme = {
    'layout': {
        'font': {'family': 'Roboto, sans-serif', 'color': COLORS['text']},
        'title': {'font': {'size': 20, 'color': COLORS['text']}},
        'paper_bgcolor': COLORS['background'],
        'plot_bgcolor': COLORS['light'],
        'colorway': [COLORS['primary'], COLORS['secondary'], COLORS['success'], 
                    COLORS['danger'], COLORS['info'], COLORS['warning']],
        'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}
    }
}

# We'll initialize the Dash app in get_dash_app() function with the Flask server
dash_app = None

# Define the layout to be used in get_dash_app()
def create_layout():
    data, themes_df, subthemes_df, categories_df, names_df, name_categories_df = load_data()
    return html.Div([
        # Navbar
        html.Nav([
            html.Div([
                html.A([
                    html.I(className='fas fa-tools me-2'),
                    'Tool Set'
                ], href='/', className='navbar-brand fw-bold'),
                html.Button([
                    html.Span(className='navbar-toggler-icon')
                ], className='navbar-toggler', **{'data-bs-toggle': 'collapse', 'data-bs-target': '#navbarNav'}),
                html.Div([
                    html.Ul([
                        html.Li(html.A([html.I(className='fas fa-home me-1'), 'Home'], href='/', className='nav-link'), className='nav-item'),
                        html.Li(html.A([html.I(className='fas fa-chart-bar me-1'), 'Dashboard'], href='/dashboard/', className='nav-link active'), className='nav-item'),
                        html.Li(html.A([html.I(className='fas fa-user-shield me-1'), 'Admin'], href='/admin', className='nav-link'), className='nav-item'),
                        html.Li(html.A([html.I(className='fas fa-sign-out-alt me-1'), 'Logout'], href='/logout', className='nav-link'), className='nav-item'),
                    ], className='navbar-nav ms-auto')
                ], className='collapse navbar-collapse', id='navbarNav')
            ], className='container-fluid')
        ], className='navbar navbar-expand-lg navbar-dark bg-primary shadow-sm mb-4'),
        
        # Header
        html.Div([
            html.H1('Tool Set Analytics Dashboard', className='text-center mb-4'),
            html.P('Interactive data visualization of tool set categories and themes', 
                    className='text-center lead text-muted mb-5')
        ], className='container'),
        
        # Summary Cards
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-layer-group fa-2x text-primary'),
                            html.Div([
                                html.H5('Total Themes', className='card-title mb-0'),
                                html.H2(f"{len(data['Theme'].unique())}", className='fs-1 fw-bold text-primary')
                            ], className='ms-3')
                        ], className='d-flex align-items-center')
                    ], className='card-body')
                ], className='card h-100 shadow-sm')
            ], className='col-md-3'),
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-sitemap fa-2x text-success'),
                            html.Div([
                                html.H5('Total Subthemes', className='card-title mb-0'),
                                html.H2(f"{len(data['Subtheme'].unique())}", className='fs-1 fw-bold text-success')
                            ], className='ms-3')
                        ], className='d-flex align-items-center')
                    ], className='card-body')
                ], className='card h-100 shadow-sm')
            ], className='col-md-3'),
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-tags fa-2x text-warning'),
                            html.Div([
                                html.H5('Total Categories', className='card-title mb-0'),
                                html.H2(f"{len(data['Category'].unique())}", className='fs-1 fw-bold text-warning')
                            ], className='ms-3')
                        ], className='d-flex align-items-center')
                    ], className='card-body')
                ], className='card h-100 shadow-sm')
            ], className='col-md-3'),
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className='fas fa-file-alt fa-2x text-info'),
                            html.Div([
                                html.H5('Total Names', className='card-title mb-0'),
                                html.H2(f"{data['Name'].nunique()}", className='fs-1 fw-bold text-info')
                            ], className='ms-3')
                        ], className='d-flex align-items-center')
                    ], className='card-body')
                ], className='card h-100 shadow-sm')
            ], className='col-md-3'),
        ], className='container row mx-auto mb-4 g-4'),
        
        # Filter Section
        html.Div([
            html.Div([
                html.Div([
                    html.H4('Data Filters', className='card-header bg-light'),
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Label('Theme', className='form-label fw-bold'),
                                dcc.Dropdown(
                                    id='theme-dropdown',
                                    options=[{'label': theme, 'value': theme} for theme in data['Theme'].unique()],
                                    placeholder='Select Theme(s)',
                                    multi=True,
                                    className='mb-3',
                                    style={'borderRadius': '8px'}
                                )
                            ], className='col-md-4'),
                            html.Div([
                                html.Label('Subtheme', className='form-label fw-bold'),
                                dcc.Dropdown(
                                    id='subtheme-dropdown',
                                    options=[{'label': sub, 'value': sub} for sub in data['Subtheme'].unique()],
                                    placeholder='Select Subtheme(s)',
                                    multi=True,
                                    className='mb-3',
                                    style={'borderRadius': '8px'}
                                )
                            ], className='col-md-4'),
                            html.Div([
                                html.Label('Category', className='form-label fw-bold'),
                                dcc.Dropdown(
                                    id='category-dropdown',
                                    options=[{'label': cat, 'value': cat} for cat in data['Category'].unique()],
                                    placeholder='Select Category(s)',
                                    multi=True,
                                    className='mb-3',
                                    style={'borderRadius': '8px'}
                                )
                            ], className='col-md-4'),
                        ], className='row g-3'),
                        html.Div([
                            html.Button([
                                html.I(className='fas fa-sync-alt me-2'),
                                'Reset Filters'
                            ], id='reset-filters', className='btn btn-outline-secondary mt-2')
                        ], className='d-flex justify-content-end')
                    ], className='card-body')
                ], className='card shadow-sm mb-4')
            ])
        ], className='container'),

        # Main Charts
        html.Div([
            # Row 1: Bar & Pie Chart
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.H5('Category Distribution', className='card-header bg-light d-flex justify-content-between align-items-center'),
                            html.Div([
                                dcc.Graph(
                                    id='bar-chart',
                                    className='mt-1',
                                    config={'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['lasso2d', 'select2d']}
                                )
                            ], className='card-body')
                        ], className='card h-100 shadow-sm')
                    ], className='col-lg-8'),
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H5('Theme Distribution', className='card-header bg-light d-flex justify-content-between align-items-center'),
                                html.Div([
                                    dcc.Graph(
                                        id='pie-chart',
                                        className='mt-1',
                                        config={'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['lasso2d', 'select2d']}
                                    )
                                ], className='card-body')
                            ], className='card h-100 shadow-sm')
                        ])
                    ], className='col-lg-4')
                ], className='row mb-4 g-4'),
                
                # Row 2: Sunburst & Heatmap
                html.Div([
                    html.Div([
                        html.Div([
                            html.H5('Hierarchy Visualization', className='card-header bg-light d-flex justify-content-between align-items-center'),
                            html.Div([
                                dcc.Graph(
                                    id='sunburst-chart',
                                    className='mt-1',
                                    config={'displayModeBar': True, 'displaylogo': False}
                                )
                            ], className='card-body')
                        ], className='card h-100 shadow-sm')
                    ], className='col-lg-6'),
                    html.Div([
                        html.Div([
                            html.H5('Name Category Associations', className='card-header bg-light d-flex justify-content-between align-items-center'),
                            html.Div([
                                dcc.Graph(
                                    id='treemap-chart',
                                    className='mt-1',
                                    config={'displayModeBar': True, 'displaylogo': False}
                                )
                            ], className='card-body')
                        ], className='card h-100 shadow-sm')
                    ], className='col-lg-6')
                ], className='row mb-4 g-4'),
                
                # Row 3: Data Table
                html.Div([
                    html.Div([
                        html.H5('Data Overview', className='card-header bg-light d-flex justify-content-between align-items-center'),
                        html.Div(id='data-table-container', className='card-body')
                    ], className='card shadow-sm')
                ], className='mb-4')
            ])
        ], className='container'),
        
        # Font Awesome for icons
        html.Link(
            rel='stylesheet',
            href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
        )
    ])

# This function will be used to register callbacks
def register_callbacks(app):
    def get_data():
        data, _, _, _, _, _ = load_data()
        return data

    # Main chart update callback
    @app.callback(
        [Output('bar-chart', 'figure'),
         Output('pie-chart', 'figure'),
         Output('treemap-chart', 'figure'),
         Output('sunburst-chart', 'figure'),
         Output('data-table-container', 'children')],
        [
            Input('theme-dropdown', 'value'),
            Input('subtheme-dropdown', 'value'),
            Input('category-dropdown', 'value'),
            Input('reset-filters', 'n_clicks')
        ],
        [State('theme-dropdown', 'value'),
         State('subtheme-dropdown', 'value'),
         State('category-dropdown', 'value')]
    )
    def update_charts(selected_themes, selected_subthemes, selected_categories, n_clicks, 
                      theme_state, subtheme_state, category_state):
        # Reset filters if button clicked
        ctx = dash.callback_context
        if ctx.triggered and 'reset-filters' in ctx.triggered[0]['prop_id']:
            selected_themes = None
            selected_subthemes = None
            selected_categories = None
            
        # Start with full dataset
        filtered_data = get_data()
        
        # Apply filters
        if selected_themes:
            filtered_data = filtered_data[filtered_data['Theme'].isin(selected_themes)]
        if selected_subthemes:
            filtered_data = filtered_data[filtered_data['Subtheme'].isin(selected_subthemes)]
        if selected_categories:
            filtered_data = filtered_data[filtered_data['Category'].isin(selected_categories)]
            
        if len(filtered_data) == 0:
            # Create empty figures if no data
            empty_message = "No data matches the selected filters. Try adjusting your selections."
            empty_layout = go.Layout(
                title=empty_message,
                font={'size': 16},
                xaxis={'visible': False},
                yaxis={'visible': False},
                plot_bgcolor=COLORS['light'],
                paper_bgcolor=COLORS['background'],
                height=350
            )
            
            empty_fig = go.Figure(layout=empty_layout)
            empty_table = html.Div([
                html.P(empty_message, className='text-center text-muted py-5')
            ])
            
            return empty_fig, empty_fig, empty_fig, empty_fig, empty_table

        # ------------------- Bar Chart -------------------
        bar_data = filtered_data.groupby('Category').size().reset_index(name='Count')
        bar_data = bar_data.sort_values('Count', ascending=False).head(15)  # Top 15 for readability
        
        bar_fig = go.Figure()
        bar_fig.add_trace(go.Bar(
            x=bar_data['Category'],
            y=bar_data['Count'],
            marker_color=COLORS['primary'],
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        ))
        
        bar_fig.update_layout(
            title={
                'text': f'Top {len(bar_data)} Categories by Name Count',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title='',
            yaxis_title='Number of Names',
            xaxis={'tickangle': -45},
            template='plotly_white',
            height=400,
            margin={'t': 80, 'l': 50, 'r': 20, 'b': 100}
        )
        
        # ------------------- Pie Chart -------------------
        pie_data = filtered_data.groupby('Theme').size().reset_index(name='Count')
        
        pie_fig = go.Figure()
        pie_fig.add_trace(go.Pie(
            labels=pie_data['Theme'],
            values=pie_data['Count'],
            hole=0.4,
            textinfo='percent+label',
            insidetextorientation='radial',
            marker=dict(
                colors=px.colors.qualitative.Pastel,
                line=dict(color='white', width=2)
            ),
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        ))
        
        pie_fig.update_layout(
            title={
                'text': 'Name Distribution by Theme',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            template='plotly_white',
            legend_title_text='Themes',
            height=400,
            margin={'t': 80, 'l': 20, 'r': 20, 'b': 20}
        )
        
        # ------------------- Treemap Chart (replacing heatmap) -------------------
        # Group data for treemap
        tree_data = filtered_data.groupby(['Theme', 'Subtheme', 'Category']).size().reset_index(name='Count')
        
        treemap_fig = px.treemap(
            tree_data, 
            path=['Theme', 'Subtheme', 'Category'], 
            values='Count',
            color='Count',
            hover_data=['Count'],
            color_continuous_scale='Blues',
            color_continuous_midpoint=np.average(tree_data['Count'])
        )
        
        treemap_fig.update_layout(
            title={
                'text': 'Category Hierarchy Tree Map',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            template='plotly_white',
            height=500,
            margin={'t': 80, 'l': 20, 'r': 20, 'b': 20}
        )
        
        # ------------------- Sunburst Chart -------------------
        sunburst_fig = px.sunburst(
            filtered_data, 
            path=['Theme', 'Subtheme', 'Category'],
            color_discrete_sequence=px.colors.qualitative.Pastel,
            branchvalues='total'
        )
        
        sunburst_fig.update_layout(
            title={
                'text': 'Hierarchical View of Categories',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            template='plotly_white',
            height=500,
            margin={'t': 80, 'l': 20, 'r': 20, 'b': 20}
        )
        
        # ------------------- Data Table -------------------
        # Get summary statistics
        summary = filtered_data.groupby(['Theme', 'Subtheme', 'Category']).agg(
            Name_Count=pd.NamedAgg(column='Name', aggfunc='nunique')
        ).reset_index().sort_values('Name_Count', ascending=False).head(10)
        
        # Create table for data overview
        table = html.Table([
            # Header
            html.Thead(
                html.Tr([
                    html.Th('Theme', className='text-center'),
                    html.Th('Subtheme', className='text-center'),
                    html.Th('Category', className='text-center'),
                    html.Th('Name Count', className='text-center')
                ], className='table-light')
            ),
            # Body
            html.Tbody([
                html.Tr([
                    html.Td(row['Theme']),
                    html.Td(row['Subtheme']),
                    html.Td(row['Category']),
                    html.Td(row['Name_Count'], className='text-center')
                ]) for _, row in summary.iterrows()
            ])
        ], className='table table-striped table-hover table-bordered')
        
        # Add a title above the table
        table_section = html.Div([
            html.H6('Top 10 Categories by Name Count', className='text-muted mb-3'),
            table
        ])

        return bar_fig, pie_fig, treemap_fig, sunburst_fig, table_section

    # Callback to update subtheme dropdown options based on selected themes
    @app.callback(
        [Output('subtheme-dropdown', 'options'),
         Output('subtheme-dropdown', 'value')],
        [Input('theme-dropdown', 'value'),
         Input('reset-filters', 'n_clicks')],
        [State('subtheme-dropdown', 'value')]
    )
    def update_subtheme_options(selected_themes, n_clicks, current_value):
        ctx = dash.callback_context
        if ctx.triggered and 'reset-filters' in ctx.triggered[0]['prop_id']:
            df = get_data()
            subthemes = df['Subtheme'].unique()
            return [{'label': sub, 'value': sub} for sub in subthemes], None
            
        df = get_data()
        if selected_themes:
            df = df[df['Theme'].isin(selected_themes)]
            
        subthemes = df['Subtheme'].unique()
        options = [{'label': sub, 'value': sub} for sub in subthemes]
            
        # Keep only the valid values based on the current filter
        filtered_values = []
        if current_value:
            filtered_values = [val for val in current_value if val in subthemes]
            
        return options, filtered_values

    # Callback to update category dropdown options based on selected themes and subthemes
    @app.callback(
        [Output('category-dropdown', 'options'),
         Output('category-dropdown', 'value')],
        [Input('theme-dropdown', 'value'),
         Input('subtheme-dropdown', 'value'),
         Input('reset-filters', 'n_clicks')],
        [State('category-dropdown', 'value')]
    )
    def update_category_options(selected_themes, selected_subthemes, n_clicks, current_value):
        ctx = dash.callback_context
        if ctx.triggered and 'reset-filters' in ctx.triggered[0]['prop_id']:
            df = get_data()
            categories = df['Category'].unique()
            return [{'label': cat, 'value': cat} for cat in categories], None
            
        df = get_data()
        if selected_themes:
            df = df[df['Theme'].isin(selected_themes)]
        if selected_subthemes:
            df = df[df['Subtheme'].isin(selected_subthemes)]
            
        categories = df['Category'].unique()
        options = [{'label': cat, 'value': cat} for cat in categories]
        
        # Keep only the valid values based on the current filter
        filtered_values = []
        if current_value:
            filtered_values = [val for val in current_value if val in categories]
            
        return options, filtered_values

# Function to get dash app
def get_dash_app():
    global dash_app
    if dash_app is None:
        # Add Bootstrap 5 CSS and JS
        external_stylesheets = [
            'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
            'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap'
        ]
        external_scripts = [
            'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
            'https://kit.fontawesome.com/a076d05399.js'
        ]
        
        dash_app = dash.Dash(
            __name__,
            url_base_pathname='/dashboard/',
            external_stylesheets=external_stylesheets,
            external_scripts=external_scripts,
            suppress_callback_exceptions=True
        )
        
        # Apply custom theme
        dash_app._theme = custom_theme
        dash_app.layout = create_layout()
        register_callbacks(dash_app)
        
    return dash_app
