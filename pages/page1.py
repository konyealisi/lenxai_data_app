import dash_bootstrap_components as dbc
from dash import dcc, html
from utils import age_group
import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# # Database connection settings
# db_user = os.environ.get('DB_USER_ndqadata')
# db_password = os.environ.get('DB_PASSWORD_ndqadata')
# db_host = os.environ.get('DB_HOST_ndqadata')
# db_name = os.environ.get('DB_NAME_ndqadata')

# Load database connection details from JSON file
secrets_file = 'C:/Users/konye/Documents/mydoc.json'
try:
    with open(secrets_file) as f:
        secrets = json.load(f)
except FileNotFoundError:
    print(f"Error: {secrets_file} not found.")
    exit(1)

db_user = secrets.get('db_user', None)
db_password = secrets.get('db_password', None)
db_host = secrets.get('db_host', None)
db_name = secrets.get('db_name', None)

# Check if any of the required values are missing
if None in (db_user, db_password, db_host, db_name):
    print("Error: Missing database configuration values in the JSON file.")
    exit(1)

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


layout = dbc.Container([
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
