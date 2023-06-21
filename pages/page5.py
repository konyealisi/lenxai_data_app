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
# print('merged df')

# print(merged_df)
layout = html.Div([
            html.Div([
                html.Div(
            [
                html.H6(
                    children='Reported - NDR',
                    style={'textAlign': 'center', 'color': 'white', 'fontSize': 18}
                ),
                # The paragraph element that will be updated by the callback function
                html.P(id='card1-content',
                    style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25}),
            ],
            id='card1',
            className="card_container two columns"
        ),

        html.Div(
        [
            html.H6(
                children='Verified - Clients Folder',
                style={'textAlign': 'center', 'color': 'white', 'fontSize': 18}
            ),
            # The paragraph element that will be updated by the callback function
            html.P(id='card2-content',
                style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25}),
        ],
        id='card2',
        className="card_container two columns"
    )
    ,

        html.Div(
        [
            html.H6(
                children='Verified - Pharmacy Record',
                style={'textAlign': 'center', 'color': 'white', 'fontSize': 18}
            ),
            # The paragraph element that will be updated by the callback function
            html.P(id='card3-content',
                style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25}),
        ],
        id='card3',
        className="card_container two columns"
    )
    ,
        html.Div(
        [
            html.H6(
                children='Verification Factor',
                style={'textAlign': 'center', 'color': 'white', 'fontSize': 18}
            ),
            # The paragraph element that will be updated by the callback function
            html.P(id='card4-content',
                style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25}),
        ],
        id='card4',
        className="card_container two columns"
        )
        ,

        html.Div(
        [
            html.H6(
                children='VF Pregnant Women',
                style={'textAlign': 'center', 'color': 'white', 'fontSize': 18}
            ),
            # The paragraph element that will be updated by the callback function
            html.P(id='card5-content',
                style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25}),
        ],
        id='card5',
        className="card_container two columns"
    )], 
    className="row flex-display"),

    html.Div([
        html.Div([

            html.P('Select State:', className='fix_label',  style={'color': 'white'}),
            dbc.Col(dcc.Dropdown(id='state-filter',
                                 options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['state'].unique()))],
                                 value=['All'],
                                 multi=True), width={"xs": 6, "sm": 4, "md": 2}),

            html.P('Select LGA:', className='fix_label',  style={'color': 'white'}),
            dbc.Col(dcc.Dropdown(id='lga-filter',
                                 options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['lga'].unique()))],
                                 value=['All'],
                                 multi=True), width={"xs": 6, "sm": 4, "md": 2}),

            html.P('Select Facility:', className='fix_label',  style={'color': 'white'}),
            dbc.Col(dcc.Dropdown(id='facility-filter',
                                 options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['facility_name'].unique()))],
                                 value=['All'],
                                 multi=True), width={"xs": 6, "sm": 4, "md": 2}),                                 
            html.P('Select Sex:', className='fix_label',  style={'color': 'white'}),
            dbc.Col(dcc.Dropdown(id='sex-filter',
                                 options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['sex'].unique()))],
                                 value=['All'],
                                 multi=True), width={"xs": 6, "sm": 4, "md": 2}),

            html.P('Select Age Group:', className='fix_label',  style={'color': 'white'}),
            dbc.Col(dcc.Dropdown(id='age-group-filter',
                                options=[{'label': i,'value': i} for i in (['All'] + ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"])],
                                value=['All'],
                                 multi=True), width={"xs": 6, "sm": 4, "md": 2}),

        ], className="create_container two columns", id="cross-filter-options"),

        html.Div([
            dcc.Graph(id='vf_funder')],className="create_container three columns"),

        html.Div([
            dcc.Graph(id='vf_fo')],className="create_container three columns"),

        html.Div([
            dcc.Graph(id="vf_ft")], className="create_container three columns"),
    ], className="row flex-display"),

    html.Div([
        html.Div([
            dcc.Graph(id='vf_im')],className="create_container four columns"),

        html.Div([
            dcc.Graph(id='vf_map')],className="create_container seven columns"),
    ], className="row flex-display"),

    html.Div([
        html.Div([
            dcc.Graph(id='vf_facility')],className="create_container four columns"),

        html.Div([
            dcc.Graph(id='vf_bubble')],className="create_container seven columns"),
    ], className="row flex-display"),
], id="mainContainer", style={"display": "flex", "flex-direction": "column"})
