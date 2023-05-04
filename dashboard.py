import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from pages import page1, page2, page3, page4, page5

import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from utils import * # age_group, txcurr_vf, bar_chart_age_sex, bar_chart_age_sex1, vf_plot_funder, scatter_plot_tx_age, create_table, bar_chart, pie_chart, map_figure, vf_plot_fo, vf_plot_ft, vf_plot_ip



# Database connection settings
db_user = os.environ.get('DB_USER_ndqadata')
db_password = os.environ.get('DB_PASSWORD_ndqadata')
db_host = os.environ.get('DB_HOST_ndqadata')
db_name = os.environ.get('DB_NAME_ndqadata')

# Connect to the database
db_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# Load DataEntry data
data_entry_query = text("SELECT * FROM data_entry")
data_entry_result = session.execute(data_entry_query)
data_entry_df = pd.DataFrame(data_entry_result.fetchall(), columns=data_entry_result.keys())

# Load Facility data
facility_query = text("SELECT * FROM facility")
facility_result = session.execute(facility_query)
facility_df = pd.DataFrame(facility_result.fetchall(), columns=facility_result.keys())

# Merge the facility table with the data_entry table on facility_name
merged_df = data_entry_df.merge(facility_df, on='facility_name', how='left')
merged_df['age_group'] = merged_df['age'].apply(age_group)
merged_df['curr_ll'] = merged_df['curr_ll'].str.lower().str.strip()
merged_df['curr_cr'] = merged_df['curr_cr'].str.lower().str.strip()
merged_df['curr_pr'] = merged_df['curr_pr'].str.lower().str.strip()

vf_df = merged_df[(merged_df['curr_ll'] == 'yes') & (merged_df['curr_pr'].isin(['yes', 'no']))]
df =vf_df.copy()
df['txcurr_ndr'] = (df['curr_ll'] == 'yes').astype(int)
df['txcurr_cr'] = (df['curr_cr'] == 'yes').astype(int)
df['txcurr_pr'] = (df['curr_pr'] == 'yes').astype(int)
df['txcurr_vf'] = (df['curr_pr'] == 'yes').astype(int)
# print('vf_df DataFrame:')
# print(df)
df['latitude'] = df['latitude'].fillna(0)
df['longitude'] = df['longitude'].fillna(0)
grouped_df = df.groupby(['state', 'lga', 'facility_name', 'facility_type', 'facility_ownership', 'implementing_partner', 'funder', 'latitude', 'longitude'])
grouped_counts = grouped_df.agg(
    txcurr_ndr=('txcurr_ndr', 'count'),
    txcurr_cr=('txcurr_cr', 'sum'),
    txcurr_pr=('txcurr_pr', 'sum'),#lambda x: (x == 'yes').sum()),
    txcurr_vf=('txcurr_vf', 'mean')
).reset_index()
print('grouped_counts DataFrame:')
print(grouped_counts)
df1 = pd.DataFrame(grouped_counts)

