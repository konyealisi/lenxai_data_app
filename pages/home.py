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
    html.Br(),
    html.Br(),
    html.Hr()

])