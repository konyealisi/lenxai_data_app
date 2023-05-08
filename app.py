from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Request

import csv
import os
import subprocess
import re
import json
from xml.etree.ElementTree import Element, SubElement, tostring
from decimal import Decimal


from sqlalchemy import text, create_engine, inspect, or_
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField, DateField, EmailField, FileField, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

from io import StringIO
from flask import Response, abort
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
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message, Mail

from dashboard import init_dash



app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.environ.get('FLASK_APP_SECRET_KEY', 'fallback_secret_key')

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
sender_username = secrets.get('sender_username', None)
sender_passward = secrets.get('sender_passward', None)
sender_server = secrets.get('sender_server', None)

# Check if any of the required values are missing
if None in (db_user, db_password, db_host, db_name):
    print("Error: Missing database configuration values in the JSON file.")
    exit(1)

# # Database connection settings
# db_user = os.environ.get('DB_USER_ndqadata')
# db_password = os.environ.get('DB_PASSWORD_ndqadata')
# db_host = os.environ.get('DB_HOST_ndqadata')
# db_name = os.environ.get('DB_NAME_ndqadata')


app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'

# app.config.update(
#     MAIL_SERVER=sender_server,
#     MAIL_PORT=465,
#     MAIL_USE_SSL=True,
#     MAIL_USERNAME=sender_username,
#     MAIL_PASSWORD=sender_passward
# )
# mail = Mail(app)

# db = SQLAlchemy()
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

def get_user_accessible_facilities(user):
    if user.role == 'sysadmin' or user.role == 'admin':
        return Facility.query.all()
    elif user.role == 'superuser' or user.role == 'datavalidator' or user.role == 'dataentrant':
        return Facility.query.filter_by(state=user.state).all()
    else:
        return []

def get_requested_state():
    return request.view_args.get('state')

def get_requested_facility():
    return request.view_args.get('facility')

