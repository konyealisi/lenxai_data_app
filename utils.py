# utils.py
from wtforms.validators import  ValidationError
from models import User, DataEntry, Facility
from datetime import timedelta, date
import plotly.express as px
import plotly.graph_objs as go
from dash import dash_table
import seaborn as sns
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

import pandas as pd, numpy as np

def facility_choices():
    facilities = DataEntry.query.with_entities(DataEntry.facility_name, DataEntry.facility_name).distinct().all()
    return facilities

def client_choices():
    clients = DataEntry.query.with_entities(DataEntry.client_id, DataEntry.client_id).distinct().all()
    return clients

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'xml', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_dataframe(df):
    # Trim column names, convert to lowercase, and replace spaces with underscores
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Trim all string values in the DataFrame
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    return df

def calculate_age(ndate, benchmark_date):
    n = benchmark_date.year - ndate.year - ((benchmark_date.month, benchmark_date.day) < (ndate.month, ndate.day))
    return n

def calculate_age_in_months(ndate, benchmark_date):
    years_difference = benchmark_date.year - ndate.year
    months_difference = benchmark_date.month - ndate.month
    days_difference = benchmark_date.day - ndate.day

    age_in_months = years_difference * 12 + months_difference

    if days_difference < 0:
        age_in_months -= 1

    return age_in_months

# Validate username - checks if a username already exist
def validate_username(form, field):
    username = field.data
    user = User.query.filter_by(username=username).first()
    if user:
        raise ValidationError('Username is already taken.')

def validate_email(form, field):
    email = field.data
    user = User.query.filter_by(email=email).first()
    if user:
        raise ValidationError('Email is already taken.')
    
def entry_exists(client_id, facility_name):
    existing_entry = DataEntry.query.filter_by(client_id=client_id, facility_name=facility_name).first()
    return existing_entry is not None

def facility_exists(facility_name):
    existing_facility = Facility.query.filter_by(facility_name=facility_name).first()
    return existing_facility is not None

# def curr(last_pickup_date, cutoff, grace_period):
#     grace_period_timedelta = timedelta(days=grace_period)
#     if last_pickup_date + grace_period_timedelta >= cutoff:
#         return 'yes'
#     else:
#         return 'no'
    
# def curr(last_pickup_date, months_of_arv_refill, cutoff, grace_period):
#     if last_pickup_date is None:
#         return None  # or any default value you want to return when last_pickup_date is None

#     qdrugs = months_of_arv_refill*30
#     months_of_arv_refill_t = timedelta(days=qdrugs)

#     grace_period_timedelta = timedelta(days=grace_period)

#     if last_pickup_date + months_of_arv_refill_t + grace_period_timedelta >= cutoff: #if last_pickup_date + months_of_arv_refill_t + grace_period_timedelta >= pd.Timestamp(cutoff): #
#         return "yes"
#     else:
#         return "no"
# def curr(last_pickup_date, months_of_arv_refill, cutoff, grace_period):
#     if last_pickup_date is None:
#         return None  # or any default value you want to return when last_pickup_date is None

#     qdrugs = months_of_arv_refill*30
#     months_of_arv_refill_t = timedelta(days=qdrugs)

#     grace_period_timedelta = timedelta(days=grace_period)

#     if pd.Timestamp(last_pickup_date) + months_of_arv_refill_t + grace_period_timedelta >= pd.Timestamp(cutoff).date():
#         return "yes"
#     else:
#         return "no"


def curr(last_pickup_date, months_of_arv_refill, cutoff, grace_period):
    if last_pickup_date is None:
        return None  # or any default value you want to return when last_pickup_date is None

    qdrugs = months_of_arv_refill*30
    months_of_arv_refill_t = timedelta(days=qdrugs)

    grace_period_timedelta = timedelta(days=grace_period)

    if last_pickup_date + months_of_arv_refill_t + grace_period_timedelta >= pd.Timestamp(cutoff).date():
        return "yes"
    else:
        return "no"

def get_facility_names():
    facilities = Facility.query.with_entities(Facility.facility_name).all()
    facility_names = [facility.facility_name for facility in facilities]
    return facility_names

def age_group(age):
    if age < 1:
        return "<1"
    elif 1 <= age <= 4:
        return "1-4"
    elif 5 <= age <= 9:
        return "5-9"
    elif 10 <= age <= 14:
        return "10-14"
    elif 15 <= age <= 19:
        return "15-19"
    elif 20 <= age <= 24:
        return "20-24"
    elif 25 <= age <= 29:
        return "25-29"
    elif 30 <= age <= 34:
        return "30-34"
    elif 35 <= age <= 39:
        return "35-39"
    elif 40 <= age <= 44:
        return "40-44"
    elif 45 <= age <= 49:
        return "45-49"
    elif 50 <= age <= 54:
        return "50-54"
    elif 55 <= age <= 59:
        return "55-59"
    elif 60 <= age <= 64:
        return "60-64"
    else:
        return "65+"

