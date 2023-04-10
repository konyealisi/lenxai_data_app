from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

import csv
import os

import re

from sqlalchemy import text
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
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename
from functools import wraps

from forms import LoginForm, DataEntryForm, ValidationEntryForm, RegistrationFormAdmin, RegistrationFormSuperuser, ClientRecordUpdateForm,PharmacyRecordUpdateForm
from utils import facility_choices, client_choices, allowed_file, calculate_age, calculate_age_in_months, clean_dataframe
from models import db, User, DataEntry, FacilityNameItem, ClientIdItem, UserIdItem
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.environ.get('FLASK_APP_SECRET_KEY', 'fallback_secret_key')

db_user = os.environ.get('DB_USER_ndqadata')
db_password = os.environ.get('DB_PASSWORD_ndqadata')
db_host = os.environ.get('DB_HOST_ndqadata')
db_name = os.environ.get('DB_NAME_ndqadata')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'

db.init_app(app)

# Initialize the migration tool 
# this is used to modify the database schema 
# after it has been created
migrate = Migrate(app, db)

def populate_tables():
    facility_names = db.session.query(DataEntry.facility_name).distinct()
    client_ids = db.session.query(DataEntry.client_id).distinct()
    user_ids = db.session.query(User.id).distinct()

    for facility_name in facility_names:
        facility_name_item = FacilityNameItem.query.filter_by(facility_name=facility_name[0]).first()
        if not facility_name_item:
            new_facility_name_item = FacilityNameItem(facility_name=facility_name[0])
            db.session.add(new_facility_name_item)
            db.session.commit()

    for client_id in client_ids:
        client_id_item = ClientIdItem.query.filter_by(client_id=client_id[0]).first()
        if not client_id_item:
            new_client_id_item = ClientIdItem(client_id=client_id[0])
            db.session.add(new_client_id_item)
            db.session.commit()

    for user_id in user_ids:
        user_id_item = UserIdItem.query.filter_by(user_id=user_id[0]).first()
        if not user_id_item:
            new_user_id_item = UserIdItem(user_id=user_id[0])
            db.session.add(new_user_id_item)
            db.session.commit()

