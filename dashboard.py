import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import dash
from dash import dcc, html, no_update
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from utils import age_group
from dash_bootstrap_components import Tab, Tabs
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from utils import age_group, txcurr_vf
from dash import dash_table

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
df['txcurr_pr'] = (df['curr_pr'] == 'yes').astype(int)
df['txcurr_vf'] = (df['curr_pr'] == 'yes').astype(int)
# print('vf_df DataFrame:')
# print(df)
df['latitude'] = df['latitude'].fillna(0)
df['longitude'] = df['longitude'].fillna(0)
grouped_df = df.groupby(['state', 'lga', 'facility_name', 'facility_type', 'facility_ownership', 'funder', 'latitude', 'longitude'])
grouped_counts = grouped_df.agg(
    txcurr_ndr=('txcurr_ndr', 'count'),
    txcurr_pr=('txcurr_pr', 'sum'),#lambda x: (x == 'yes').sum()),
    txcurr_vf=('txcurr_vf', 'mean')
).reset_index()
# print('grouped_counts DataFrame:')
# print(grouped_counts)
df1 = pd.DataFrame(grouped_counts)

# Define the bar_chart_age_sex function
# def bar_chart_age_sex(filtered_df):
#     yes_grouped = filtered_df[filtered_df['curr_ll'] == 'yes'].groupby(['age_group', 'sex']).size().reset_index(name='curr_ll')

#     all_age_groups = pd.DataFrame({
#         'age_group': ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
#     })

#     pivot_table = yes_grouped.pivot_table(index='age_group', columns='sex', values='curr_ll', fill_value=0).reset_index()

#     pivot_table.columns.name = None
#     pivot_table.reset_index(drop=True, inplace=True)

#     merged_grouped_data = all_age_groups.merge(pivot_table, on='age_group', how='left').fillna(0)

#     value_vars = [col for col in ['Male', 'Female'] if col in merged_grouped_data.columns]
#     melted_grouped_data = pd.melt(merged_grouped_data, id_vars=['age_group'], value_vars=value_vars, var_name='sex', value_name='curr_ll')

#     bar_chart = px.bar(melted_grouped_data, x='age_group', y='curr_ll', color='sex', text='curr_ll', title="TX_Curr by Age and Sex", labels={'age_group': 'Age Group', 'curr_ll': 'Current on Treatment', 'sex': 'Sex'})

#     return bar_chart

def bar_chart_age_sex(filtered_df):
    yes_grouped = filtered_df[filtered_df['curr_pr'] == 'yes'].groupby(['age_group', 'sex']).size().reset_index(name='curr_pr')

    all_age_groups = pd.DataFrame({
        'age_group': ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
    })

    pivot_table = yes_grouped.pivot_table(index='age_group', columns='sex', values='curr_pr', fill_value=0).reset_index()

    pivot_table.columns.name = None
    pivot_table.reset_index(drop=True, inplace=True)

    merged_grouped_data = all_age_groups.merge(pivot_table, on='age_group', how='left').fillna(0)

    fig = go.Figure()

    for sex, direction in [('Male', -1), ('Female', 1)]:
        fig.add_trace(go.Bar(y=merged_grouped_data['age_group'],
                             x=direction * merged_grouped_data.get(sex, [0]*len(merged_grouped_data)),#[sex],
                             name=sex,
                             orientation='h',
                             text=[abs(x) for x in merged_grouped_data.get(sex, [0]*len(merged_grouped_data))],
                             textposition='inside'))

    fig.update_layout(
        barmode='relative',
        title="TX_Curr by Age and Sex (Validated - Pharmacy Record)",
        xaxis=dict(title='TX_Curr'),
        yaxis=dict(title='Age Group', categoryorder='array', categoryarray=["65+", "60-64", "55-59", "50-54", "45-49", "40-44", "35-39", "30-34", "25-29", "20-24", "15-19", "10-14", "5-9", "1-4", "<1"]),
        showlegend=True,
        height=600
    )

    return fig


def bar_chart_age_sex1(filtered_df):
    yes_grouped = filtered_df[filtered_df['curr_ll'] == 'yes'].groupby(['age_group', 'sex']).size().reset_index(name='curr_ll')

    all_age_groups = pd.DataFrame({
        'age_group': ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
    })

    pivot_table = yes_grouped.pivot_table(index='age_group', columns='sex', values='curr_ll', fill_value=0).reset_index()

    pivot_table.columns.name = None
    pivot_table.reset_index(drop=True, inplace=True)

    merged_grouped_data = all_age_groups.merge(pivot_table, on='age_group', how='left').fillna(0)

    fig = go.Figure()

    for sex, direction in [('Male', -1), ('Female', 1)]:
        fig.add_trace(go.Bar(y=merged_grouped_data['age_group'],
                             x=direction * merged_grouped_data.get(sex, [0]*len(merged_grouped_data)),#[sex],
                             name=sex,
                             orientation='h',
                             #text=abs(merged_grouped_data.get(sex, [0]*len(merged_grouped_data))),#[sex]),
                             text=[abs(x) for x in merged_grouped_data.get(sex, [0]*len(merged_grouped_data))],
                             textposition='inside'))

    fig.update_layout(
        barmode='relative',
        title="TX_Curr by Age and Sex (Reported - NDR)",
        xaxis=dict(title='TX_Curr'),
        yaxis=dict(title='Age Group', categoryorder='array', categoryarray=["65+", "60-64", "55-59", "50-54", "45-49", "40-44", "35-39", "30-34", "25-29", "20-24", "15-19", "10-14", "5-9", "1-4", "<1"]),#["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]),
        showlegend=True,
        height=600
    )

    return fig


