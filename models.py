#from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

import os
from flask_sqlalchemy import SQLAlchemy

db_user = os.environ.get('DB_USER_ndqadata')
db_password = os.environ.get('DB_PASSWORD_ndqadata')
db_host = os.environ.get('DB_HOST_ndqadata')
db_name = os.environ.get('DB_NAME_ndqadata') 

print(f' Database name: \t {db_name}')

db = SQLAlchemy()


# DataEntry class
# This define the main database - postgres
# that all store data collect using the system
class DataEntry(db.Model):
    userid = db.Column(db.Integer, nullable=True) # User Id, Id of the user making the entry
    facility_name = db.Column(db.String(100), nullable=False) # Name of the health facility been accessed - data loaded via bulk data uoplad
    facility_id = db.Column(db.String(100), nullable=True) # Id of the health facility (where available)
    geolocation = db.Column(db.String(100), nullable=True) # geolocation of the health facility (where available)
    client_id = db.Column(db.String(100), primary_key=True) # Unique Id of the client - patient
    name = db.Column(db.String(100), nullable=False) # Name of the client -  patient
    sex = db.Column(db.String(100), nullable=False)  # Sex of the client -  patient (binary M/F)
    age = db.Column(db.Integer, nullable=False) # Age of the client -  patient (when last seen - at last drug pickup) calculated from date_of_birth and last_pickup_date
    dregimen_ll = db.Column(db.String(100), nullable=True)  # current treatment regimen
    tx_age = db.Column(db.Integer, nullable=True)  # Treatment age, how long the client has been on trea
    dregimen_po = db.Column(db.String(100), nullable=True)
    dregimen_pw = db.Column(db.String(100), nullable=True)
    dregimen_po_correct = db.Column(db.Boolean, nullable=True)
    dregimen_pw_correct = db.Column(db.Boolean, nullable=True)
    mrefill_ll = db.Column(db.Integer, nullable=True)
    mrefill_po = db.Column(db.Integer, nullable=True)
    mrefill_pw = db.Column(db.Integer, nullable=True)
    laspud_ll = db.Column(db.Date, nullable=True)
    laspud_po = db.Column(db.Date, nullable=True)
    laspud_pw = db.Column(db.Date, nullable=True)
    laspud_po_correct = db.Column(db.Boolean, nullable=True)
    laspud_pw_correct = db.Column(db.Boolean, nullable=True)
    quantityd_po = db.Column(db.Integer, nullable=True)
    quantityd_pw = db.Column(db.Integer, nullable=True)
    quantityd_po_correct = db.Column(db.Boolean, nullable=True)
    quantityd_pw_correct = db.Column(db.Boolean, nullable=True)
    pharm_doc = db.Column(db.String(5), nullable=True)
    client_folder = db.Column(db.String(5), nullable=True)

    # def __repr__(self):
    #     return f'<DataEntry {self.first_name} {self.last_name}>'

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# User class
# This define the Use database - in postgres
# that all store user datsa needed forauthentication
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='dataentrant')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# class FacilityNameItem:
#     def __init__(self, facility_name):
#         self.facility_name = facility_name

# class ClientIdItem:
#     def __init__(self, client_id):
#         self.client_id = client_id

# class UserIdItem:
#     def __init__(self, user_id):
#         self.user_id = user_id

class FacilityNameItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facility_name = db.Column(db.String(128), unique=True)

class ClientIdItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(128), unique=True)

class UserIdItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)