# custom decorator for restricting access to app 
# resources based on user roles and access level
def requires_roles(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('You do not have permission to access this page.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/get_data_entry', methods=['GET'])
def get_data_entry():
    facility_name = request.args.get('facility_name')
    client_id = request.args.get('client_id')

    # Fetch the DataEntry object based on the facility and client_id
    data_entry = DataEntry.query.filter_by(facility_id=facility_name, client_id=client_id).first()

    if data_entry is None:
        # Return an appropriate response when no data_entry is found
        return jsonify(
            error="No record found! Validation not posible at the moment. Check back when data has been entered!"
        )

    # Return the data_entry object as a JSON response
    return jsonify(
        dregimen_po=data_entry.dregimen_po,
        dregimen_pw=data_entry.dregimen_pw,
        laspud_po=data_entry.laspud_po,
        laspud_pw=data_entry.laspud_pw,
        quantityd_po=data_entry.quantityd_po,
        quantityd_pw=data_entry.quantityd_pw
    )


# 
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        userid = request.form['userid']
        facility_name = request.form['facility_name']
        facility_id = request.form['facility_id']
        geolocation = request.form['geolocation']
        client_id = request.form['client_id']
        name = request.form['name']
        age = request.form['age']
        sex = request.form['sex']
        dregimen_ll = request.form['dregimen_ll']
        tx_age = request.form['tx_age']
        dregimen_po = request.form['dregimen_po']
        dregimen_pw = request.form['dregimen_pw']
        mrefill_ll = request.form['mrefill_ll']
        mrefill_po = request.form['mrefill_po']
        mrefill_pw = request.form['mrefill_pw']
        laspud_ll = request.form['laspud_ll']
        laspud_po = request.form['laspud_po']
        laspud_pw = request.form['laspud_pw']
        quantityd_po = request.form['quantityd_po']
        quantityd_pw = request.form['quantityd_pw']

        # # Perform validation checks
        # if not re.match(r'^\d{4}-\d{2}-\d{2}$', facility_id):
        #     flash('Invalid unique code format. Please use YYYY-MM-DD format.', 'error')
        #     return redirect(url_for('index'))

        # if not re.match(r'^\d{1,3}\.\d{6},\s?\d{1,3}\.\d{6}$', geolocation):
        #     flash('Invalid geolocation format. Please use latitude,longitude format with six decimal places.', 'error')
        #     return redirect(url_for('index'))

        # Save the data to the PostgreSQL database
        new_entry = DataEntry(
            userid=userid,
            facility_name=facility_name,
            facility_id=facility_id,
            geolocation=geolocation,
            client_id=client_id,
            name=name,
            age=age,
            sex=sex,
            dregimen_ll=dregimen_ll,
            tx_age=tx_age,
            dregimen_po=dregimen_po,
            dregimen_pw=dregimen_pw,
            mrefill_ll=mrefill_ll,
            mrefill_po=mrefill_po,
            mrefill_pw=mrefill_pw,
            laspud_ll=laspud_ll,
            laspud_po=laspud_po,
            laspud_pw=laspud_pw,
            quantityd_po=quantityd_po,
            quantityd_pw=quantityd_pw
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Data submitted successfully!', 'success')
        return redirect(url_for('index'))

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# login manager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Home route
@app.route("/")
def home():
    return render_template("index.html")

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
    return redirect(url_for("home"))

 
# Route to render the download page - this redirects to the download_csv route
@app.route("/download")
@requires_roles('sysadmin', 'admin', 'superuser')
def download():
    return render_template("download.html")

# Download_csv route - let authorized user (sysadmin, admin, superuser) download 
# data entered and stored by the platform
@app.route('/download_csv', methods=['GET'])
@requires_roles('sysadmin', 'admin', 'superuser')
def download_csv():
    # Query data from the database
    data = DataEntry.query.all()

    # Convert data to a list of dictionaries
    data_list = [row.to_dict() for row in data]

    # Create a CSV file in memory
    csv_file = StringIO()
    fieldnames = ['userid','facility_name','facility_id','geolocation','client_id','name','age','sex','dregimen_ll','tx_age','dregimen_po','dregimen_pw','mrefill_ll','mrefill_po','mrefill_pw','laspud_ll','laspud_po','laspud_pw','quantityd_po','quantityd_pw','client_folder', 'laspud_pw_correct', 'dregimen_po_correct', 'quantityd_pw_correct', 'dregimen_pw_correct', 'pharm_doc', 'laspud_po_correct', 'quantityd_po_correct']  # Replace with your actual column names
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for row in data_list:
        writer.writerow(row)

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

# Ensure the UPLOAD_FOLDER exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


@app.route('/upload', methods=['GET', 'POST'])
@requires_roles('sysadmin','admin')
def upload_file():
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
            df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], dayfirst=True)
            df['art_start_date'] = pd.to_datetime(df['art_start_date'], dayfirst=True)
            df['last_pickup_date'] = pd.to_datetime(df['last_pickup_date'], dayfirst=True)
            
            df['age'] = df.apply(lambda row: calculate_age(row['date_of_birth'], row['last_pickup_date']), axis=1)
            df['tx_age'] = df.apply(lambda row: calculate_age_in_months(row['art_start_date'], row['last_pickup_date']), axis=1)


            # Process the data and save it to the database
            column_mapping = {
                'facility': 'facility_name',
                'u_code': 'facility_id',
                'geo_loc': 'geolocation',
                'unique_id': 'client_id',
                'patient_id': 'name',
                'sex': 'sex',
                'age': 'age',
                'tx_age': 'tx_age',
                'current_art_regimen': 'dregimen_ll',
                'months_of_arv_refill': 'mrefill_ll',
                'last_pickup_date': 'laspud_ll',
            }


            # Process the data and save it to the database
            for index, row in df.iterrows():
                entry_data = {}
                for file_col, data_entry_col in column_mapping.items():
                    if file_col in df.columns:  # Check if the file_col exists in the DataFrame
                        entry_data[data_entry_col] = row[file_col]
                    else:
                        entry_data[data_entry_col] = None  # Assign a default value (e.g., None) if the file_col is missing

                new_entry = DataEntry(**entry_data)
                db.session.add(new_entry)
                db.session.commit()

            flash('Data uploaded successfully!', 'success')
            return redirect(url_for('landing'))
    return render_template('upload.html')

# # Create a new route for the validation page -to be completed
# @app.route('/validate', methods=['GET', 'POST'])
# @login_required
# def validate():
#     form = ValidationEntryForm()
#     if form.validate_on_submit():
#         # Perform validation or any other operation here
#         flash('Data validated successfully', 'success')
#         return redirect(url_for('validate'))
#     return render_template('ventry.html', title='Validate', form=form)

