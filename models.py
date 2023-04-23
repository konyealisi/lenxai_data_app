#from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric, ForeignKey, Column, Integer, String, Date, Boolean
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import event

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
    userid_cr = db.Column(db.Integer, nullable=True) # User Id, Id of the user making the entry
    userid_pr = db.Column(db.Integer, nullable=True) # User Id, Id of the user making the entry
    #facility_name = db.Column(db.String(100), nullable=False) # Name of the health facility been accessed - data loaded via bulk data uoplad
    #facility_id = db.Column(db.String(100), nullable=True) # Id of the health facility (where available)
    facility_name = db.Column(db.String, ForeignKey("facility.facility_name"), nullable=True)
    facility = relationship("Facility", back_populates="client_records")
    client_id = db.Column(db.String(100), primary_key=True) # Unique Id of the client - patient
    client_name = db.Column(db.String(100), nullable=False) # Name of the client -  patient
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
    curr_ll = db.Column(db.String, nullable=True)
    curr_cr = db.Column(db.String, nullable=True)
    curr_pr = db.Column(db.String, nullable=True)
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
    entry_datetime_cr = db.Column(db.DateTime, nullable=True)
    entry_datetime_pr = db.Column(db.DateTime, nullable=True)

   
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

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    facility_name = db.Column(db.String(128), nullable=False, unique=True)
    client_records = relationship("DataEntry", back_populates="facility")
    country = db.Column(db.String(128), nullable=True)
    state = db.Column(db.String(128), nullable=True)
    lga = db.Column(db.String(128), nullable=True)
    latitude = db.Column(Numeric(precision=8, scale=4), nullable=True)
    longitude = db.Column(Numeric(precision=8, scale=4), nullable=True)
    facility_type = db.Column(db.String(128), nullable=True)
    facility_ownership = db.Column(db.String(128), nullable=True)
    funder = db.Column(db.String(128), nullable=True)
    implementing_partner = db.Column(db.String(128), nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def update_facility_after_data_entry_change(mapper, connection, target):
    # Retrieve the facility related to the changed data_entry
    facility = target.facility

    # Check if the facility attribute is not None
    if facility is not None:
        # Calculate the sum of the count of 'yes' for curr_ll in data_entry table for the facility
        Session = sessionmaker(bind=connection)
        session = Session()
        txcurr_ndr = session.query(DataEntry).filter(DataEntry.facility_name == facility.facility_name, DataEntry.curr_ll == 'yes').count()
        txcurr_cr = session.query(DataEntry).filter(DataEntry.facility_name == facility.facility_name, DataEntry.curr_cr == 'yes').count()
        txcurr_pr = session.query(DataEntry).filter(DataEntry.facility_name == facility.facility_name, DataEntry.curr_pr == 'yes').count()

        txcurr_ndr_vf = session.query(DataEntry).filter(
            DataEntry.facility_name == facility.facility_name,
            DataEntry.curr_ll == 'yes',
            DataEntry.curr_cr.isnot(None)  # Use the .isnot() method instead of !=
        ).count()

        txcurr_cr_vf = session.query(DataEntry).filter(
            DataEntry.facility_name == facility.facility_name,
            DataEntry.curr_ll.isnot(None),  # Use the .isnot() method instead of !=
            DataEntry.curr_cr == 'yes'
        ).count()
        # Calculate txcur_vf as txcurr_cr/txcurr_ndr to 2 decimal places
        if txcurr_ndr_vf != 0:
            txcur_vf = round(txcurr_cr_vf / txcurr_ndr_vf, 2)
        else:
            txcur_vf = None

        # Update the txcurr_ndr in the facility table
        facility.txcurr_ndr = txcurr_ndr
        facility.txcurr_cr = txcurr_cr
        facility.txcurr_pr = txcurr_pr
        facility.txcur_vf = txcur_vf

        # Commit the changes to the database
        session.merge(facility)
        session.commit()

# Add event listeners
event.listen(DataEntry, 'after_insert', update_facility_after_data_entry_change)
event.listen(DataEntry, 'after_update', update_facility_after_data_entry_change)
event.listen(DataEntry, 'after_delete', update_facility_after_data_entry_change)

#

# def update_all_facilities_txcurr_ndr():
#     # Get all the facilities
#     facilities = Facility.query.all()

#     for facility in facilities:
#         # Calculate the sum of the count of 'yes' for curr_ll in data_entry table for the facility
#         txcurr_ndr = DataEntry.query.filter(DataEntry.facility_name == facility.facility_name, DataEntry.curr_ll == 'yes').count()

#         # Update the txcurr_ndr in the facility table
#         facility.txcurr_ndr = txcurr_ndr

#     # Commit the changes to the database
#     db.session.commit()


# def update_all_facilities_txcurr_cr():
#     # Get all the facilities
#     facilities = Facility.query.all()

#     for facility in facilities:
#         # Calculate the sum of the count of 'yes' for curr_ll in data_entry table for the facility
#         txcurr_cr = DataEntry.query.filter(DataEntry.facility_name == facility.facility_name, DataEntry.curr_cr == 'yes').count()

#         # Update the txcurr_ndr in the facility table
#         facility.txcurr_cr = txcurr_cr

#     # Commit the changes to the database
#     db.session.commit()

# def update_all_facilities_txcurr_pr():
#     # Get all the facilities
#     facilities = Facility.query.all()

#     for facility in facilities:
#         # Calculate the sum of the count of 'yes' for curr_ll in data_entry table for the facility
#         txcurr_pr = DataEntry.query.filter(DataEntry.facility_name == facility.facility_name, DataEntry.curr_pr == 'yes').count()

#         # Update the txcurr_ndr in the facility table
#         facility.txcurr_pr = txcurr_pr

#     # Commit the changes to the database
#     db.session.commit()

# def update_all_facilities_txcurr_vf():
#     # Get all facilities
#     facilities = Facility.query.all()

#     # Loop through each facility and update txcurr_ndr, txcurr_cr, and txcur_vf
#     for facility in facilities:
#         txcurr_ndr_vf = DataEntry.query.filter(
#             DataEntry.facility_name == facility.facility_name, 
#             DataEntry.curr_ll == 'yes', 
#             DataEntry.curr_cr != None
#         ).count()
#         txcurr_cr_vf = DataEntry.query.filter(
#             DataEntry.facility_name == facility.facility_name, 
#             DataEntry.curr_ll != None, 
#             DataEntry.curr_cr == 'yes'
#         ).count()

#         if txcurr_ndr_vf != 0:
#             txcur_vf = round(txcurr_cr_vf / txcurr_ndr_vf, 2)
#         else:
#             txcur_vf = None
#         #txcur_vf = round(txcurr_cr / txcurr_ndr, 2)

#         # Update the txcurr_ndr, txcurr_cr, and txcur_vf in the facility table
#         # facility.txcurr_ndr = txcurr_ndr
#         # facility.txcurr_cr = txcurr_cr
#         facility.txcur_vf = txcur_vf

#         # Commit the changes to the database
#         db.session.add(facility)

#     db.session.commit()

def update_all_facilities():
    # Get all facilities
    facilities = Facility.query.all()

    # Loop through each facility and update txcurr_ndr, txcurr_cr, txcurr_pr, and txcur_vf
    for facility in facilities:
        txcurr_ndr = DataEntry.query.filter(
            DataEntry.facility_name == facility.facility_name,
            DataEntry.curr_ll == 'yes'
        ).count()

        txcurr_cr = DataEntry.query.filter(
            DataEntry.facility_name == facility.facility_name,
            DataEntry.curr_cr == 'yes'
        ).count()

        txcurr_pr = DataEntry.query.filter(
            DataEntry.facility_name == facility.facility_name,
            DataEntry.curr_pr == 'yes'
        ).count()

        # txcurr_ndr_vf = DataEntry.query.filter(
        #     DataEntry.facility_name == facility.facility_name,
        #     DataEntry.curr_ll == 'yes',
        #     DataEntry.curr_cr != None
        # ).count()

        # txcurr_cr_vf = DataEntry.query.filter(
        #     DataEntry.facility_name == facility.facility_name,
        #     DataEntry.curr_ll != None,
        #     DataEntry.curr_cr == 'yes'
        # ).count()

        txcurr_ndr_vf = DataEntry.query.filter(
            DataEntry.facility_name == facility.facility_name,
            DataEntry.curr_ll == 'yes',
            DataEntry.curr_cr.isnot(None)
        ).count()

        txcurr_cr_vf = DataEntry.query.filter(
            DataEntry.facility_name == facility.facility_name,
            DataEntry.curr_ll.isnot(None),
            DataEntry.curr_cr == 'yes'
        ).count()


        if txcurr_ndr_vf != 0:
            txcur_vf = round(txcurr_cr_vf / txcurr_ndr_vf, 2)
        else:
            txcur_vf = None

        # Update the txcurr_ndr, txcurr_cr, txcurr_pr, and txcur_vf in the facility table
        facility.txcurr_ndr = txcurr_ndr
        facility.txcurr_cr = txcurr_cr
        facility.txcurr_pr = txcurr_pr
        facility.txcur_vf = txcur_vf

        # Commit the changes to the database
        db.session.merge(facility)

    db.session.commit()

# Call the function to update all facilities
#update_all_facilities()