def txcurr_vf(merged_df):
    # Filter the merged_df DataFrame, keeping only the rows where the curr_ll value is 'yes' and curr_pr value is either 'yes' or 'no'
    filtered_merged_df = merged_df[(merged_df['curr_ll'] == 'yes') & (merged_df['curr_pr'].isin(['yes', 'no']))]
    
    filtered_merged_df['latitude'] = filtered_merged_df['latitude'].fillna(0)
    filtered_merged_df['longitude'] = filtered_merged_df['longitude'].fillna(0)

    # Group the DataFrame by the required columns
    grouped_df = filtered_merged_df.groupby(['state', 'lga', 'facility_name', 'facility_type', 'facility_ownership', 'latitude', 'longitude'])

   
    grouped_counts = grouped_df.agg(
        txcurr_ndr=('curr_ll', 'count'),
        txcurr_pr=('curr_pr', lambda x: (x == 'yes').sum()),
        #txcurr_vf=('curr_vf', 'mean')
    ).reset_index()

    # Calculate txcurr_vf
    grouped_counts['txcurr_vf'] = grouped_counts['txcurr_pr'] / grouped_counts['txcurr_ndr']

    # Print the grouped_counts DataFrame to check if it contains data
    print("Grouped Counts###### DataFrame:")
    print(grouped_counts)

    return(grouped_counts)

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

    for sex, direction in [('male', -1), ('female', 1)]:
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
        height=500,
        # plot_bgcolor='rgba(0, 0, 0, 0)',
        # paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='black', size=14),
        margin=dict(l=50, r=50,b=50, t=50), #
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
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

    for sex, direction in [('male', -1), ('female', 1)]:
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
        height=500,
        # plot_bgcolor='rgba(0, 0, 0, 0)',
        # paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='black', size=14),
        margin=dict(l=50, r=50,b=50, t=50), #
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

    return fig

def vf_plot_funder(grouped_counts):
    # Create a bar chart with Plotly
    fig = go.Figure()
    a = 'funder'

    # Aggregate txcurr_ndr and txcurr_pr by facility type
    grouped = grouped_counts.groupby(a)

    # Calculate txcurr_vf
    txcurr_ndr = grouped['txcurr_ndr'].sum()
    txcurr_pr = grouped['txcurr_pr'].sum()
    txcurr_vf = (txcurr_pr / txcurr_ndr * 100).fillna(0)

    grouped_sums = pd.concat([txcurr_ndr, txcurr_pr, txcurr_vf], axis=1)
    grouped_sums.columns = ['txcurr_ndr', 'txcurr_pr', 'txcurr_vf']

    # sort values by txcurr_vf
    grouped_sums.sort_values(by='txcurr_vf', inplace=True)

    # Add bars for txcurr_ndr and txcurr_pr
    fig.add_trace(go.Bar(x=grouped_sums.index, y=grouped_sums['txcurr_ndr'], name='Txcurr NDR', yaxis='y', text=grouped_sums['txcurr_ndr'], textposition='auto'))
    fig.add_trace(go.Bar(x=grouped_sums.index, y=grouped_sums['txcurr_pr'], name='Txcurr PR', yaxis='y', text=grouped_sums['txcurr_pr'], textposition='auto'))

    # Add txcurr_vf as a line plot on a secondary y-axis
    fig.add_trace(go.Scatter(x=grouped_sums.sort_values('txcurr_vf').index, 
                         y=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'], 
                         name='Txcurr VF (%)', yaxis='y2', mode='markers', 
                         marker=dict(size=17), text=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'], textposition='top center', 
                         hovertemplate='%{y:.2f}%<br><extra></extra>'#hovertemplate='%{y:.2f}%'
                         ))
    # Add annotations to the marker points
    for i in range(len(grouped_sums)):
        fig.add_annotation(x=grouped_sums.sort_values('txcurr_vf').index[i],
                           y=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'][i],
                           text=f"{grouped_sums.sort_values('txcurr_vf')['txcurr_vf'][i]:.2f}%",
                           xanchor='center',
                           yanchor='bottom',
                           showarrow=False,
                           font=dict(color='black', size=12),
                           xshift=0,
                           yshift=10,
                           yref='y2')

    # Customize the layout
    fig.update_layout(
        title=f'Verification Factor by {a.capitalize()}',
        # xaxis_title= f'{a.capitalize()}',
        # yaxis_title='Counts',
        yaxis=dict(range=[0, grouped_sums['txcurr_ndr'].max()+1]),
        yaxis2=dict(title='Txcurr VF (%)', overlaying='y', side='right', tickformat='.2f%', showgrid=False),#, range=[0, 1.05]),
        barmode='group',
        showlegend=True,
        height=400,
        font=dict(color='black', size=10),
        margin=dict(l=50, r=50, b=50, t=50),
        # legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=7))
        legend=dict(
            x=0.5,
            y=-0.1,
            xanchor='center',
            yanchor='top',
            orientation='h',
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='black', size=10))
    )
 
    return fig

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

def bar_chart(df):
    fig = px.bar(df, x='funder', y='count', color='curr_ll', barmode='group',title="Number of cases by funder")
    fig.update_layout(
    height=500,
    # plot_bgcolor='rgba(0, 0, 0, 0)',
    # paper_bgcolor='rgba(0, 0, 0, 0)',
    font=dict(color='black', size=14),
    margin=dict(l=50, r=50,b=50, t=50), #
    legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
        
    )
    
    return fig

def pie_chart(df):
    fig = px.pie(df, values='count', names='facility_type', title="Proportion of validated TX_CURR by Facility Type")
    fig.update_layout(
    height=500,
        # plot_bgcolor='rgba(0, 0, 0, 0)',
        # paper_bgcolor='rgba(0, 0, 0, 0)',
    font=dict(color='black', size=14),
    margin=dict(l=50, r=50,b=50, t=50), #
    legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
)
    return fig

def map_figure(df):
    fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", color="txcurr_vf", size="txcurr_ndr",
                            hover_name="facility_name", hover_data=["state", "lga", "facility_type", "facility_ownership", "funder"],
                            color_continuous_scale=px.colors.diverging.RdYlGn[::], color_continuous_midpoint=0.5, size_max=25, zoom=5)
    fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=5,
                      margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      coloraxis_colorbar=dict(title="Verification Factor"),
                      height=500)
    fig.update_coloraxes(colorbar=dict(tickformat=".2%"))
    return fig

