from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Request

import csv
import os
import subprocess
import re

from sqlalchemy import text, create_engine, inspect
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField, DateField, EmailField, FileField, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

from io import StringIO
from flask import Response
from flask_migrate import Migrate
from flask import current_app
from datetime import datetime, timedelta, date
import pandas as pd
from werkzeug.utils import secure_filename
from functools import wraps

from forms import LoginForm, DataEntryForm, RegistrationFormAdmin, RegistrationFormSuperuser, FacilityClientForm, FacilityForm, PhamarcyForm, ValidateRecordForm
from utils import facility_choices, client_choices, allowed_file, calculate_age, calculate_age_in_months, clean_dataframe, entry_exists, facility_exists, curr, get_facility_names
from models import db, User, DataEntry, Facility#, update_all_facilities, update_all_facilities_txcurr_pr, update_all_facilities_txcurr_cr, update_all_facilities_txcurr_ndr, update_all_facilities_txcurr_vf
from sqlalchemy.engine.reflection import Inspector
from flask.cli import AppGroup

from dashboard import init_dash



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.environ.get('FLASK_APP_SECRET_KEY', 'fallback_secret_key')

db_user = os.environ.get('DB_USER_ndqadata')
db_password = os.environ.get('DB_PASSWORD_ndqadata')
db_host = os.environ.get('DB_HOST_ndqadata')
db_name = os.environ.get('DB_NAME_ndqadata')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'

db.init_app(app)

# Create a group of commands for user management
user_cli = AppGroup('user')
# Register the command group with the app
app.cli.add_command(user_cli)

# Initialize the migration tool 
# this is used to modify the database schema 
# after it has been created
migrate = Migrate(app, db)