def requires_data_permission(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Login required.')
            return redirect(url_for('login'))

        requested_state = get_requested_state(*args, **kwargs)
        requested_facility = get_requested_facility(*args, **kwargs)

        if not current_user.has_permission(requested_state, requested_facility):
            flash('You do not have permission to access this page.')
            return redirect(url_for('landing'))

        return f(*args, **kwargs)
    return decorated_function

def requires_roles_and_data_permission(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                abort(401)

            current_user = User.query.get(session['user_id'])
            has_required_roles = all(current_user.has_role(role) for role in roles)

            if not has_required_roles:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('landing')) #render_template('index.html', title='Home')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# login manager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def get_facility_choices():
    facilities = Facility.query.all()
    facility_choices = [(facility.id, facility.facility_name) for facility in facilities]
    return facility_choices

# login route - for login in and gaining access to the platform
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('landing'))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and user.check_password(login_form.password.data):

            # if user.is_active:
            #     login_user(user)
            #     flash('You have successfully logged in.', 'success')
            #     next_page = request.args.get('next')
            #     return redirect(next_page) if next_page else redirect(url_for('landing'))
            # else:
            #     return "Please verify your email before logging in."
            login_user(user)
            flash('You have successfully logged in.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('landing'))
        else:
            flash('Login unsuccessful.  Please check your email and password.', 'danger')
    return render_template('login.html', title='Login', login_form=login_form)#, register_form=register_form)


# s = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# def generate_confirmation_token(email):
#     return s.dumps(email, salt=app.config["SECURITY_PASSWORD_SALT"])

# def confirm_token(token, expiration=3600):
#     return s.loads(token, salt=app.config["SECURITY_PASSWORD_SALT"], max_age=expiration)

# @app.route('/confirm_email/<token>')
# def confirm_email(token):
#     try:
#         email = confirm_token(token)
#     except Exception as e:
#         return str(e)

#     user = User.query.filter_by(email=email).first()

#     if user:
#         user.is_active = True
#         db.session.commit()
#         return "Email confirmed successfully!"
#     else:
#         return "User not found!"


# def send_verification_email(email, token):
#     confirm_url = url_for('confirm_email', token=token, _external=True)
#     msg = Message("Please Confirm Your Email", sender="noreply@example.com", recipients=[email])
#     msg.body = f"Click the following link to confirm your email: {confirm_url}"
#     mail.send(msg)


@app.route('/register', methods=['GET', 'POST'])
@requires_roles('sysadmin', 'admin', 'superuser')
def register():
    if not current_user.is_authenticated or current_user.role not in ['sysadmin', 'admin', 'superuser']:
        flash("You don't have permission to access this page.")
        return redirect(url_for('index'))

    register_form = RegistrationFormAdmin()
    register_form.state.choices = [f.state for f in Facility.query.distinct(Facility.state)]
    register_form.facility_name.choices = get_facility_choices()

    if request.method == 'POST':
        form_data = request.form
        print(f"Form data: {form_data}")

        username = form_data.get('username')
        email = form_data.get('email')
        password = form_data.get('password')
        confirm_password = form_data.get('confirm_password')
        role = form_data.get('role')
        state = form_data.get('state')
        facility_name = form_data.get('facility_name')

        if password == confirm_password:
            user = User(
                username=username,
                email=email,
                role=role,
                state=state if state != '' else None,
                facility_name=facility_name if facility_name != '' else None#, is_active=False
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            # # Send the email verification link
            # token = generate_confirmation_token(email)
            # send_verification_email(email, token)

            # return "Registration successful! Please verify your email."

            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash("Passwords do not match.", 'error')

    return render_template('register.html', title='Register', register_form=register_form)


# def send_password_reset_email(email, token):
#     reset_url = url_for('reset_password', token=token, _external=True)
#     msg = Message("Reset Your Password", sender="noreply@example.com", recipients=[email])
#     msg.body = f"Click the following link to reset your password: {reset_url}"
#     mail.send(msg)

# # Route to handle password reset request
# @app.route('/forgot_password', methods=["POST"])
# def forgot_password():
#     email = request.form["email"]
    
#     # Verify if the email exists in your database
#     user = User.query.filter_by(email=email).first()
    
#     if user:
#         token = generate_confirmation_token(email)
#         send_password_reset_email(email, token)
#         flash("Password reset email sent!", "success")
#         # You can redirect to a relevant page, such as the login page
#         return redirect(url_for("login"))
#     else:
#         flash("Email address not found!", "error")
#         # Redirect to the same forgot_password page or another relevant page
#         return redirect(url_for("forgot_password"))

# @app.route('/reset_password/<token>', methods=["GET", "POST"])
# def reset_password(token):
#     try:
#         email = confirm_token(token)
#     except Exception as e:
#         return str(e)

#     user = User.query.filter_by(email=email).first()
#     if user is None:
#         flash("Invalid token or email not found!", "error")
#         return redirect(url_for("forgot_password"))

#     if request.method == "POST":
#         new_password = request.form["new_password"]
        
#         # Update the user's password in the database
#         user.password = generate_password_hash(new_password)
#         db.session.commit()

#         flash("Password reset successfully!", "success")
#         return redirect(url_for("login"))

#     return render_template("reset_password.html", token=token)


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


from flask_login import current_user  # Add this import at the top of your file if it's not there

@app.route('/download_csv', methods=['GET'])
@requires_roles('sysadmin', 'admin', 'superuser')
def download_csv():
    # Get the current user

    # If the user is not assigned to a specific state or facility, return all data
    if (current_user.state is None or current_user.state == 'All states') and (current_user.facility_name is None or current_user.facility_name == 'All facilities'):
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name).all()
    # If the user is assigned to a specific state and all facilities within that state
    elif current_user.state != 'All states' and (current_user.facility_name is None or current_user.facility_name == 'All facilities'):
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name)\
            .filter(Facility.state == current_user.state).all()
    # If the user is assigned to a specific state and a specific facility
    else:
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name)\
            .filter(Facility.state == current_user.state)\
            .filter(Facility.facility_name == current_user.facility_name).all()

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
    fieldnames = ['facility_name', 'id', 'state', 'lga', 'latitude', 'longitude', 'client_id', 'client_name', 'sex', 'age', 'tx_age', 'dregimen_ll', 'mrefill_ll', 'laspud_ll', 'curr_ll',
                    'userid_cr', 'entry_datetime_cr', 'dregimen_po', 'mrefill_po', 'laspud_po', 'quantityd_po', 'curr_cr', 'client_folder', 'dregimen_po_correct', 'laspud_po_correct', 'quantityd_po_correct',
                    'userid_pr', 'entry_datetime_pr', 'dregimen_pw', 'mrefill_pw', 'laspud_pw', 'quantityd_pw', 'curr_pr', 'pharm_doc', 'dregimen_pw_correct', 'laspud_pw_correct', 'quantityd_pw_correct']

    # Define user-friendly headers
    friendly_headers = ['Health Facility', 'Facility ID', 'State', 'LGA', 'Latitude', 'Longitude', 'Client ID', 'Client Name', 'Sex', 'Age', 'Tx Age (months)', 'Drug Regimen NDR', 'Month of Refill NDR', 'LAST Pick Up Date NDR', 'is Current on Tx NDR',
                        'User ID CR', 'Data Entry Time CR', 'Drug Regimen CR', 'Month of Refill CR', 'LAST Pick Up Date CR', 'Drug Quantity CR', 'is Current on Tx CR', 'Client Folder Sighted?', 'Drug Regimen CR Correct?', 'LAST Pick Up Date CR Correct?', 'Drug Quantity CR Correct?', 
                        'User ID PR', 'Data Entry Time PR', 'Drug Regimen PR', 'Month of Refill PR', 'LAST Pick Up Date PR', 'Drug Quantity PR', 'is Current on Tx PR', 'Pharmacy Documentation Sighted?', 'Drug Regimen PR Correct?', 'LAST Pick Up Date PR Correct?', 'Drug Quantity PR Correct?']
   
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


