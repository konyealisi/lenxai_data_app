# utils.py
from wtforms.validators import  ValidationError
from models import User, DataEntry, Facility
from datetime import datetime, timedelta

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

def curr(last_pickup_date, cutoff, grace_period):
    grace_period_timedelta = timedelta(days=grace_period)
    if last_pickup_date + grace_period_timedelta >= cutoff:
        return 'yes'
    else:
        return 'no'