def requires_roles(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Login required.')
                return redirect(url_for('login'))
            elif current_user.role not in roles:
                flash('You do not have permission to access this page.')
                return redirect(url_for('landing'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# login manager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# register route - for creating new user by authorized user - sysadmin, admin, and superuser
@app.route('/register', methods=['GET', 'POST'])
@requires_roles('sysadmin','admin', 'superuser')
def register():
    if not current_user.is_authenticated or current_user.role not in ['sysadmin', 'admin', 'superuser']:
        flash("You don't have permission to access this page.")
        return redirect(url_for('index'))
    if current_user.role in ['sysadmin', 'admin']:
        register_form = RegistrationFormAdmin()
    elif current_user.role == 'superuser':
        register_form = RegistrationFormSuperuser()    
    if register_form.validate_on_submit():
        user = User(username=register_form.username.data, email=register_form.email.data, role=register_form.role.data)
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('login'))
    return render_template('register.html', title='Register', register_form=register_form)

# login route - for login in and gaining access to the platform
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('landing'))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user)
            flash('You have successfully logged in.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('landing'))
        else:
            flash('Login unsuccessful.  Please check your email and password.', 'danger')
    return render_template('login.html', title='Login', login_form=login_form)#, register_form=register_form)

# User route - lets the sysadmin and admin user view all registered users on the platform
@app.route('/users')
@requires_roles('sysadmin', 'admin')
def users():
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

# logou route - for login out of the platform
@app.route('/logout')
@login_required
def logout():
    # Clear the user's session
    session.clear()
    db.session.remove()
    # Redirect the user to the login page or another page of your choice
    return redirect(url_for("login"))

 
# Route to render the download page - this redirects to the download_csv route
@app.route("/download")
@requires_roles('sysadmin', 'admin', 'superuser')
def download():
    return render_template("download.html")


@app.route('/download_csv', methods=['GET'])
@requires_roles('sysadmin', 'admin', 'superuser')
def download_csv():
    # Query data from the database and join DataEntry and Facility tables on facility_name
    data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name).all()

    # Convert data to a list of dictionaries
    data_list = []
    for row in data:
        data_entry = row.DataEntry.to_dict()
        facility = row.Facility.to_dict()

        # Merge the dictionaries and add the 'facility_id' from the Facility table
        merged_data = {**data_entry, **facility}
        data_list.append(merged_data)

    # Create a CSV file in memory
    csv_file = StringIO()
    fieldnames = ['facility_name','id', 'state', 'lga', 'latitude', 'longitude','client_id','client_name','sex','age','tx_age','dregimen_ll','mrefill_ll','laspud_ll','curr_ll',
                    'userid_cr','dregimen_po','mrefill_po','laspud_po','quantityd_po','curr_cr','client_folder','dregimen_po_correct','laspud_po_correct','quantityd_po_correct', 
                        'userid_pr','dregimen_pw','mrefill_pw','laspud_pw','quantityd_pw','curr_pr','pharm_doc', 'dregimen_pw_correct','laspud_pw_correct','quantityd_pw_correct']
    
    # Define user-friendly headers
    friendly_headers = ['Health Facility', 'Facility ID', 'State', 'LGA', 'Latitude', 'Longitude', 'Client ID', 'Client Name', 'Sex', 'Age', 'Tx Age (months)', 'Drug Regimen NDR', 'Month of Refill NDR', 'LAST Pick Up Date NDR', 'is Current on Tx NDR',
                        'User ID CR', 'Drug Regimen CR', 'Month of Refill CR', 'LAST Pick Up Date CR', 'Drug Quantity CR', 'is Current on Tx CR', 'Client Folder Sighted?', 'Drug Regimen CR Correct?', 'LAST Pick Up Date CR Correct?', 'Drug Quantity CR Correct?',
                        'User ID PR', 'Drug Regimen PR', 'Month of Refill PR', 'LAST Pick Up Date PR', 'Drug Quantity PR', 'is Current on Tx PR', 'Pharmacy Documentation Sighted?', 'Drug Regimen PR Correct?', 'LAST Pick Up Date PR Correct?', 'Drug Quantity PR Correct?']
    
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction='ignore')
    writer.writerow(dict(zip(fieldnames, friendly_headers)))
    for row in data_list:
        filtered_row = {k: v for k, v in row.items() if k not in ['txcurr_cr', 'txcurr_vf', 'txcurr_ndr', 'txcurr_pr', 'facility_id']}
        writer.writerow(filtered_row)

    # Serve the CSV file as a response
    response = Response(
        csv_file.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=data.csv'}
    )

    return response


# The main landing page
@app.route("/landing")
@login_required
def landing():
    return render_template("landing.html")

@app.route("/data_entry")
@login_required
def data_entry():
    return render_template("dataentry.html")

@app.route("/validate_entry")
@requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator')
def validate_entry():
    return render_template("valentry.html")

@app.route("/update_record")
@requires_roles('sysadmin', 'admin')
def update_record():
    return render_template("updaterecord.html")



# @app.route("/upload")
# @requires_roles('sysadmin','admin')
# def upload():
#     return render_template("upload.html")

# Ensure the UPLOAD_FOLDER exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


cutoff = date(year=2022, month=6, day=30)
grace_period = 28