def vf_plot_ip(grouped_counts):
    # Create a bar chart with Plotly
    fig = go.Figure()
    a = 'implementing_partner'

    # Aggregate txcurr_ndr and txcurr_pr by facility type
    grouped = grouped_counts.groupby(a)

    # Calculate txcurr_vf
    txcurr_ndr = grouped['txcurr_ndr'].sum()
    txcurr_pr = grouped['txcurr_pr'].sum()
    txcurr_vf = (txcurr_pr / txcurr_ndr * 100).fillna(0)

    grouped_sums = pd.concat([txcurr_ndr, txcurr_pr, txcurr_vf], axis=1)
    grouped_sums.columns = ['txcurr_ndr', 'txcurr_pr', 'txcurr_vf']

    # sort values by txcurr_vf
    grouped_sums.sort_values(by='txcurr_vf', inplace=True)

    # Add bars for txcurr_ndr and txcurr_pr
    fig.add_trace(go.Bar(x=grouped_sums.index, y=grouped_sums['txcurr_ndr'], name='Txcurr NDR', yaxis='y', text=grouped_sums['txcurr_ndr'], textposition='auto'))
    fig.add_trace(go.Bar(x=grouped_sums.index, y=grouped_sums['txcurr_pr'], name='Txcurr PR', yaxis='y', text=grouped_sums['txcurr_pr'], textposition='auto'))

    # Add txcurr_vf as a line plot on a secondary y-axis
    fig.add_trace(go.Scatter(x=grouped_sums.sort_values('txcurr_vf').index, 
                         y=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'], 
                         name='Txcurr VF (%)', yaxis='y2', mode='markers', 
                         marker=dict(size=17), text=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'], textposition='top center', 
                         hovertemplate='%{y:.2f}%<br><extra></extra>'#hovertemplate='%{y:.2f}%'
                         ))
    # Add annotations to the marker points
    for i in range(len(grouped_sums)):
        fig.add_annotation(x=grouped_sums.sort_values('txcurr_vf').index[i],
                           y=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'][i],
                           text=f"{grouped_sums.sort_values('txcurr_vf')['txcurr_vf'][i]:.2f}%",
                           xanchor='center',
                           yanchor='bottom',
                           showarrow=False,
                           font=dict(color='black', size=12),
                           xshift=0,
                           yshift=10,
                           yref='y2')

    # Customize the layout
    fig.update_layout(
        title='Verification Factor by Implementing Partner',
        xaxis_title= 'Implementing Partner',
        yaxis_title='Counts',
        yaxis=dict(range=[0, grouped_sums['txcurr_ndr'].max()+1]),
        yaxis2=dict(title='Txcurr VF (%)', overlaying='y', side='right', tickformat='.2f%', showgrid=False),
        barmode='group',
        showlegend=True,
        height=500,
        font=dict(color='black', size=10),
        margin=dict(l=50, r=50, b=50, t=50),
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

   
    return fig

def vf_plot_fo(grouped_counts):
    # Create a bar chart with Plotly
    fig = go.Figure()
    a = 'facility_ownership'

    # Aggregate txcurr_ndr and txcurr_pr by facility type
    grouped = grouped_counts.groupby(a)

    # Calculate txcurr_vf
    txcurr_ndr = grouped['txcurr_ndr'].sum()
    txcurr_pr = grouped['txcurr_pr'].sum()
    txcurr_vf = (txcurr_pr / txcurr_ndr * 100).fillna(0)

    grouped_sums = pd.concat([txcurr_ndr, txcurr_pr, txcurr_vf], axis=1)
    grouped_sums.columns = ['txcurr_ndr', 'txcurr_pr', 'txcurr_vf']

    # sort values by txcurr_vf
    grouped_sums.sort_values(by='txcurr_vf', inplace=True)

    # Add bars for txcurr_ndr and txcurr_pr
    fig.add_trace(go.Bar(x=grouped_sums.index, y=grouped_sums['txcurr_ndr'], name='Txcurr NDR', yaxis='y', text=grouped_sums['txcurr_ndr'], textposition='auto'))
    fig.add_trace(go.Bar(x=grouped_sums.index, y=grouped_sums['txcurr_pr'], name='Txcurr PR', yaxis='y', text=grouped_sums['txcurr_pr'], textposition='auto'))

    # Add txcurr_vf as a line plot on a secondary y-axis
    fig.add_trace(go.Scatter(x=grouped_sums.sort_values('txcurr_vf').index, 
                         y=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'], 
                         name='Txcurr VF (%)', yaxis='y2', mode='markers', 
                         marker=dict(size=17), text=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'], textposition='top center', 
                         hovertemplate='%{y:.2f}%<br><extra></extra>'#hovertemplate='%{y:.2f}%'
                         ))
    # Add annotations to the marker points
    for i in range(len(grouped_sums)):
        fig.add_annotation(x=grouped_sums.sort_values('txcurr_vf').index[i],
                           y=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'][i],
                           text=f"{grouped_sums.sort_values('txcurr_vf')['txcurr_vf'][i]:.2f}%",
                           xanchor='center',
                           yanchor='bottom',
                           showarrow=False,
                           font=dict(color='black', size=10),
                           xshift=0,
                           yshift=10,
                           yref='y2')

    # Customize the layout
    fig.update_layout(
        title=f'Verification Factor by Facility Ownership',
        xaxis_title= 'Facility Ownership',
        yaxis_title='Counts',
        yaxis=dict(range=[0, grouped_sums['txcurr_ndr'].max()+1]),
        yaxis2=dict(title='Txcurr VF (%)', overlaying='y', side='right', tickformat='.2f%', showgrid=False),
        barmode='group',
        showlegend=True,
        height=400,
        font=dict(color='black', size=10),
        margin=dict(l=50, r=50, b=50, t=50),
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

   
    return fig

def vf_plot_ft(grouped_counts):
    # Create a bar chart with Plotly
    fig = go.Figure()
    a = 'facility_type'

    # Aggregate txcurr_ndr and txcurr_pr by facility type
    grouped = grouped_counts.groupby(a)

    # Calculate txcurr_vf
    txcurr_ndr = grouped['txcurr_ndr'].sum()
    txcurr_pr = grouped['txcurr_pr'].sum()
    txcurr_vf = (txcurr_pr / txcurr_ndr * 100).fillna(0)

    grouped_sums = pd.concat([txcurr_ndr, txcurr_pr, txcurr_vf], axis=1)
    grouped_sums.columns = ['txcurr_ndr', 'txcurr_pr', 'txcurr_vf']

    # sort values by txcurr_vf
    grouped_sums.sort_values(by='txcurr_vf', inplace=True)

    # Add bars for txcurr_ndr and txcurr_pr
    fig.add_trace(go.Bar(x=grouped_sums.index, y=grouped_sums['txcurr_ndr'], name='Txcurr NDR', yaxis='y', text=grouped_sums['txcurr_ndr'], textposition='auto'))
    fig.add_trace(go.Bar(x=grouped_sums.index, y=grouped_sums['txcurr_pr'], name='Txcurr PR', yaxis='y', text=grouped_sums['txcurr_pr'], textposition='auto'))

    # Add txcurr_vf as a line plot on a secondary y-axis
    fig.add_trace(go.Scatter(x=grouped_sums.sort_values('txcurr_vf').index, 
                         y=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'], 
                         name='Txcurr VF (%)', yaxis='y2', mode='markers', 
                         marker=dict(size=17), text=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'], textposition='top center', 
                         hovertemplate='%{y:.2f}%<br><extra></extra>'#hovertemplate='%{y:.2f}%'
                         ))
    # Add annotations to the marker points
    for i in range(len(grouped_sums)):
        fig.add_annotation(x=grouped_sums.sort_values('txcurr_vf').index[i],
                           y=grouped_sums.sort_values('txcurr_vf')['txcurr_vf'][i],
                           text=f"{grouped_sums.sort_values('txcurr_vf')['txcurr_vf'][i]:.2f}%",
                           xanchor='center',
                           yanchor='bottom',
                           showarrow=False,
                           font=dict(color='black', size=10),
                           xshift=0,
                           yshift=10,
                           yref='y2')

    # Customize the layout
    fig.update_layout(
        title='Verification Factor by Facility Type',
        xaxis_title= 'Facility Type',
        yaxis_title='Counts',
        yaxis=dict(range=[0, grouped_sums['txcurr_ndr'].max()+1]),
        yaxis2=dict(title='Txcurr VF (%)', overlaying='y', side='right', tickformat='.2f%', showgrid=False),
        barmode='group',
        showlegend=True,
        height=400,
        font=dict(color='black', size=10),
        margin=dict(l=50, r=50, b=50, t=50),
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

   
    return fig

def bubble_chart(df):
    # Calculate the height dynamically
    height = len(df['facility_name'].unique()) * 15  # Adjust the multiplying factor as per your requirements
    height = max(height, 400)  # Set a minimum height

    fig = px.scatter(df, x="txcurr_vf", y="txcurr_ndr", color="txcurr_vf", size="txcurr_pr",
                     hover_name="facility_name", text="state",
                     hover_data=["lga", "facility_type", "facility_ownership", "funder"],
                     color_continuous_scale=px.colors.diverging.RdYlGn[::], color_continuous_midpoint=0.5, size_max=25)
    fig.update_traces(textfont=dict(color='black', size=14))
    fig.update_layout(title="Verification Factory by State", #Current Viral Load Suppression Among Different Health Facilities
                      xaxis_title="Verification Factor",
                      yaxis_title="TXCURR_NDR",
                      coloraxis_colorbar=dict(title="Verification Factor"),
                      height=height,  # use the calculated height here
                      xaxis=dict(tickformat=".2%", range=[0, 1.1]),  # set x-axis range from 0% to 100%
                      yaxis=dict(range=[0, df['txcurr_ndr'].max()+2]))  # set y-axis range from 0 to the maximum value in 'txcurr_ndr'
    
    fig.update_coloraxes(colorbar=dict(tickformat=".2%"))
    return fig

def map_figure_ch(df):
    fig = px.choropleth(df, locations='state', locationmode="NG-states",
                        color='txcurr_vf', scope="nigeria",
                        hover_data=["state", "lga", "facility_type", "facility_ownership", "funder"],
                        color_continuous_scale=px.colors.diverging.RdYlGn[::-1],
                        labels={'txcurr_vf': 'VF_Curr'})
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                      coloraxis_colorbar=dict(title="VF_Curr"),
                      height=600)
    return fig

def map_figure_bu(df):
    fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", color="state", size="txcurr_ndr",
                            hover_name="facility_name", hover_data=["state", "lga", "facility_type", "facility_ownership", "funder"],
                            color_continuous_scale=px.colors.qualitative.Pastel, zoom=5)
    fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=5,
                      margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      coloraxis_colorbar=dict(title="State"),
                      height=600)
    return fig

