from flask import Flask, render_template, request, redirect, url_for, session, flash

import csv
import os

import re

from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

from forms import LoginForm, DataEntryForm

from io import StringIO
from flask import Response
from flask_migrate import Migrate
from flask import current_app
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.environ.get('FLASK_APP_SECRET_KEY', 'fallback_secret_key')

db_user = os.environ.get('DB_USER_ndqadata') #'ndqadata'
db_password = os.environ.get('DB_PASSWORD_ndqadata') #'*K5e1l0e7c4H5i95'
db_host = os.environ.get('DB_HOST_ndqadata') # 'localhost'
db_name = os.environ.get('DB_NAME_ndqadata') #'ndqadcollection'

print(f' Database name: \t {db_name}')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
db = SQLAlchemy(app)

class DataEntry(db.Model):
    userid = db.Column(db.Integer, nullable=True)
    facility_name = db.Column(db.String(100), nullable=False)
    facility_id = db.Column(db.String(100), nullable=True)
    geolocation = db.Column(db.String(100), nullable=True)
    client_id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    dregimen_ll = db.Column(db.String(100), nullable=True)
    tx_age = db.Column(db.Integer, nullable=True)
    dregimen_po = db.Column(db.String(100), nullable=True)
    dregimen_pw = db.Column(db.String(100), nullable=True)
    mrefill_ll = db.Column(db.Integer, nullable=True)
    mrefill_po = db.Column(db.Integer, nullable=True)
    mrefill_pw = db.Column(db.Integer, nullable=True)
    laspud_ll = db.Column(db.Date, nullable=True)
    laspud_po = db.Column(db.Date, nullable=True)
    laspud_pw = db.Column(db.Date, nullable=True)
    quantityd_po = db.Column(db.Integer, nullable=True)
    quantityd_pw = db.Column(db.Integer, nullable=True)


    # def __repr__(self):
    #     return f'<DataEntry {self.first_name} {self.last_name}>'

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# # Initialize the migration tool
# migrate = Migrate(app, db)


#db.create_all()

# @app.route('/')
# def index():
#     return render_template('index.html')

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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
    #return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("index.html")

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         user = User(username=form.username.data, email=form.email.data)
#         user.set_password(form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         flash('Your account has been created! You can now log in.', 'success')
#         return redirect(url_for('login'))
#     return render_template('login.html', title='Register', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('landing'))
    register_form = RegistrationForm()
    if register_form.validate_on_submit():
        user = User(username=register_form.username.data, email=register_form.email.data)
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('login'))
    return render_template('register.html', title='Register', register_form=register_form)

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


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user and user.check_password(form.password.data):
#             login_user(user)
#             flash('You have successfully logged in.', 'success')
#             next_page = request.args.get('next')
#             return redirect(next_page) if next_page else redirect(url_for('index'))
#         else:
#             flash('Login unsuccessful.  Please check your email and password.', 'danger')
#     return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    # Clear the user's session
    session.clear()
    db.session.remove()
    # Redirect the user to the login page or another page of your choice
    return redirect(url_for("home"))

 
# Route to render the download page
@app.route("/download")
@login_required
def download():
    return render_template("download.html")


@app.route('/download_csv', methods=['GET'])
def download_csv():
    # Query data from the database
    data = DataEntry.query.all()

    # Convert data to a list of dictionaries
    data_list = [row.to_dict() for row in data]

    # Create a CSV file in memory
    csv_file = StringIO()
    fieldnames = ['userid','facility_name','facility_id','geolocation','client_id','name','age','sex','dregimen_ll','tx_age','dregimen_po','dregimen_pw','mrefill_ll','mrefill_po','mrefill_pw','laspud_ll','laspud_po','laspud_pw','quantityd_po','quantityd_pw']  # Replace with your actual column names
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

@app.route("/landing")
@login_required
def landing():
    return render_template("landing.html")

@app.route("/data_entry", methods=["GET", "POST"])
@login_required
def data_entry():
    form = DataEntryForm()
    if form.validate_on_submit():
        # Process and store the form data here
        flash("Data entry submitted successfully.", "success")
        return redirect(url_for("data_entry"))
    return render_template("dataentry.html", form=form)

@app.route("/validate_entry")
@login_required
def validate_entry():
    return render_template("validate.html")

# Ensure the UPLOAD_FOLDER exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


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

@app.route('/upload', methods=['GET', 'POST'])
@login_required
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
            df['tx_age'] = df.apply(lambda row: calculate_age(row['art_start_date'], row['last_pickup_date']), axis=1)


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

@app.cli.command('drop-data-entry-table')
def drop_data_entry_table():
    with app.app_context():
        sql = text('DROP TABLE IF EXISTS data_entry;')
        result = db.session.execute(sql)
        db.session.commit()
        print("Dropped table 'data_entry' successfully.")
# flask drop-data-entry-table


#@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