@app.route("/upload_facility", methods=['GET', 'POST'])
@requires_roles('sysadmin','admin')
def upload_facility():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print("File saved at:", os.path.join(app.config['UPLOAD_FOLDER'], filename))

            if filename.endswith('.csv'):
                df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            elif filename.endswith('.xls') or filename.endswith('.xlsx'):
                df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            elif filename.endswith('.json'):
                df = pd.read_json(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            elif filename.endswith('.xml'):
                df = pd.read_xml(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            print("Data read from file:\n", df)

            df.columns = df.columns.str.replace(r'\s*[\(\[].*?[\)\]]|\?', '', regex=True)
            print("Column names after processing:\n", df.columns)

            facility_mapping = {
                'Facility Name': 'facility_name',
                'Country': 'country',
                'State': 'state',
                'LGA': 'lga',
                'Latitude': 'latitude',
                'Longitude': 'longitude',
                'Facility type': 'facility_type',
                'Facility Ownership': 'facility_ownership',
                'Funder': 'funder',
                'Implementing Partner': 'implementing_partner'
            }

            for index, row in df.iterrows():
                fac_data = {}
                for file_col, data_entry_col in facility_mapping.items():
                    if file_col in df.columns:
                        fac_data[data_entry_col] = row[file_col]
                    else:
                        fac_data[data_entry_col] = None
                print("Facility data:", fac_data)
                if fac_data['facility_name'] is not None and not facility_exists(fac_data['facility_name']):
                    new_entry = Facility(**fac_data)
                    db.session.add(new_entry)
                    db.session.commit()
                    print(f"Added new facility: {fac_data['facility_name']}")

            flash('Data uploaded successfully!', 'success')
            return redirect(url_for('landing'))
    return render_template("uploadfacility.html")


@app.route('/upload_data', methods=['GET', 'POST'])
@requires_roles('sysadmin','admin')
def upload_data():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submits an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Read the file and process the data
            if filename.endswith('.csv'):
                df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            elif filename.endswith('.xls') or filename.endswith('.xlsx'):
                df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            elif filename.endswith('.json'):
                df = pd.read_json(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            elif filename.endswith('.xml'):
                df = pd.read_xml(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            
            # Remove text within brackets (including the brackets) and question marks from column names
            df.columns = df.columns.str.replace(r'\s*[\(\[].*?[\)\]]|\?', '', regex=True)
            
            #clean data 
            df = clean_dataframe(df)
            
            # If 'last_pickup_date' is na, fill it with the corresponding 'art_start_date'
            df['last_pickup_date'] = df['last_pickup_date'].fillna(df['art_start_date'])

            # convert to datetime.
            df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], dayfirst=True)
            df['art_start_date'] = pd.to_datetime(df['art_start_date'], dayfirst=True)
            df['last_pickup_date'] = pd.to_datetime(df['last_pickup_date'], dayfirst=True)

            df['months_of_arv_refill'] = df['months_of_arv_refill'].fillna(1)
            df['current_art_regimen'] = df['current_art_regimen'].fillna('TDF-3TC-DTG')
            
            df['age'] = df.apply(lambda row: calculate_age(row['date_of_birth'], row['last_pickup_date']), axis=1)
            df['tx_age'] = df.apply(lambda row: calculate_age_in_months(row['art_start_date'], row['last_pickup_date']), axis=1)
            #df['curr_ll'] = df.apply(lambda row: curr(row['last_pickup_date'], row['cutoff'], row['grace_period']), axis=1)

            #df['next'] = df['last_pickup_date'] + pd.to_timedelta(df['months_of_arv_refill'] * 30, unit='days')

            df['curr_ll'] = df.apply(lambda row: curr(row['last_pickup_date'], row['months_of_arv_refill'], cutoff, grace_period), axis=1)
        

            # Retrieve the list of facility names from the Facility table
            existing_facilities = get_facility_names()

            # If the list of existing facilities is empty, prompt the user to upload facility data first
            if not existing_facilities:
                flash('No facilities found. Please upload facility data first.', 'warning')
                return redirect(url_for('upload_facility'))

            # Find the unique facilities in the DataFrame
            unique_facilities_in_df = df['facility'].unique()

            # Find the missing facilities
            missing_facilities = list(set(unique_facilities_in_df) - set(existing_facilities))

            # If there are any missing facilities, prompt the user to upload the missing facility data first
            if missing_facilities:
                missing_facilities_str = ', '.join(missing_facilities)
                flash(f'Missing facilities found: {missing_facilities_str}. Please upload the missing facility data first.', 'warning')
                return redirect(url_for('upload_facility'))

            # Filter the DataFrame to only include records with matching facility names
            df = df[df['facility'].isin(existing_facilities)]


            # Process the data and save it to the database
            column_mapping = {
                'facility': 'facility_name',
                'unique_id': 'client_id',
                'patient_id': 'client_name',
                'sex': 'sex',
                'age': 'age',
                'tx_age': 'tx_age',
                'current_art_regimen': 'dregimen_ll',
                'months_of_arv_refill': 'mrefill_ll',
                'last_pickup_date': 'laspud_ll',
                'curr_ll': 'curr_ll'
            }

            
            # Process the data and save it to the database -DataEntry table
            for index, row in df.iterrows():
                entry_data = {}
                for file_col, data_entry_col in column_mapping.items():
                    if file_col in df.columns:  # Check if the file_col exists in the DataFrame
                        entry_data[data_entry_col] = row[file_col]
                    else:
                        entry_data[data_entry_col] = None  # Assign a default value (e.g., None) if the file_col is missing
                if not entry_exists(entry_data['client_id'], entry_data['facility_name']):
                    new_entry = DataEntry(**entry_data)
                    db.session.add(new_entry)
                    db.session.commit()

            

            flash('Data uploaded successfully!', 'success')
            return redirect(url_for('landing'))
    return render_template('uploaddata.html')


@app.route('/validate_client_record', methods=['GET', 'POST'])
@requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator')
def validate_client_record():
    form = ValidateRecordForm(request.form)
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('landing'))
        
        if not client_record.dregimen_po_correct:
            client_record.dregimen_po_correct = form.dregimen_po_correct.data
        if not client_record.dregimen_pw_correct:
            client_record.dregimen_pw_correct = form.dregimen_pw_correct.data
        if not client_record.laspud_po_correct:
            client_record.laspud_po_correct = form.laspud_po_correct.data
        if not client_record.laspud_pw_correct:
            client_record.laspud_pw_correct = form.laspud_pw_correct.data
        if not client_record.quantityd_po_correct:
            client_record.quantityd_po_correct = form.quantityd_po_correct.data
        if not client_record.quantityd_pw_correct: 
            client_record.quantityd_pw_correct = form.quantityd_pw_correct.data

        db.session.commit()
        flash('Client record validated successfully.', 'success')
        return redirect(url_for('landing'))
   
    return render_template('validate_client_record.html', form=form)

@app.route('/validate_pharm_record', methods=['GET', 'POST'])
@requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator')
def validate_pharm_record():
    form = ValidateRecordForm(request.form)
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('landing'))
        
        if not client_record.dregimen_po_correct:
            client_record.dregimen_po_correct = form.dregimen_po_correct.data
        if not client_record.dregimen_pw_correct:
            client_record.dregimen_pw_correct = form.dregimen_pw_correct.data
        if not client_record.laspud_po_correct:
            client_record.laspud_po_correct = form.laspud_po_correct.data
        if not client_record.laspud_pw_correct:
            client_record.laspud_pw_correct = form.laspud_pw_correct.data
        if not client_record.quantityd_po_correct:
            client_record.quantityd_po_correct = form.quantityd_po_correct.data
        if not client_record.quantityd_pw_correct: 
            client_record.quantityd_pw_correct = form.quantityd_pw_correct.data

        db.session.commit()
        flash('Client record validated successfully.', 'success')
        return redirect(url_for('landing'))
   
    return render_template('validate_pharm_record.html', form=form)