def bubble_chart_age_sex(filtered_df):
    yes_grouped = filtered_df[filtered_df['curr_pr'] == 'yes'].groupby(['age_group', 'sex']).size().reset_index(name='curr_pr')
    
    all_age_groups = pd.DataFrame({
        'age_group': ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]
    })
    
    pivot_table = yes_grouped.pivot_table(index='age_group', columns='sex', values='curr_pr', fill_value=0).reset_index()
    pivot_table.columns.name = None
    pivot_table.reset_index(drop=True, inplace=True)

    merged_grouped_data = all_age_groups.merge(pivot_table, on='age_group', how='left').fillna(0)

    # Calculate the total number of records for each age group and sex combination
    merged_grouped_data['total_count'] = merged_grouped_data['Male'] + merged_grouped_data['Female']
    
    fig = go.Figure()
    
    # Create a trace for each age group and sex combination
    for sex, direction in [('Male', -1), ('Female', 1)]:
        fig.add_trace(go.Scatter(
            x=direction * merged_grouped_data.get(sex, [0]*len(merged_grouped_data)),
            y=merged_grouped_data['age_group'],
            name=sex,
            mode='markers',
            marker=dict(
                size=merged_grouped_data['total_count'],
                sizemode='diameter',
                sizeref=0.1,
                sizemin=1,
                color=sex,
                opacity=0.7
            ),
            text=[abs(x) for x in merged_grouped_data.get(sex, [0]*len(merged_grouped_data))],
            textposition='middle right'
        ))
    
    fig.update_layout(
        title="TX_Curr by Age and Sex (Validated - Pharmacy Record)",
        xaxis=dict(title='TX_Curr'),
        yaxis=dict(title='Age Group', categoryorder='array', categoryarray=["65+", "60-64", "55-59", "50-54", "45-49", "40-44", "35-39", "30-34", "25-29", "20-24", "15-19", "10-14", "5-9", "1-4", "<1"]),
        showlegend=True,
        hovermode='closest',
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

# def bar_chart_facility(df):
#     df_sorted = df.sort_values('txcurr_vf')

#     # Calculate the height dynamically, e.g. 50 pixels per bar
#     height = len(df_sorted['facility_name'].unique()) * 50
#     height = max(height, 400)  # Set a minimum height

#     fig = px.bar(df_sorted, x='txcurr_vf', y='facility_name', #color='txcurr_vf',
#                  orientation='h', hover_name="facility_name", text=df_sorted['txcurr_pr']/df_sorted['txcurr_ndr']*100,
#                  hover_data=['state', 'lga', 'facility_type', 'facility_ownership', 'funder'],
#                  color_continuous_scale=px.colors.diverging.RdYlGn[::], color_continuous_midpoint=0.5)
#     fig.update_traces(textposition='outside', texttemplate='%{text:.2f}%')
#     fig.update_layout(title='Verification Factor by Facility',
#                       xaxis_title='Verification Factor (%)',
#                       yaxis_title='Facility',
#                       coloraxis_colorbar=dict(title='Verification Factor (%)'),
#                       height=height,
#                       font=dict(size=12))
#     fig.update_xaxes(tickformat=".2%")
#     fig.update_coloraxes(colorbar=dict(tickformat=".2%"))
#     return fig

import textwrap

def bar_chart_facility(df):
    df_sorted = df.sort_values('txcurr_vf')
    df_sorted['facility_name'] = ['<br>'.join(textwrap.wrap(x, width=15)) for x in df_sorted['facility_name']]

    # Calculate the height dynamically, e.g. 50 pixels per bar
    height = len(df_sorted['facility_name'].unique()) * 50
    height = max(height, 400)  # Set a minimum height

    fig = px.bar(df_sorted, x='txcurr_vf', y='facility_name', #color='txcurr_vf',
                 orientation='h', hover_name="facility_name", text=df_sorted['txcurr_pr']/df_sorted['txcurr_ndr']*100,
                 hover_data=['state', 'lga', 'facility_type', 'facility_ownership', 'funder'],
                 color_continuous_scale=px.colors.diverging.RdYlGn[::], color_continuous_midpoint=0.5)
    fig.update_traces(textposition='outside', texttemplate='%{text:.2f}%')
    fig.update_layout(title='Verification Factor by Facility',
                      xaxis_title='Verification Factor (%)',
                      yaxis_title='Facility',
                      coloraxis_colorbar=dict(title='Verification Factor (%)'),
                      height=height,
                      font=dict(size=10))
    fig.update_xaxes(tickformat=".2%")
    fig.update_coloraxes(colorbar=dict(tickformat=".2%"))
    return fig


def plot_txcurr_pr_vs_txcurr_ndr(df):
    # Count the occurrences of 'yes' for curr_pr and curr_ll
    count_curr_pr_yes = len(df[df['curr_pr'] == 'yes'])
    count_curr_ll_yes = len(df[df['curr_ll'] == 'yes'])
    
    # Create a horizontal bar chart
    fig = go.Figure(go.Bar(x=[count_curr_pr_yes, count_curr_ll_yes], 
                           y=['Validated Drug Pick-up Pharmacy', 'Reported NDR'], 
                           text=[count_curr_pr_yes, count_curr_ll_yes], 
                           textposition='auto', 
                           orientation='h'))

    fig.update_layout(
        title="Comparison of Reported TX_CURR and Verified TX_CURR(Confirmed Pharmacy Pick-up)",
        xaxis_title="Treatment Curr",
        yaxis_title="Variable",
        height=300,
        font=dict(color='black', size=10),
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

    return fig

def plot_txcurr_cr_vs_txcurr_ndr(df):
    # Count the occurrences of 'yes' for curr_pr and curr_ll
    count_curr_cr_yes = len(df[df['curr_cr'] == 'yes'])
    count_curr_ll_yes = len(df[df['curr_ll'] == 'yes'])
    
    # Create a horizontal bar chart
    fig = go.Figure(go.Bar(x=[count_curr_cr_yes, count_curr_ll_yes], 
                           y=['Validated Client Folder', 'Reported NDR'], 
                           text=[count_curr_cr_yes, count_curr_ll_yes], 
                           textposition='auto', 
                           orientation='h'))

    fig.update_layout(
        title="Comparison of Reported TX_CURR and Verified TX_CURR(Client Folder)",
        xaxis_title="Treatment Curr",
        yaxis_title="Variable",
        height=300,
        font=dict(color='black', size=10),
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

    return fig

def plot_txcurr_pr_vs_txcurr_cr(df):
    # Count the occurrences of 'yes' for curr_pr and curr_ll
    count_curr_pr_yes = len(df[df['curr_pr'] == 'yes'])
    count_curr_cr_yes = len(df[df['curr_cr'] == 'yes'])
    
    # Create a horizontal bar chart
    fig = go.Figure(go.Bar(x=[count_curr_pr_yes, count_curr_cr_yes], 
                           y=['Validated Drug Pick-up Pharmacy', 'Validated Client Folder'], 
                           text=[count_curr_pr_yes, count_curr_cr_yes], 
                           textposition='auto', 
                           orientation='h'))

    fig.update_layout(
        title="Comparison of Verified TX_CURR(Confirmed Pharmacy Pick-up) and Verified TX_CURR(Client Folder)",
        xaxis_title="Treatment Curr",
        yaxis_title="Variable",
        height=300,
        font=dict(color='black', size=10),
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

    return fig

def plot_weekly_curr_pr(df, start, stop):
    df['entry_datetime_pr'] = pd.to_datetime(df['entry_datetime_pr'])
    
    filtered_df = df[(df['entry_datetime_pr'] >= start) & (df['entry_datetime_pr'] <= stop)]
    weekly_grouped_pr = filtered_df[filtered_df['curr_pr'].isin(['yes', 'no'])].groupby(filtered_df['entry_datetime_pr'].dt.to_period("W")).size().reset_index(name='count')

    # Generate a DataFrame with all weeks between April 24th and July 30th
    all_weeks = pd.date_range(start=start, end=stop, freq='W').to_period("W").to_frame(index=False, name='entry_datetime_pr')

    # Merge weekly_grouped_pr with all_weeks, filling missing values with 0
    merged_weekly_grouped_pr = all_weeks.merge(weekly_grouped_pr, on='entry_datetime_pr', how='left').fillna(0)

    # Create a new column with the format "wk1", "wk2", etc.
    merged_weekly_grouped_pr['week_label'] = 'wk' + (merged_weekly_grouped_pr.index + 1).astype(str)

    fig = go.Figure()

    fig.add_trace(go.Bar(x=merged_weekly_grouped_pr['week_label'],
                         y=merged_weekly_grouped_pr['count'],
                         name='Weekly curr_pr'))

    fig.update_layout(title='Weekly Verified TX_CURR - Pharmacy Pick up',
                      xaxis=dict(title='Weeks', ticktext=merged_weekly_grouped_pr['week_label'], tickvals=merged_weekly_grouped_pr['week_label']),
                      yaxis_title='Verified TX_CURR - Pharm',
                      height=270,
                      legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10)))

    return fig

def plot_weekly_curr_cr(df, start, stop):
    df['entry_datetime_cr'] = pd.to_datetime(df['entry_datetime_cr'])
    
    filtered_df = df[(df['entry_datetime_cr'] >= start) & (df['entry_datetime_cr'] <= stop)]
    weekly_grouped_cr = filtered_df[filtered_df['curr_cr'].isin(['yes', 'no'])].groupby(filtered_df['entry_datetime_cr'].dt.to_period("W")).size().reset_index(name='count')

    # Generate a DataFrame with all weeks between April 24th and July 30th
    all_weeks = pd.date_range(start=start, end=stop, freq='W').to_period("W").to_frame(index=False, name='entry_datetime_cr')

    # Merge weekly_grouped_cr with all_weeks, filling missing values with 0
    merged_weekly_grouped_cr = all_weeks.merge(weekly_grouped_cr, on='entry_datetime_cr', how='left').fillna(0)

    # Create a new column with the format "wk1", "wk2", etc.
    merged_weekly_grouped_cr['week_label'] = 'wk' + (merged_weekly_grouped_cr.index + 1).astype(str)

    fig = go.Figure()

    fig.add_trace(go.Bar(x=merged_weekly_grouped_cr['week_label'],
                         y=merged_weekly_grouped_cr['count'],
                         name='Weekly curr_cr'))

    fig.update_layout(title='Weekly Verified TX_CURR -Client Filder',
                      xaxis=dict(title='Weeks', ticktext=merged_weekly_grouped_cr['week_label'], tickvals=merged_weekly_grouped_cr['week_label']),
                      yaxis_title='Verified TX_CURR - Folder',
                      height=270,
                      legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10)))

    return fig

