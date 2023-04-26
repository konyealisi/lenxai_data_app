# utils.py
from wtforms.validators import  ValidationError
from models import User, DataEntry, Facility
from datetime import datetime, timedelta

import pandas as pd

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
    
def curr(last_pickup_date, months_of_arv_refill, cutoff, grace_period):
    if last_pickup_date is None:
        return None  # or any default value you want to return when last_pickup_date is None

    qdrugs = months_of_arv_refill*30
    months_of_arv_refill_t = timedelta(days=qdrugs)

    grace_period_timedelta = timedelta(days=grace_period)

    if last_pickup_date + months_of_arv_refill_t + grace_period_timedelta >= cutoff:
        return "Yes"
    else:
        return "No"


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


# Group the DataFrame by required columns
#grouped_df = merged_df[merged_df['curr_ll'].isin(['yes', 'no'])].groupby(['state', 'lga', 'facility_name', 'facility_type', 'facility_ownership', 'latitude', 'longitude'])
def txcurr_vf(merged_df):
    # Filter the merged_df DataFrame, keeping only the rows where the curr_ll value is 'yes' and curr_pr value is either 'yes' or 'no'
    filtered_merged_df = merged_df[(merged_df['curr_ll'] == 'yes') & (merged_df['curr_pr'].isin(['yes', 'no']))]
    
    # for col in ['state', 'lga', 'facility_name', 'facility_type', 'facility_ownership', 'latitude', 'longitude']:
    #     print(f"{col}: {filtered_merged_df[col].unique()}")

    # filtered_merged_df['txcurr_ndr'] = (filtered_merged_df['curr_ll'] == 'yes').astype(int)
    # filtered_merged_df['txcurr_pr'] = ((filtered_merged_df['curr_pr'] == 'yes') | (filtered_merged_df['curr_pr'] == 'no')).astype(int)

    filtered_merged_df['latitude'] = filtered_merged_df['latitude'].fillna(0)
    filtered_merged_df['longitude'] = filtered_merged_df['longitude'].fillna(0)

    # grouped_df = filtered_merged_df.groupby(['state', 'lga', 'facility_name', 'facility_type', 'facility_ownership', 'latitude', 'longitude'])[['txcurr_ndr', 'txcurr_pr']].sum().reset_index()

    # grouped_df['txcurr_vf'] = grouped_df['txcurr_ndr'] - grouped_df['txcurr_pr']

    # print("Grouped Counts DataFrame:")
    # print(grouped_df)

    # grouped_df = filtered_merged_df[filtered_merged_df['curr_ll'].isin(['yes', 'no'])].groupby(['state', 'lga', 'facility_name', 'facility_type', 'facility_ownership', 'latitude', 'longitude'])
    
    # print("~~~~~~~~~~~")
    # print(grouped_df.head())



    # Group the DataFrame by the required columns
    grouped_df = filtered_merged_df.groupby(['state', 'lga', 'facility_name', 'facility_type', 'facility_ownership', 'latitude', 'longitude'])

    # Calculate the counts for txcurr_ndr and txcurr_pr
    # grouped_counts = grouped_df.agg(
    #     txcurr_ndr=pd.NamedAgg(column='curr_ll', aggfunc=lambda x: x.eq('yes').sum()),
    #     txcurr_pr=pd.NamedAgg(column='curr_pr', aggfunc=lambda x: x.eq('yes').sum())
    # ).reset_index()

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