@app.route('/download_json', methods=['GET'])
@requires_roles('sysadmin', 'admin', 'superuser')
def download_json():
    # Get the current user

    # If the user is not assigned to a specific state or facility, return all data
    if (current_user.state is None or current_user.state == 'All states') and (current_user.facility_name is None or current_user.facility_name == 'All facilities'):
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name).all()
    # If the user is assigned to a specific state and all facilities within that state
    elif current_user.state != 'All states' and (current_user.facility_name is None or current_user.facility_name == 'All facilities'):
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name)\
            .filter(Facility.state == current_user.state).all()
    # If the user is assigned to a specific state and a specific facility
    else:
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name)\
            .filter(Facility.state == current_user.state)\
            .filter(Facility.facility_name == current_user.facility_name).all()

    # Convert data to a list of dictionaries
    data_list = []
    for row in data:
        data_entry = row.DataEntry.to_dict()
        facility = row.Facility.to_dict()

        # Merge the dictionaries and add the 'facility_id' from the Facility table
        merged_data = {**data_entry, **facility}
        data_list.append(merged_data)

    # Convert the data_list to a JSON string
    json_data = json.dumps(data_list, default=str)  # Use default=str to handle date and time objects

    # Serve the JSON data as a response
    response = Response(
        json_data,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=data.json'}
    )

    return response

@app.route('/download_xml', methods=['GET'])
@requires_roles('sysadmin', 'admin', 'superuser')
def download_xml():
    # Get the current user

    # If the user is not assigned to a specific state or facility, return all data
    if (current_user.state is None or current_user.state == 'All states') and (current_user.facility_name is None or current_user.facility_name == 'All facilities'):
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name).all()
    # If the user is assigned to a specific state and all facilities within that state
    elif current_user.state != 'All states' and (current_user.facility_name is None or current_user.facility_name == 'All facilities'):
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name)\
            .filter(Facility.state == current_user.state).all()
    # If the user is assigned to a specific state and a specific facility
    else:
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name)\
            .filter(Facility.state == current_user.state)\
            .filter(Facility.facility_name == current_user.facility_name).all()

    # Convert data to a list of dictionaries
    data_list = []
    for row in data:
        data_entry = row.DataEntry.to_dict()
        facility = row.Facility.to_dict()

        # Merge the dictionaries and add the 'facility_id' from the Facility table
        merged_data = {**data_entry, **facility}
        data_list.append(merged_data)

    # Create the root element of the XML tree
    root = Element('data_entries')

    # Add a new element for each row in data_list
    for row in data_list:
        entry = SubElement(root, 'entry')
        for key, value in row.items():
            elem = SubElement(entry, key)
            elem.text = str(value)

    # Convert the XML tree to a string
    xml_data = tostring(root, encoding='utf-8')

    # Serve the XML data as a response
    response = Response(
        xml_data,
        mimetype='application/xml',
        headers={'Content-Disposition': 'attachment;filename=data.xml'}
    )

    return response

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super(CustomJSONEncoder, self).default(obj)