def plot_progress_pr_towards_ll(df):
    curr_pr_yes_count = df[df['curr_pr'].isin(['yes', 'no'])].shape[0]
    curr_ll_yes_count = df[df['curr_ll'] == 'yes'].shape[0]
    # Avoid dividing by zero
    if curr_ll_yes_count != 0:
        rate = (curr_pr_yes_count / curr_ll_yes_count) * 100
    else:
        rate = 0

    fig = go.Figure()

    fig.add_trace(go.Bar(y=['Progress'],
                         x=[curr_ll_yes_count],
                         name='Total Reported',
                         base=0,
                         width=0.2,
                         orientation='h'
                         ))

    fig.add_trace(go.Bar(y=['Progress'],
                         x=[curr_pr_yes_count],
                         name='Total Verified',
                         base=0,
                         width=0.1,
                         orientation='h',
                         text=f'{rate:.2f}%',
                         textposition='outside',
                         textfont_color='white'
                         ))

    fig.update_layout(barmode='overlay',
                      title='Progress in Treatment Current Verification (Phamarcy Drug Pick up)',
                      xaxis_title='TX_CURR',
                      height=270,
                      legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10)))

    return fig

def plot_progress_cr_towards_ll(df):
    curr_cr_yes_count = df[df['curr_cr'].isin(['yes', 'no'])].shape[0]
    curr_ll_yes_count = df[df['curr_ll'] == 'yes'].shape[0]
    # Avoid dividing by zero
    if curr_ll_yes_count != 0:
        rate = (curr_cr_yes_count / curr_ll_yes_count) * 100
    else:
        rate = 0

    fig = go.Figure()

    fig.add_trace(go.Bar(y=['Progress'],
                         x=[curr_ll_yes_count],
                         name='Total Reported',
                         base=0,
                         width=0.2,
                         orientation='h'
                         ))

    fig.add_trace(go.Bar(y=['Progress'],
                         x=[curr_cr_yes_count],
                         name='Total Verified',
                         base=0,
                         width=0.1,
                         orientation='h',
                         text=f'{rate:.2f}%',
                         textposition='outside',
                         textfont_color='white'
                         ))

    fig.update_layout(barmode='overlay',
                      title='Progress in Treatment Current Verification (Client Folder)',
                      xaxis_title='TX_CURR',
                      height=270,
                      legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10)))

    return fig

