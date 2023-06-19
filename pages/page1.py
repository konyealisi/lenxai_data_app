import dash_bootstrap_components as dbc
from dash import dcc, html
from utils import age_group
import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

from utils import *

merged_df, df1 = database_data()


layout = dbc.Container([
    # dbc.Row([
    #     dbc.Col(html.H6("Filters", style={'color': 'white'}, className='text-center'), className="mb-3 mt-3")
    # ]),
    html.Br(),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.Label("State", style={'color': 'white'}),
            dcc.Dropdown(id='state-filter1',
                        options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['state'].unique()))],
                        value=['All'],
                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
        dbc.Col([
            html.Label("LGA", style={'color': 'white'}),
            dcc.Dropdown(id='lga-filter1',
                        options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['lga'].unique()))],
                        value=['All'],
                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
        dbc.Col([
            html.Label("Facility", style={'color': 'white'}),
            dcc.Dropdown(id='facility-filter1',
                        options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['facility_name'].unique()))],
                        value=['All'],
                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
        dbc.Col([
            html.Label("Sex", style={'color': 'white'}),
            dcc.Dropdown(id='sex-filter1',
                        options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['sex'].unique()))],
                        value=['All'],
                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
        dbc.Col([
            html.Label("Age Group", style={'color': 'white'}),
            dcc.Dropdown(id='age-group-filter1',
                        options=[{'label': i,'value': i} for i in (['All'] + ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"])],
                        value=['All'],
                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
    ]),
    dbc.Row([
        dbc.Col(html.H3("Verification Factor Analytics", className='text-center'), className="mb-4 mt-4", style={'color': 'white'})
    ]),
     dbc.Row([
        dbc.Col(dcc.Graph(id='vf_map'), width=12),
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col(dcc.Graph(id='vf_bubble'), width=12),
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col(dcc.Graph(id='vf_facility'), width=12),
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col(dcc.Graph(id='vf_chart'), width=6),
        dbc.Col(dcc.Graph(id='vf_chart1'), width=6),
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col(dcc.Graph(id='vf_chart2'), width=6),
        dbc.Col(dcc.Graph(id='vf_chart3'), width=6),
    ]),
    html.Br(),
    # dbc.Row([
    #     dbc.Col(dcc.Graph(id='vf_chart4'), width=12),
    #     #dbc.Col(dcc.Graph(id='vf_chart5'), width=6),
    # ]),
    # html.Br(),
])