def init_dash(app):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=app, url_base_pathname='/dashboard/', title="DQA Analytics - LenxAI")

    app.layout = html.Div(
        style={"backgroundColor": "#104888"},
        children=[
            dbc.Container(
                [
                    
                    dbc.Row(
                        [
                            dbc.Col(
                                html.H1("ART Data Quality Assessment Analytics Dashboard", className="text-center", style={'color': 'white'}),
                                className="mb-5 mt-5",
                            )
                        ]
                    ),
                    dbc.Row([
            dbc.Col(
                dbc.Tabs(id='tabs', active_tab='tab-1', children=[
                    dbc.Tab(label='Verification Factor', tab_id='tab-1', label_style={'font-weight': 'bold', 'color': 'orange'}),
                    dbc.Tab(label='Treatment Current', tab_id='tab-2', label_style={'font-weight': 'bold', 'color': 'orange'}),
                    dbc.Tab(label='Progress', tab_id='tab-3', label_style={'font-weight': 'bold', 'color': 'orange'}),
                    dbc.Tab(label='Page 4', tab_id='tab-4', label_style={'font-weight': 'bold', 'color': 'orange'}),
                    dbc.Tab(label='Page 5', tab_id='tab-5', label_style={'font-weight': 'bold', 'color': 'orange'})
                ]),
                width={'size': 6, 'offset': 3},
                lg={'size': 6, 'offset': 3}
            )
        ]),
        dbc.Row([
            dbc.Col(id='page-content')
        ])
    ])
        ])
    

    @app.callback(Output('page-content', 'children'),
                Input('tabs', 'active_tab'))
    def render_content(active_tab):
        if active_tab == 'tab-1':
            return page1.layout
        elif active_tab == 'tab-2':
            return page2.layout
        elif active_tab == 'tab-3':
            return page3.layout
        elif active_tab == 'tab-4':
            return page4.layout
        elif active_tab == 'tab-5':
            return page5.layout
    
    @app.callback(
        Output('lga-filter1', 'options'),
        Input('state-filter1', 'value')
    )
    def update_lga_options1(selected_state):
        if 'All' in selected_state or not selected_state:
            options = [{'label': i, 'value': i} for i in (['All'] + list(merged_df['lga'].unique()))]
        else:
            options = [{'label': i, 'value': i} for i in (['All'] + list(merged_df[merged_df['state'].isin(selected_state)]['lga'].unique()))]
        return options

    @app.callback(
        Output('facility-filter1', 'options'),
        Input('state-filter1', 'value'),
        Input('lga-filter1', 'value')
    )
    def update_facility_options1(selected_state, selected_lga):
        filtered_df = merged_df
        if 'All' not in selected_state and selected_state:
            filtered_df = filtered_df[filtered_df['state'].isin(selected_state)]
        if 'All' not in selected_lga and selected_lga:
            filtered_df = filtered_df[filtered_df['lga'].isin(selected_lga)]
        options = [{'label': i, 'value': i} for i in (['All'] + list(filtered_df['facility_name'].unique()))]
        return options
    
    @app.callback(
        Output('lga-filter', 'options'),
        Input('state-filter', 'value')
    )
    def update_lga_options(selected_state):
        if 'All' in selected_state or not selected_state:
            options = [{'label': i, 'value': i} for i in (['All'] + list(merged_df['lga'].unique()))]
        else:
            options = [{'label': i, 'value': i} for i in (['All'] + list(merged_df[merged_df['state'].isin(selected_state)]['lga'].unique()))]
        return options

    @app.callback(
        Output('facility-filter', 'options'),
        Input('state-filter', 'value'),
        Input('lga-filter', 'value')
    )
    def update_facility_options(selected_state, selected_lga):
        filtered_df = merged_df
        if 'All' not in selected_state and selected_state:
            filtered_df = filtered_df[filtered_df['state'].isin(selected_state)]
        if 'All' not in selected_lga and selected_lga:
            filtered_df = filtered_df[filtered_df['lga'].isin(selected_lga)]
        options = [{'label': i, 'value': i} for i in (['All'] + list(filtered_df['facility_name'].unique()))]
        return options

    #Treatment Current Analytics
    @app.callback(
        [Output('age_sex_chart1', 'figure'),
        Output('age_sex_chart', 'figure'),
        Output('bar-chart', 'figure'),
        Output('pie-chart', 'figure'),
        # Output('line-chart', 'figure')
        ],
        [Input('state-filter', 'value'),
        Input('lga-filter', 'value'),
        Input('facility-filter', 'value'),
        Input('sex-filter', 'value'),
        Input('age-group-filter', 'value'),
        ],
    )
    def update_charts(state_filter, lga_filter, facility_filter, sex_filter, age_group_filter):
        filtered_df = merged_df.copy()

        if 'All' not in state_filter:
            filtered_df = filtered_df[filtered_df['state'].isin(state_filter)]

        if 'All' not in lga_filter:
            filtered_df = filtered_df[filtered_df['lga'].isin(lga_filter)]

        if 'All' not in facility_filter:
            filtered_df = filtered_df[filtered_df['facility_name'].isin(facility_filter)]

        if 'All' not in sex_filter:
            filtered_df = filtered_df[filtered_df['sex'].isin(sex_filter)]

        if 'All' not in age_group_filter:
            filtered_df = filtered_df[filtered_df['age_group'].isin(age_group_filter)]

        aggregated_filtered_df = filtered_df[filtered_df['curr_ll'] == 'yes'].groupby(['facility_name', 'state', 'lga', 'funder', 'facility_ownership', 'facility_type', 'curr_ll']).size().reset_index(name='count')


        
        return bar_chart_age_sex1(filtered_df), bar_chart_age_sex(filtered_df), bar_chart(aggregated_filtered_df), pie_chart(aggregated_filtered_df)#,plot_grouped_counts(df1)

    # Verification Factor Analytics
    @app.callback(
        [Output('vf_chart', 'figure'),
        Output('vf_chart1', 'figure'),
        Output('vf_map', 'figure'),
        Output('vf_bubble', 'figure'),
        Output('vf_chart3', 'figure'),
        Output('vf_chart2', 'figure'),
        Output('vf_facility', 'figure')
        ],
        [Input('state-filter1', 'value'),
        Input('lga-filter1', 'value'),
        Input('facility-filter1', 'value'),
        Input('sex-filter1', 'value'),
        Input('age-group-filter1', 'value'),
        ],
    )
    def update_charts1(state_filter1, lga_filter1, facility_filter1, sex_filter1, age_group_filter1):
        filtered_df = df1.copy()
        
        if 'All' not in state_filter1:
            filtered_df = filtered_df[filtered_df['state'].isin(state_filter1)]

        if 'All' not in lga_filter1:
            filtered_df = filtered_df[filtered_df['lga'].isin(lga_filter1)]

        if 'All' not in facility_filter1:
            filtered_df = filtered_df[filtered_df['facility_name'].isin(facility_filter1)]

        if 'All' not in sex_filter1:
            filtered_df = filtered_df[filtered_df['sex'].isin(sex_filter1)]

        if 'All' not in age_group_filter1:
            filtered_df = filtered_df[filtered_df['age_group'].isin(age_group_filter1)]

        
        return vf_plot_funder(filtered_df), vf_plot_ip(filtered_df), map_figure(filtered_df), bubble_chart(filtered_df), vf_plot_fo(filtered_df), vf_plot_ft(filtered_df), bar_chart_facility(filtered_df)
    
    return app

    #return app