def plot_grouped_counts(grouped_counts):
    # Create a bar chart with Plotly
    fig = go.Figure()

    # Add bars for txcurr_ndr and txcurr_pr
    fig.add_trace(go.Bar(x=grouped_counts['funder'], y=grouped_counts['txcurr_ndr'], name='Txcurr NDR', yaxis='y'))
    fig.add_trace(go.Bar(x=grouped_counts['funder'], y=grouped_counts['txcurr_pr'], name='Txcurr PR', yaxis='y'))

    # Add txcurr_vf as a line plot on a secondary y-axis
    fig.add_trace(go.Scatter(x=grouped_counts['funder'], y=grouped_counts['txcurr_vf'] * 100, name='Txcurr VF (%)', yaxis='y2', mode='lines+markers'))

    # Customize the layout
    fig.update_layout(
        title='Verification Factor by Funder',
        xaxis_title='Facility Name',
        yaxis_title='Counts',
        yaxis2=dict(title='Txcurr VF (%)', overlaying='y', side='right', tickformat='.2f', showgrid=False),
        barmode='group'
    )

    # Create a Dash component for the chart
    #chart_component = dcc.Graph(id='grouped-counts-chart', figure=fig)

    return fig#chart_component

def create_table(df):
    
    return dash_table.DataTable(df.to_dict('records'), [{"name": i, "id": i} for i in df.columns],
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        }
    )

def scatter_plot_tx_age(filtered_df):
    scatter_plot = px.scatter(filtered_df, x='tx_age', y='curr_ll', title="Scatter plot of tx_age vs Tx_Curr")
    return scatter_plot