@app.route('/validate', methods=['GET', 'POST'])
@requires_roles('sysadmin','admin', 'superuser', 'datavalidator')
def validate():
    form = ValidationEntryForm()

    if form.validate_on_submit():
        # Find the record to update
        record = DataEntry.query.filter_by(facility=form.facility.data, client_id=form.client_id.data).first()
        if record:
            # Update the record
            record.dregimen_po_correct = form.dregimen_po_correct.data
            record.dregimen_pw_correct = form.dregimen_pw_correct.data
            record.laspud_po_correct = form.laspud_po_correct.data
            record.laspud_pw_correct = form.laspud_pw_correct.data
            record.quantityd_po_correct = form.quantityd_po_correct.data
            record.quantityd_pw_correct = form.quantityd_pw_correct.data

            db.session.commit()
            flash('Data entry has been validated and updated.', 'success')
        else:
            flash('No data entry found for the selected facility and client_id.', 'danger')

    # Call get_data_entry function and get the JSON response
    data_entry_response = get_data_entry()

    # Check if the response is a dictionary or a JSON object
    if isinstance(data_entry_response, dict):
        data_entry = data_entry_response
    else:
        data_entry = data_entry_response.json

    # Check for an error in the response
    error_message = data_entry.get('error', None)
    
    return render_template('validate.html', form=form, data_entry=data_entry, error_message=error_message)

@app.route('/update_client_record', methods=['GET', 'POST'])
@login_required
def update_client_record():
    form = ClientRecordUpdateForm()

    if form.validate_on_submit():
        client_id_value = form.client_id.data.client_id
        client_record = DataEntry.query.filter_by(client_id=client_id_value, facility_name=form.facility.data.facility_name).first()

        if not client_record:
            flash('Client record not found.', 'danger')
            return redirect(url_for('landing'))

        client_record.dregimen_po = form.dregimen_po.data
        client_record.mrefill_po = form.mrefill_po.data
        client_record.laspud_po = form.laspud_po.data
        client_record.quantityd_po = form.quantityd_po.data
        client_record.client_folder = form.client_folder.data
        client_record.userid = current_user.id

        db.session.commit()
        flash('Client record updated successfully.', 'success')
        return redirect(url_for('landing'))

    return render_template('update_client_record.html', form=form)

@app.route('/update_pharm_record', methods=['GET', 'POST'])
@login_required
def update_pharm_record():
    form = PharmacyRecordUpdateForm()

    if form.validate_on_submit():
        client_id_value = form.client_id.data.client_id
        client_record = DataEntry.query.filter_by(client_id=client_id_value, facility_name=form.facility.data.facility_name).first()

        if not client_record:
            flash('Client record not found.', 'danger')
            return redirect(url_for('landing'))

        client_record.dregimen_pw = form.dregimen_pw.data
        client_record.mrefill_pw = form.mrefill_pw.data
        client_record.laspud_pw = form.laspud_pw.data
        client_record.quantityd_pw = form.quantityd_pw.data
        client_record.pharm_doc = form.pharm_doc.data
        client_record.userid = current_user.id

        db.session.commit()
        flash('Client record updated successfully.', 'success')
        return redirect(url_for('landing'))

    return render_template('update_pharm_record.html', form=form)


@app.cli.command('drop-data-entry-table')
#@requires_roles('sysadmin')
def drop_data_entry_table():
    with app.app_context():
        sql = text('DROP TABLE IF EXISTS data_entry;')
        result = db.session.execute(sql)
        db.session.commit()
        print("Dropped table 'data_entry' successfully.")
# flask drop-data-entry-table

@app.cli.command('drop-facility_name_item-table')
#@requires_roles('sysadmin')
def drop_data_entry_table():
    with app.app_context():
        sql = text('DROP TABLE IF EXISTS facility_name_item;')
        result = db.session.execute(sql)
        db.session.commit()
        print("Dropped table 'facility_name_item' successfully.")
# flask drop-facility_name_item-table


# @app.cli.command('drop-user-table')
# def drop_user_table():
#     with app.app_context():
#         sql = text('DROP TABLE IF EXISTS "user" CASCADE;')
#         result = db.session.execute(sql)
#         db.session.commit()
#         print("Dropped table 'user' successfully.")
# # flask drop-user-table

from flask.cli import AppGroup

# Create a group of commands for user management
user_cli = AppGroup('user')

# Drop the user table if the current user is an admin
@user_cli.command('drop_table')
#@requires_roles('sysadmin')
def drop_user_table():
    # Check if the current user is an admin
    #if current_user.is_authenticated and current_user.role == 'admin':
        with current_app.app_context():
            sql = text('DROP TABLE IF EXISTS "user" CASCADE;')
            db.session.execute(sql)
            db.session.commit()
            print("User table dropped.")
    #else:
     #   print("Only admins can perform this action.")
# Register the command group with the app
app.cli.add_command(user_cli)
#flask user drop_table

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.utcnow().year}

#@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Call the function to populate the tables
        populate_tables()
    app.run(debug=True)
