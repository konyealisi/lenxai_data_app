import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots

from pages import page1, page2, page3, page4, page5, home

import os
import pandas as pd
import numpy as np
from datetime import date as d
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objs as go
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from utils import * # age_group, txcurr_vf, bar_chart_age_sex, bar_chart_age_sex1, vf_plot_funder, scatter_plot_tx_age, create_table, bar_chart, pie_chart, map_figure, vf_plot_fo, vf_plot_ft, vf_plot_ip



merged_df, df1 = database_data()
font_awesome1 = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.1/css/all.min.css'
font_awesome3 = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.1/css/solid.min.css'

def init_dash(app):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.themes.DARKLY, font_awesome1, font_awesome3], server=app, url_base_pathname='/dashboard/', title="DQA Analytics - LenxAI",  meta_tags=[{"name": "viewport", "content": "width=device-width"}])

    

    sidebar =  html.Div(
        [
            html.Div([
                html.Div([
                    html.Img(src="/assets/statistics.png", style={"width": "4.9rem"}),
                    html.H6("Analytics Dashboard", style={'color': 'white', 'margin-top': '15px'}),
                ], className='icon_title')
            ], className="sidebar-header"),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink([html.Div([
                        html.I(className="fa-solid fa-house"),
                        html.Span("Home", style={'margin-top': '3px'})], className='icon_title')],
                        href="/",
                        active="exact",
                        className="pe-3"
                    ),
                    dbc.NavLink([html.Div([
                        html.I(className="fa-solid fa-gauge"),
                        html.Span("Verification Factor Analytics", style={'margin-top': '3px'})], className='icon_title')],
                        href="/pages/page5",
                        active="exact",
                        className="pe-3"
                    ),
                    dbc.NavLink([html.Div([
                        html.I(className="fa-solid fa-gauge"),
                        html.Span("Treatment Current Analytics", style={'margin-top': '3px'})], className='icon_title')],
                        href="/pages/page2",
                        active="exact",
                        className="pe-3"
                    ),
                    dbc.NavLink([html.Div([
                        html.I(className="fa fa-shield fa-rotate-270"),
                        html.Span("Progress", style={'margin-top': '3px'})], className='icon_title')],
                        href="/pages/page3",
                        active="exact",
                        className="pe-3"
                    ),
                    dbc.NavLink([html.Div([
                        html.I(className="fa-solid fa-database"),
                        html.Span("Validation", style={'margin-top': '3px'})], className='icon_title')],
                        href="/pages/page4",
                        active="exact",
                        className="pe-3"
                    ),
                    dbc.NavLink([html.Div([
                        html.I(className="fa-solid fa-circle-info"),
                        html.Span("About", style={'margin-top': '3px'})], className='icon_title')],
                        href="/apps/about",
                        active="exact",
                        className="pe-3"
                    ),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        id="bg_id",
        className="sidebar",
    )

    content = html.Div(id="page-content", children=[], className = 'mainContainer')

    app.layout = html.Div([
        html.Div(
        html.H1("ART Data Quality Assessment Analytics Dashboard", className="header", style={'color': 'white'})
        ),
        dcc.Location(id='url', refresh=True),
        sidebar,
        content

])




    @app.callback(Output('page-content', 'children'),
                [Input('url', 'pathname')])
    def display_page(pathname):
        if pathname == '/':
            return home.layout
        elif pathname == '/pages/page1':
            return page1.layout
        elif pathname == '/pages/page2':
            return page2.layout
        elif pathname == '/pages/page3':
            return page3.layout
        elif pathname == '/pages/page4':
            return page4.layout
        elif pathname == '/pages/page5':
            return page5.layout

    
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

    # Cards
    @app.callback(
        Output('card1-content', 'children'),
        Output('card2-content', 'children'),
        Output('card3-content', 'children'),
        Output('card4-content', 'children'),
        [Input('state-filter', 'value'),
        Input('lga-filter', 'value'),
        Input('facility-filter', 'value'),
        Input('sex-filter', 'value'),
        Input('age-group-filter', 'value'),
        ]
    )
    def update_cards(state_filter, lga_filter, facility_filter, sex_filter, age_group_filter):
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

        card1_content = txcurr_ndr_card(filtered_df)
        card2_content = txcurr_cr_card(filtered_df)
        card3_content = txcurr_pr_card(filtered_df)
        card4_content = txcurr_vf_card(filtered_df)
        return html.P(f"{card1_content}", style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25}),\
                html.P(f"{card2_content}", style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25}),\
                    html.P(f"{card3_content}", style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25}),\
                        html.P(f"{card4_content*100:,.2f} %", style={'textAlign': 'center', 'color': 'orange', 'fontSize': 25})


    # # Verification Factor Analytics
    @app.callback(
        [Output('vf_funder', 'figure'),
        Output('vf_im', 'figure'),
        Output('vf_map', 'figure'),
        Output('vf_bubble', 'figure'),
        Output('vf_fo', 'figure'),
        Output('vf_ft', 'figure'),
        Output('vf_facility', 'figure')
        ],
        [Input('state-filter', 'value'),
        Input('lga-filter', 'value'),
        Input('facility-filter', 'value'),
        Input('sex-filter', 'value'),
        Input('age-group-filter', 'value'),
        ],
    )
    def update_charts1(state_filter, lga_filter, facility_filter, sex_filter, age_group_filter):
        filtered_df = df1.copy()
        
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
            
        return vf_plot_funder(filtered_df), vf_plot_ip(filtered_df), map_figure(filtered_df), bubble_chart(filtered_df), vf_plot_fo(filtered_df), vf_plot_ft(filtered_df), bar_chart_facility(filtered_df)
    

    return app

    