def plot_daily_curr_pr(df, start, stop):
    df['entry_datetime_pr'] = pd.to_datetime(df['entry_datetime_pr'])
    
    filtered_df = df[(df['entry_datetime_pr'] >= start) & (df['entry_datetime_pr'] <= stop)]
    daily_grouped_pr = filtered_df[filtered_df['curr_pr'].isin(['yes', 'no'])].groupby(filtered_df['entry_datetime_pr'].dt.to_period("D")).size().reset_index(name='count')

    # Generate a DataFrame with all days between May 1st and July 30th
    all_days = pd.date_range(start=start, end=stop, freq='D').to_period("D").to_frame(index=False, name='entry_datetime_pr')

    # Merge daily_grouped_pr with all_days, filling missing values with 0
    merged_daily_grouped_pr = all_days.merge(daily_grouped_pr, on='entry_datetime_pr', how='left').fillna(0)

    fig = go.Figure()

    fig.add_trace(go.Bar(x=merged_daily_grouped_pr['entry_datetime_pr'].astype(str),
                         y=merged_daily_grouped_pr['count'],
                         name='Daily curr_pr'))

    fig.update_layout(title='Daily Verified TX_CURR - Pharmacy Pick up',
                      xaxis=dict(title='Days', tickangle=45, ticktext=merged_daily_grouped_pr['entry_datetime_pr'].astype(str), tickvals=merged_daily_grouped_pr['entry_datetime_pr'].astype(str)),
                      yaxis_title='Verified TX_CURR - Pharm',
                      height=350,
                      legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10)))

    return fig