def init_dash(app):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=app, url_base_pathname='/dashboard/')

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
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                label="Verification Fcator Analytics", 
                                children=[
                                  dbc.Row([
                                        dbc.Col(html.H6("Filters", style={'color': 'white'}, className='text-center'), className="mb-3 mt-3")
                                    ]),
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
                                                        options=[{'label': i, 'value': i} for i in (['All'] + ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"])],
                                                        value=['All'],
                                                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
                                    ]),
                                    dbc.Row([
                                        dbc.Col(html.H3("Verification Factor Analytics", className='text-center'), className="mb-4 mt-4", style={'color': 'white'})
                                    ]),
                                    dbc.Row([
                                        dbc.Col(dcc.Graph(id='vf_chart'), width=6),
                                        dbc.Col(dcc.Graph(id='vf_chart1'), width=6),
                                    ]),
                                    dbc.Row([
                                        dbc.Col(dcc.Graph(id='vf_chart2'), width=6),
                                        dbc.Col(dcc.Graph(id='vf_chart3'), width=6),
                                    ]),
                                    dbc.Row([
                                        dbc.Col(dcc.Graph(id='vf_chart4'), width=6),
                                        dbc.Col(dcc.Graph(id='vf_chart5'), width=3),
                                        dbc.Col(dcc.Graph(id='vf_chart6'), width=3),
                                        dbc.Col(dcc.Graph(id='vf_chart7'), width=3),
                                        dbc.Col(dcc.Graph(id='vf_chart8'), width=3),
                                    ])
                                ]
                            ),
                            dbc.Tab(
                                label="TX_CURR Analytics",
                                children=[
                                    dbc.Row([
                                        dbc.Col(html.H6("Filters", style={'color': 'white'}, className='text-center'), className="mb-3 mt-3")
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label("State", style={'color': 'white'}),
                                            dcc.Dropdown(id='state-filter',
                                                        options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['state'].unique()))],
                                                        value=['All'],
                                                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
                                        dbc.Col([
                                            html.Label("LGA", style={'color': 'white'}),
                                            dcc.Dropdown(id='lga-filter',
                                                        options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['lga'].unique()))],
                                                        value=['All'],
                                                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
                                        dbc.Col([
                                            html.Label("Facility", style={'color': 'white'}),
                                            dcc.Dropdown(id='facility-filter',
                                                        options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['facility_name'].unique()))],
                                                        value=['All'],
                                                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
                                        dbc.Col([
                                            html.Label("Sex", style={'color': 'white'}),
                                            dcc.Dropdown(id='sex-filter',
                                                        options=[{'label': i, 'value': i} for i in (['All'] + list(merged_df['sex'].unique()))],
                                                        value=['All'],
                                                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
                                        dbc.Col([
                                            html.Label("Age Group", style={'color': 'white'}),
                                            dcc.Dropdown(id='age-group-filter',
                                                        options=[{'label': i, 'value': i} for i in (['All'] + ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"])],
                                                        value=['All'],
                                                        multi=True)], width={"xs": 6, "sm": 4, "md": 2}),
                                    ]),
                                    dbc.Row([
                                        dbc.Col(html.H3("Current on Treatment  Analytics", className='text-center'), className="mb-4 mt-4", style={'color': 'white'})
                                    ]),
                                    dbc.Row([
                                        dbc.Col(dcc.Graph(id='age_sex_chart1'), width=6),
                                        dbc.Col(dcc.Graph(id='age_sex_chart'), width=6),
                                    ]),
                                    dbc.Row([
                                        dbc.Col(dcc.Graph(id='bar-chart'), width=6),
                                        dbc.Col(dcc.Graph(id='pie-chart'), width=6),
                                    ]),
                                    dbc.Row([
                                        dbc.Col(dcc.Graph(id='line-chart'), width=6),
                                    ]),
                                ]
                            ),
                            dbc.Tab(label="Progress", children=[]),
                            dbc.Tab(label="Dashboard 3", children=[]),
                        ]
                    ),
                ]
            )
        ]
    )

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

    @app.callback(
        [Output('age_sex_chart1', 'figure'),
        Output('age_sex_chart', 'figure'),
        Output('bar-chart', 'figure'),
        Output('pie-chart', 'figure'),
        Output('line-chart', 'figure')],
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

        bar_chart = px.bar(aggregated_filtered_df, x='funder', y='count', color='curr_ll', barmode='group',
                        title="Number of cases by funder")

        pie_chart = px.pie(aggregated_filtered_df, values='count', names='facility_type', title="Proportion of validated TX_CURR by Facility Type")

        #line_chart = px.line(aggregated_filtered_df, x='count', y='count', color='facility_name', title="Cases over time")
        #datatable = txcurr_vf(merged_df=filtered_df)

        return bar_chart_age_sex1(filtered_df), bar_chart_age_sex(filtered_df), bar_chart, pie_chart,plot_grouped_counts(df1)

    @app.callback(
        [Output('vf_chart', 'figure'),
        Output('vf_chart1', 'figure'),
        Output('vf_chart2', 'figure'),
        Output('vf_chart3', 'figure'),
        Output('vf_chart4', 'figure')],
        [Input('state-filter1', 'value'),
        Input('lga-filter1', 'value'),
        Input('facility-filter1', 'value'),
        Input('sex-filter1', 'value'),
        Input('age-group-filter1', 'value'),
        ],
    )
    def update_charts1(state_filter1, lga_filter1, facility_filter1, sex_filter1, age_group_filter1):
        filtered_df = merged_df.copy()
        
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

        aggregated_filtered_df = filtered_df[filtered_df['curr_ll'] == 'yes'].groupby(['facility_name', 'state', 'lga', 'funder', 'facility_ownership', 'facility_type', 'curr_ll']).size().reset_index(name='count')

        bar_chart = px.bar(aggregated_filtered_df, x='funder', y='count', color='curr_ll', barmode='group',
                        title="Number of cases by funder")

        pie_chart = px.pie(aggregated_filtered_df, values='count', names='facility_type', title="Proportion of validated TX_CURR by Facility Type")

        #line_chart = px.line(aggregated_filtered_df, x='count', y='count', color='facility_name', title="Cases over time")
        #datatable = txcurr_vf(merged_df=filtered_df)

        return bar_chart_age_sex1(filtered_df), bar_chart_age_sex(filtered_df), bar_chart, pie_chart,plot_grouped_counts(df1)
    
    return app

    
    



    # def update_charts(state_filter, lga_filter, facility_filter, sex_filter, age_group_filter):
    #     filtered_df = merged_df.copy()

    #     if 'All' not in state_filter:
    #         filtered_df = filtered_df[filtered_df['state'].isin(state_filter)]

    #     if 'All' not in lga_filter:
    #         filtered_df = filtered_df[filtered_df['lga'].isin(lga_filter)]

    #     if 'All' not in facility_filter:
    #         filtered_df = filtered_df[filtered_df['facility_name'].isin(facility_filter)]

    #     if 'All' not in sex_filter:
    #         filtered_df = filtered_df[filtered_df['sex'].isin(sex_filter)]

    #     if 'All' not in age_group_filter:
    #         filtered_df = filtered_df[filtered_df['age_group'].isin(age_group_filter)]

    #     aggregated_filtered_df = filtered_df[filtered_df['curr_ll'] == 'yes'].groupby(['facility_name', 'curr_ll']).size().reset_index(name='count')

    #     bar_chart = px.bar(aggregated_filtered_df, x='facility_name', y='count', color='curr_ll', barmode='group',
    #                     title="Number of cases by facility")

    #     pie_chart = px.pie(aggregated_filtered_df, values='count', names='facility_name', title="Proportion of cases by facility")

    #     #line_chart = px.line(aggregated_filtered_df, x='count', y='count', color='facility_name', title="Cases over time")
    #     datatable = txcurr_vf(merged_df=filtered_df)

    #     return bar_chart_age_sex(filtered_df), bar_chart, pie_chart, display_facility_table(datatable)

    # return app