def po_entry_exists(client_id, laspud_po):
    existing_entry = DataEntry.query.filter_by(client_id=client_id, laspud_po=laspud_po).first()
    return existing_entry is not None

@app.route('/client_record', methods=['GET', 'POST'])
@requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator', 'dataentrant')
def client_record():
    form = FacilityForm(request.form)
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('landing'))
        
        if not client_record.dregimen_po:
            client_record.dregimen_po = form.dregimen_po.data
        if not client_record.mrefill_po:
            client_record.mrefill_po = form.mrefill_po.data
        if not client_record.laspud_po:
            client_record.laspud_po = form.laspud_po.data
        if not client_record.quantityd_po:
            client_record.quantityd_po = form.quantityd_po.data
        if not client_record.client_folder:
            client_record.client_folder = form.client_folder.data

        client_record.userid_cr = current_user.id
        client_record.curr_cr = curr(client_record.laspud_po, client_record.mrefill_po, cutoff, grace_period)

        # Store the current date and time in the database as entry_datetime
        client_record.entry_datetime_cr = datetime.now()

        # Save the changes to the database
        db.session.commit()

        flash('Client record updated successfully.', 'success')
        return redirect(url_for('landing'))
    

    return render_template('facility.html', form=form)

@app.route('/update_client_record', methods=['GET', 'POST'])
@requires_roles('sysadmin','admin')
def update_client_record():
    form = FacilityForm(request.form)
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('landing'))
        
        client_record.dregimen_po = form.dregimen_po.data
        client_record.mrefill_po = form.mrefill_po.data
        client_record.laspud_po = form.laspud_po.data
        client_record.quantityd_po = form.quantityd_po.data
        client_record.client_folder = form.client_folder.data
        client_record.userid_cr = current_user.id
        client_record.curr_cr = curr(client_record.laspud_po, cutoff, grace_period)


        db.session.commit()
        flash('Client record updated successfully.', 'success')
        return redirect(url_for('landing'))
    

    return render_template('update_client_record.html', form=form)