def plot_daily_curr_cr(df, start, stop):
    df['entry_datetime_cr'] = pd.to_datetime(df['entry_datetime_cr'])
    
    filtered_df = df[(df['entry_datetime_cr'] >= start) & (df['entry_datetime_cr'] <= stop)]
    daily_grouped_cr = filtered_df[filtered_df['curr_cr'].isin(['yes', 'no'])].groupby(filtered_df['entry_datetime_cr'].dt.to_period("D")).size().reset_index(name='count')

    # Generate a DataFrame with all days between May 1st and July 30th
    all_days = pd.date_range(start= start, end=stop, freq='D').to_period("D").to_frame(index=False, name='entry_datetime_cr')

    # Merge daily_grouped_pr with all_days, filling missing values with 0
    merged_daily_grouped_cr = all_days.merge(daily_grouped_cr, on='entry_datetime_cr', how='left').fillna(0)

    fig = go.Figure()

    fig.add_trace(go.Bar(x=merged_daily_grouped_cr['entry_datetime_cr'].astype(str),
                         y=merged_daily_grouped_cr['count'],
                         name='Daily curr_cr'))

    fig.update_layout(title='Daily Verified TX_CURR - Folder',
                      xaxis=dict(title='Days', tickangle=45, ticktext=merged_daily_grouped_cr['entry_datetime_cr'].astype(str), tickvals=merged_daily_grouped_cr['entry_datetime_cr'].astype(str)),
                      yaxis_title='Verified TX_CURR - Folder',
                      height=350,
                      legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10)))

    return fig