@app.route('/api/data', methods=['GET'])
@requires_roles('sysadmin', 'admin', 'superuser')
def api_data():
    # Get the current user

    # If the user is not assigned to a specific state or facility, return all data
    if (current_user.state is None or current_user.state == 'All states') and (current_user.facility_name is None or current_user.facility_name == 'All facilities'):
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name).all()
    # If the user is assigned to a specific state and all facilities within that state
    elif current_user.state != 'All states' and (current_user.facility_name is None or current_user.facility_name == 'All facilities'):
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name)\
            .filter(Facility.state == current_user.state).all()
    # If the user is assigned to a specific state and a specific facility
    else:
        data = db.session.query(DataEntry, Facility).join(Facility, DataEntry.facility_name == Facility.facility_name)\
            .filter(Facility.state == current_user.state)\
            .filter(Facility.facility_name == current_user.facility_name).all()

    # Convert data to a list of dictionaries
    data_list = []
    for row in data:
        data_entry = row.DataEntry.to_dict()
        facility = row.Facility.to_dict()

        # Merge the dictionaries and add the 'facility_id' from the Facility table
        merged_data = {**data_entry, **facility}
        data_list.append(merged_data)

    # Convert data_list to JSON
    response_data = json.dumps(data_list, cls=CustomJSONEncoder)

    # Serve the JSON data as a response
    response = Response(
        response_data,
        content_type='application/json'
        # mimetype='application/json',
        # headers={'Content-Disposition': 'attachment;filename=data.json'}
    )

    return response

@app.route('/data/<string:state>/<string:facility>', methods=['GET', 'POST'])
@requires_data_permission
def data_view(state, facility):
    # Query the data based on the given state and facility
    data_entries = DataEntry.query.join(Facility).filter(Facility.state == state, Facility.facility_name == facility).all()

    # Convert the data entries to dictionaries
    data_dicts = [entry.to_dict() for entry in data_entries]

    # Return the data as a JSON response
    return jsonify(data_dicts)



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
            df = df.applymap(lambda s: s.lower() if isinstance(s, str) else s)

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
                'Region': 'region',
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

            # lower all values in the DataFrame
            df = df.applymap(lambda s: s.lower() if isinstance(s, str) else s)
        

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

            # Filter the DataFrame to only include records with curr_ll == 'yes'
            df = df[df['curr_ll'] == 'yes']

            print(f'Total records before samplling {len(df)}')

            # Function to perform sampling within each group
            def sample_group(group, chunk_size=11):
                chunks = [group.iloc[i:i + chunk_size] for i in range(0, group.shape[0], chunk_size)]
                sampled_chunks = pd.concat([chunk.sample(1) for chunk in chunks if len(chunk) == chunk_size], axis=0)
                return sampled_chunks

            # Group the DataFrame by facility and perform the sampling within each group
            sampled_df = df.groupby('facility', group_keys=True).apply(sample_group).reset_index(drop=True) #sampled_df = df.groupby('facility').apply(sample_group).reset_index(drop=True)

            print(f'Total records after samplling {len(sampled_df)}')

            # Process the data and save it to the database -DataEntry table
            for index, row in sampled_df.iterrows():
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
    #form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]
    # Get the list of facilities that the user has access to
    user_facilities = get_user_accessible_facilities(current_user)
    
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in user_facilities]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('validate_client_record'))
        
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
        return redirect(url_for('validate_client_record'))
   
    return render_template('validate_client_record.html', form=form)