@app.route('/pharm_record', methods=['GET', 'POST'])
@requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator', 'dataentrant')
def pharm_record():
    form = PhamarcyForm(request.form)
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('landing'))
        
        if not client_record.dregimen_pw:
            client_record.dregimen_pw = form.dregimen_pw.data
        if not client_record.mrefill_pw:
            client_record.mrefill_pw = form.mrefill_pw.data
        if not client_record.laspud_pw:
            client_record.laspud_pw = form.laspud_pw.data
        if not client_record.quantityd_pw:
            client_record.quantityd_pw = form.quantityd_pw.data
        if not client_record.pharm_doc:
            client_record.pharm_doc = form.pharm_doc.data

        client_record.userid_pr = current_user.id
        client_record.curr_pr = curr(client_record.laspud_pw, client_record.mrefill_pw, cutoff, grace_period)

        # Store the current date and time in the database as entry_datetime
        client_record.entry_datetime_pr = datetime.now()

        # Save the changes to the database
        db.session.commit()
        
        flash('Client record updated successfully.', 'success')
        return redirect(url_for('landing'))
    

    return render_template('pharmrecord.html', form=form)

@app.route('/update_pharm_record', methods=['GET', 'POST'])
@requires_roles('sysadmin','admin')
def update_pharm_record():
    form = PhamarcyForm(request.form)
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('landing'))
        
        client_record.dregimen_pw = form.dregimen_pw.data
        client_record.mrefill_pw = form.mrefill_pw.data
        client_record.laspud_pw = form.laspud_pw.data
        client_record.quantityd_pw = form.quantityd_pw.data
        client_record.pharm_doc= form.pharm_doc.data
        client_record.userid_pr = current_user.id
        client_record.curr_pr = curr(client_record.laspud_pw, cutoff, grace_period)


        db.session.commit()
        flash('Client record updated successfully.', 'success')
        return redirect(url_for('landing'))
    
    return render_template('update_pharm_record.html', form=form)

@app.route('/get_client_ids')
def get_client_ids():
    facility_name = request.args.get('facility_name', type=str)
    clients = DataEntry.query.filter_by(facility_name=facility_name).all()
    client_id_choices = [(c.client_id, c.client_id) for c in clients]

    return jsonify(client_id_choices)