def hplot_daily_curr_cr(df):
    df['entry_datetime_cr'] = pd.to_datetime(df['entry_datetime_cr'])

    filtered_df = df[(df['entry_datetime_cr'] >= '2023-05-01') & (df['entry_datetime_cr'] <= '2023-07-30')]
    daily_grouped_cr = filtered_df[filtered_df['curr_cr'].isin(['yes', 'no'])].groupby(filtered_df['entry_datetime_cr'].dt.to_period("D")).size().reset_index(name='count')

    # Generate a DataFrame with all days between May 1st and July 30th
    all_days = pd.date_range(start='2023-05-01', end='2023-07-30', freq='D').to_period("D").to_frame(index=False, name='entry_datetime_cr')

    # Merge daily_grouped_pr with all_days, filling missing values with 0
    merged_daily_grouped_cr = all_days.merge(daily_grouped_cr, on='entry_datetime_cr', how='left').fillna(0)

    # Reshape the data to be used in a heatmap
    heatmap_data = merged_daily_grouped_cr.pivot_table(index='entry_datetime_cr', values='count', aggfunc=np.sum)

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=heatmap_data.values,
        x=merged_daily_grouped_cr['entry_datetime_cr'].astype(str),
        y=['Verified TX_CURR - Folder'],
        colorscale='Viridis',
        name='Daily curr_cr',
    ))

    fig.update_layout(
        title='Daily Verified TX_CURR - Folder',
        xaxis=dict(title='Days', ticktext=merged_daily_grouped_cr['entry_datetime_cr'].astype(str), tickvals=merged_daily_grouped_cr['entry_datetime_cr'].astype(str)),
        yaxis_title='Verified TX_CURR - Folder',
        height=350,
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

    return fig

def hplot_daily_curr_pr(df):
    df['entry_datetime_pr'] = pd.to_datetime(df['entry_datetime_pr'])

    filtered_df = df[(df['entry_datetime_pr'] >= '2023-05-01') & (df['entry_datetime_pr'] <= '2023-07-30')]
    daily_grouped_pr = filtered_df[filtered_df['curr_cr'].isin(['yes', 'no'])].groupby(filtered_df['entry_datetime_pr'].dt.to_period("D")).size().reset_index(name='count')

    # Generate a DataFrame with all days between May 1st and July 30th
    all_days = pd.date_range(start='2023-05-01', end='2023-07-30', freq='D').to_period("D").to_frame(index=False, name='entry_datetime_pr')

    # Merge daily_grouped_pr with all_days, filling missing values with 0
    merged_daily_grouped_pr = all_days.merge(daily_grouped_pr, on='entry_datetime_pr', how='left').fillna(0)

    # Reshape the data to be used in a heatmap
    heatmap_data = merged_daily_grouped_pr.pivot_table(index='entry_datetime_pr', values='count', aggfunc=np.sum)

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=heatmap_data.values,
        x=merged_daily_grouped_pr['entry_datetime_pr'].astype(str),
        y=['Verified TX_CURR - Folder'],
        colorscale='Viridis',
        name='Daily curr_cr',
    ))

    fig.update_layout(
        title='Daily Verified TX_CURR - Folder',
        xaxis=dict(title='Days', ticktext=merged_daily_grouped_pr['entry_datetime_pr'].astype(str), tickvals=merged_daily_grouped_pr['entry_datetime_pr'].astype(str)),
        yaxis_title='Verified TX_CURR - Folder',
        height=350,
        legend=dict(x=1.02, y=1, bordercolor='black', borderwidth=0.5, orientation='v', traceorder='normal', font=dict(size=10))
    )

    return fig

def database_data():
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

    vf_df = merged_df[(merged_df['curr_ll'] == 'yes') & (merged_df['curr_pr'].isin(['yes', 'no']))]
    df = vf_df.copy()
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
    # print('grouped_counts DataFrame:')
    # print(grouped_counts)
    df1 = pd.DataFrame(grouped_counts)
    return merged_df, df1

def txcurr_ndr_card(df):
    df = df[(df['curr_ll'] == 'yes') & (df['curr_pr'].isin(['yes', 'no']))]
    df['txcurr_ndr'] = (df['curr_ll'] == 'yes').astype(int)
    # df['txcurr_cr'] = (df['curr_cr'] == 'yes').astype(int)
    # df['txcurr_pr'] = (df['curr_pr'] == 'yes').astype(int)
    content = df['txcurr_ndr'].sum()
    return content

def txcurr_cr_card(df):
    df = df[(df['curr_ll'] == 'yes') & (df['curr_pr'].isin(['yes', 'no']))]
    # df['txcurr_ndr'] = (df['curr_ll'] == 'yes').astype(int)
    df['txcurr_cr'] = (df['curr_cr'] == 'yes').astype(int)
    # df['txcurr_pr'] = (df['curr_pr'] == 'yes').astype(int)
    content = df['txcurr_cr'].sum()
    return content

def txcurr_pr_card(df):
    df = df[(df['curr_ll'] == 'yes') & (df['curr_pr'].isin(['yes', 'no']))]
    # df['txcurr_ndr'] = (df['curr_ll'] == 'yes').astype(int)
    # df['txcurr_cr'] = (df['curr_cr'] == 'yes').astype(int)
    df['txcurr_pr'] = (df['curr_pr'] == 'yes').astype(int)
    content = df['txcurr_pr'].sum()
    return content

def txcurr_vf_card(df):
    ndf = df[(df['curr_ll'] == 'yes') & (df['curr_pr'].isin(['yes', 'no']))].copy()
    ndf['txcurr_ndr'] = (ndf['curr_ll'] == 'yes').astype(int)
    # df['txcurr_cr'] = (df['curr_cr'] == 'yes').astype(int)
    ndf['txcurr_pr'] = (ndf['curr_pr'] == 'yes').astype(int)
    ndf['txcurr_vf'] = ndf['txcurr_pr'].sum()/ndf['txcurr_ndr'].sum()
    content = ndf['txcurr_vf'].mean()
    return content

# def txcurr_ndr_card(df):
#     content = df['txcurr_ndr'].sum()
#     return content