@app.route('/validate_pharm_record', methods=['GET', 'POST'])
@requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator')
def validate_pharm_record():
    form = ValidateRecordForm(request.form)
    #form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]
    # Get the list of facilities that the user has access to
    user_facilities = get_user_accessible_facilities(current_user)
    
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in user_facilities]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('validate_pharm_record'))
        
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
        return redirect(url_for('validate_pharm_record'))
   
    return render_template('validate_pharm_record.html', form=form)


def po_entry_exists(client_id, laspud_po):
    existing_entry = DataEntry.query.filter_by(client_id=client_id, laspud_po=laspud_po).first()
    return existing_entry is not None

@app.route('/client_record', methods=['GET', 'POST'])
@requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator', 'dataentrant')
def client_record():
    form = FacilityForm(request.form)
    # Get the list of facilities that the user has access to
    user_facilities = get_user_accessible_facilities(current_user)
    
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in user_facilities]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('client_record'))
        
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
        return redirect(url_for('client_record'))
    

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
                return redirect(url_for('update_client_record'))
        
        client_record.dregimen_po = form.dregimen_po.data
        client_record.mrefill_po = form.mrefill_po.data
        client_record.laspud_po = form.laspud_po.data
        client_record.quantityd_po = form.quantityd_po.data
        client_record.client_folder = form.client_folder.data
        client_record.userid_cr = current_user.id
        client_record.curr_cr = curr(client_record.laspud_po, cutoff, grace_period)


        db.session.commit()
        flash('Client record updated successfully.', 'success')
        return redirect(url_for('update_client_record'))
    

    return render_template('update_client_record.html', form=form)

@app.route('/pharm_record', methods=['GET', 'POST'])
@requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator', 'dataentrant')
def pharm_record():
    form = PhamarcyForm(request.form)
    #form.facility_name.choices = [(f.facility_name, f.facility_name) for f in DataEntry.query.distinct(DataEntry.facility_name)]
    # Get the list of facilities that the user has access to
    user_facilities = get_user_accessible_facilities(current_user)
    
    form.facility_name.choices = [(f.facility_name, f.facility_name) for f in user_facilities]

    if request.method == 'POST':
        client_id = form.client_id.data
        # Do something with the selected client_id (e.g., save it to the database)
        client_record = DataEntry.query.filter_by(client_id=client_id, facility_name=form.facility_name.data).first()
       
        if not client_record:
                flash('Client record not found.', 'danger')
                return redirect(url_for('pharm_record'))
        
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
        return redirect(url_for('pharm_record'))
    

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
                return redirect(url_for('update_pharm_record'))
        
        client_record.dregimen_pw = form.dregimen_pw.data
        client_record.mrefill_pw = form.mrefill_pw.data
        client_record.laspud_pw = form.laspud_pw.data
        client_record.quantityd_pw = form.quantityd_pw.data
        client_record.pharm_doc= form.pharm_doc.data
        client_record.userid_pr = current_user.id
        client_record.curr_pr = curr(client_record.laspud_pw, cutoff, grace_period)


        db.session.commit()
        flash('Client record updated successfully.', 'success')
        return redirect(url_for('update_pharm_record'))
    
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

# Add a route to get facilities for a given state
@app.route('/get_facilities', methods=['GET'])
def get_facilities():
    state = request.args.get('state', None)
    if state:
        facilities = Facility.query.filter_by(state=state).all()
        return jsonify([f.to_dict() for f in facilities])
    else:
        return jsonify([])


@app.context_processor
def inject_current_year():
    return {'current_year': datetime.utcnow().year}

# @app.route('/dashboard_app')
# @requires_roles('sysadmin', 'admin', 'superuser', 'datavalidator', 'dashboard')
# def dashboard_app():
#     return render_template('new_dashboard.html')
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
    #app.run(host='192.168.0.9', port=5000, debug=True)
    app.run(debug=True, host='0.0.0.0')