@app.route('/get_client_ids_validate_cr')
def get_client_ids_validate_cr():
    facility_name = request.args.get('facility_name', type=str)
    clients = DataEntry.query.filter_by(facility_name=facility_name).all()
    client_id_choices = [
        (c.client_id, c.client_id) for c in clients
        if c.dregimen_po or c.laspud_po or c.quantityd_po
    ]

    return jsonify(client_id_choices)

@app.route('/get_client_ids_validate_pr')
def get_client_ids_validate_pr():
    facility_name = request.args.get('facility_name', type=str)
    clients = DataEntry.query.filter_by(facility_name=facility_name).all()
    client_id_choices = [
        (c.client_id, c.client_id) for c in clients
        if c.dregimen_pw or c.laspud_pw or c.quantityd_pw
    ]

    return jsonify(client_id_choices)


@app.route('/get_client_data', methods=['GET'])
def get_client_data():
    client_id = request.args.get('client_id')
    client_data = DataEntry.query.filter_by(client_id=client_id).first()

    if client_data:
        response = client_data.to_dict()
    else:
        print("Client data not found")  # Debugging line
        response = {
            'dregimen_po': '',
            'laspud_po': '',
            'quantityd_po': ''
        }

    return jsonify(response)



@app.cli.command('drop-data-entry-table')
#@requires_roles('sysadmin')
def drop_data_entry_table():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(table_names)
        if 'data_entry' in table_names:
            sql = text('DROP TABLE data_entry;')
            result = db.session.execute(sql)
            db.session.commit()
            print("Dropped table 'data_entry' successfully.")
        else:
            print("Table not found.")
# flask drop-data-entry-table


@app.cli.command('drop-facility_name_item-table')
#@requires_roles('sysadmin')
def drop_data_facility_name_table():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(table_names)
        if 'facility_name_item' in table_names:
            sql = text('DROP TABLE facility_name_item;')
            result = db.session.execute(sql)
            db.session.commit()
            print("Dropped table 'facility_name_item' successfully.")
        else:
            print("Table not found.")
# flask drop-facility_name_item-table

@app.cli.command('drop-client_id_item-table')
#@requires_roles('sysadmin')
def drop_data_client_id_table():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(table_names)
        if 'client_id_item' in table_names:
            sql = text('DROP TABLE client_id_item;')
            result = db.session.execute(sql)
            db.session.commit()
            print("Dropped table 'client_id_item' successfully.")
        else:
            print("Table not found.")
# flask drop-client_id_item-table

@app.cli.command('drop-user-table')
#@requires_roles('sysadmin')
def drop_user_table():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(table_names)
        if 'user' in table_names:
            sql = text('DROP TABLE "user";')
            result = db.session.execute(sql)
            db.session.commit()
            print("Dropped table 'user' successfully.")
        else:
            print("Table not found.")
# flask drop-user-table

@app.cli.command('drop-facility-table')
#@requires_roles('sysadmin')
def drop_facility_table():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(table_names)
        if 'facility' in table_names:
            sql = text('DROP TABLE facility;')
            result = db.session.execute(sql)
            db.session.commit()
            print("Dropped table 'facility' successfully.")
        else:
            print("Table not found.")
# flask drop-facility-table

@app.cli.command('drop-user_id_item-table')
#@requires_roles('sysadmin')
def drop_data_user_id_table():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(table_names)
        if 'user_id_item' in table_names:
            sql = text('DROP TABLE user_id_item;')
            result = db.session.execute(sql)
            db.session.commit()
            print("Dropped table 'user_id_item' successfully.")
        else:
            print("Table not found.")
# flask drop-user_id_item-table

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.utcnow().year}

# @app.route('/dashboard_app')
# @requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator', 'dashboard')
# def dashboard_app():
#     cmd = "streamlit run dashboard_app.py"
#     process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
#     process.terminate()
#     return redirect("http://localhost:8501")

dash_app = init_dash(app)

@app.route('/dashboard')
@login_required
def render_dashboard():
    return dash_app.index() 


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='192.168.0.9', port=5000, debug=True)
