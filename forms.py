from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField, DateField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
#from wtforms.ext.sqlalchemy.fields import QuerySelectField
from utils import validate_email, validate_username, facility_choices, client_choices
from wtforms_sqlalchemy.fields import QuerySelectField
from models import DataEntry, User, db

class DataEntryForm(FlaskForm):
    facility_name = StringField('Facility Name', validators=[DataRequired(), Length(max=100)])
    facility_id = StringField('Unique Code', validators=[DataRequired(), Length(max=100)])
    geolocation = StringField('Geolocation', validators=[DataRequired(), Length(max=100)])
    client_id = StringField('Client ID', validators=[DataRequired(), Length(max=100)])
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    sex = StringField('Sex', validators=[DataRequired(), Length(max=100)])
    age = IntegerField('Age', validators=[DataRequired()])
    dregimen_ll = StringField('DRegimen LL', validators=[Length(max=100)])
    dregimen_po = StringField('DRegimen PO', validators=[Length(max=100)])
    dregimen_pw = StringField('DRegimen PW', validators=[Length(max=100)])
    mrefill_ll = IntegerField('MRefill LL')
    mrefill_po = IntegerField('MRefill PO')
    mrefill_pw = IntegerField('MRefill PW')
    laspud_ll = DateField('LASPUD LL', format='%Y-%m-%d')
    laspud_po = DateField('LASPUD PO', format='%Y-%m-%d')
    laspud_pw = DateField('LASPUD PW', format='%Y-%m-%d')
    quantityd_po = IntegerField('QuantityD PO')
    quantityd_pw = IntegerField('QuantityD PW')
    submit = SubmitField('Submit')

# Registration form - Admin: this is the form for registering new users by the sysadmin and an admin user 
# with this access can be created for users with access level: admin, superuser, datavalidator, and dataentrant
# Note sysadmin is created during system set up
class RegistrationFormAdmin(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20), validate_username])
    email = StringField('Email', validators=[DataRequired(), Email(), validate_email])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('superuser', 'Superuser'), ('datavalidator', 'Data Validator'), ('dataentrant', 'Data Entrant'), ('dashboard', 'Dashboard Viewer')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

# Registration form - Superuser: this is the form for registering new users by a superuser
# with this access can be created for users with access level: admin, datavalidator, and dataentrant    
class RegistrationFormSuperuser(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20), validate_username])
    email = StringField('Email', validators=[DataRequired(), Email(), validate_email])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('datavalidator', 'Data Validator'), ('dataentrant', 'Data Entrant'), ('dashboard', 'Dashboard Viewer')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# class CustomEntryForm(FlaskForm):
#     facility_name = QuerySelectField(
#         'Facility Name',
#         query_factory=lambda: [FacilityNameItem(facility_name) for facility_name in db.session.query(DataEntry.facility_name).distinct()],
#         get_label='facility_name',
#         allow_blank=True,
#         blank_text='(Select a facility name)',
#     )
#     client_id = QuerySelectField(
#         'Client ID',
#         query_factory=lambda: [ClientIdItem(client_id) for client_id in db.session.query(DataEntry.client_id).distinct()],
#         get_label='client_id',
#         allow_blank=True,
#         blank_text='(Select a client ID)',
#     )
#     user_id = QuerySelectField(
#         'User ID',
#         query_factory=lambda: [UserIdItem(user_id) for user_id in db.session.query(User.id).distinct()],
#         get_label='user_id',
#         allow_blank=True,
#         blank_text='(Select a user ID)',
#     )


# # Add a new form for data validation
# def facility_name_choices():
#     return FacilityNameItem.query

# def client_id_choices():
#     return ClientIdItem.query

# def facility_name_choices():
#     return FacilityNameItem.query.order_by(FacilityNameItem.facility_name)

# def client_id_choices():
#     return ClientIdItem.query.order_by(ClientIdItem.client_id)

# class ValidationEntryForm(FlaskForm):
#     # facility = QuerySelectField('Facility', query_factory=facility_name_choices, get_label='facility_name', allow_blank=True, blank_text='Select a facility', get_pk=lambda x: x.id)
#     # client_id = QuerySelectField('Client ID', query_factory=client_id_choices, get_label='client_id', allow_blank=True, blank_text='Select a client ID', get_pk=lambda x: x.id)
#     # data_element = StringField('Data Element', validators=[DataRequired()])

#     facility = QuerySelectField('Facility', query_factory=facility_name_choices, get_label='facility_name', allow_blank=True, blank_text='Select a facility', get_pk=lambda x: x.id)
#     client_id = QuerySelectField('Client ID', query_factory=client_id_choices, get_label='client_id', allow_blank=True, blank_text='Select a client ID', get_pk=lambda x: x.id)

#     dregimen_po = StringField('dregimen_po')
#     dregimen_pw = StringField('dregimen_pw')
#     laspud_po = StringField('laspud_po')
#     laspud_pw = StringField('laspud_pw')
#     quantityd_po = StringField('quantityd_po')
#     quantityd_pw = StringField('quantityd_pw')

#     dregimen_po_correct = RadioField('Is dregimen_po correct?', choices=[(True, 'Yes'), (False, 'No')], default=None, coerce=lambda x: x == 'True')
#     dregimen_pw_correct = RadioField('Is dregimen_pw correct?', choices=[(True, 'Yes'), (False, 'No')], default=None, coerce=lambda x: x == 'True')
#     laspud_po_correct = RadioField('Is laspud_po correct?', choices=[(True, 'Yes'), (False, 'No')], default=None, coerce=lambda x: x == 'True')
#     laspud_pw_correct = RadioField('Is laspud_pw correct?', choices=[(True, 'Yes'), (False, 'No')], default=None, coerce=lambda x: x == 'True')
#     quantityd_po_correct = RadioField('Is quantityd_po correct?', choices=[(True, 'Yes'), (False, 'No')], default=None, coerce=lambda x: x == 'True')
#     quantityd_pw_correct = RadioField('Is quantityd_pw correct?', choices=[(True, 'Yes'), (False, 'No')], default=None, coerce=lambda x: x == 'True')

#     submit = SubmitField('Submit')

#     def __init__(self, *args, **kwargs):
#         super(ValidationEntryForm, self).__init__(*args, **kwargs)
#         self.facility.choices = [(facility.id, facility.facility_name) for facility in FacilityNameItem.query.order_by(FacilityNameItem.facility_name)]
#         self.client_id.choices = [(client_item.id, client_item.client_id) for client_item in ClientIdItem.query.order_by(ClientIdItem.client_id)]

class FacilityClientForm(FlaskForm):
    facility = SelectField('Facility', validators=[DataRequired()], coerce=int)
    client_id = SelectField('Client ID', validators=[DataRequired()], choices=[])
    submit = SubmitField('Submit')

# class ValidateRecordForm(FlaskForm):
#     facility = QuerySelectField('Facility', query_factory=facility_name_choices, get_label='facility_name', allow_blank=True, blank_text='Select a facility', get_pk=lambda x: x.id)
#     client_id = QuerySelectField('Client ID', query_factory=client_id_choices, get_label='client_id', allow_blank=True, blank_text='Select a client ID', get_pk=lambda x: x.id)

#     dregimen_po_correct = RadioField('dregimen_po_correct', choices=[('yes', 'Yes'), ('no', 'No')], default='none')
#     dregimen_pw_correct = RadioField('dregimen_pw_correct', choices=[('yes', 'Yes'), ('no', 'No')], default='none')
#     laspud_po_correct = RadioField('laspud_po_correct', choices=[('yes', 'Yes'), ('no', 'No')], default='none')
#     laspud_pw_correct = RadioField('laspud_pw_correct', choices=[('yes', 'Yes'), ('no', 'No')], default='none')
#     quantityd_po_correct = RadioField('quantityd_po_correct', choices=[('yes', 'Yes'), ('no', 'No')], default='none')
#     quantityd_pw_correct = RadioField('quantityd_pw_correct', choices=[('yes', 'Yes'), ('no', 'No')], default='none')

#     submit = SubmitField('Validate Client Record')

#     def __init__(self, *args, **kwargs):
#         super(ValidateRecordForm, self).__init__(*args, **kwargs)
#         self.facility.choices = [(facility.id, facility.facility_name) for facility in FacilityNameItem.query.order_by(FacilityNameItem.facility_name)]
#         self.client_id.choices = [(client_item.id, client_item.client_id) for client_item in ClientIdItem.query.order_by(ClientIdItem.client_id)]


# class ClientRecordUpdateForm(FlaskForm):
#     facility = QuerySelectField('Facility', query_factory=facility_name_choices, get_label='facility_name', allow_blank=True, blank_text='Select a facility', get_pk=lambda x: x.id)
#     client_id = QuerySelectField('Client ID', query_factory=client_id_choices, get_label='client_id', allow_blank=True, blank_text='Select a client ID', get_pk=lambda x: x.id)

#     dregimen_po = StringField('dregimen_po', validators=[DataRequired()])
#     mrefill_po = IntegerField('mrefill_po', validators=[DataRequired()])
#     laspud_po = DateField('laspud_po', format='%Y-%m-%d', validators=[DataRequired()])
#     quantityd_po = IntegerField('quantityd_po', validators=[DataRequired()])
#     client_folder = RadioField('client_folder', choices=[('yes', 'Yes'), ('no', 'No'), ('none', 'None')], default='none')
#     submit = SubmitField('Update Client Record')

#     def __init__(self, *args, **kwargs):
#         super(ClientRecordUpdateForm, self).__init__(*args, **kwargs)
#         self.facility.choices = [(facility.id, facility.facility_name) for facility in FacilityNameItem.query.order_by(FacilityNameItem.facility_name)]
#         #self.client_id.choices = [(client_item.id, client_item.client_id) for client_item in ClientIdItem.query.order_by(ClientIdItem.client_id)]



# class PharmacyRecordUpdateForm(FlaskForm):
#     facility = SelectField('Facility Name', validators=[DataRequired()])
#     client_id = SelectField('Client ID', validators=[DataRequired()])

#     dregimen_pw = StringField('dregimen_pw', validators=[DataRequired()])
#     mrefill_pw = IntegerField('mrefill_pw', validators=[DataRequired()])
#     laspud_pw = DateField('laspud_pw', format='%Y-%m-%d', validators=[DataRequired()])
#     quantityd_pw = IntegerField('quantityd_pw', validators=[DataRequired()])
#     pharm_doc = RadioField('pharm_doc', choices=[('yes', 'Yes'), ('no', 'No'), ('none', 'None')], default='none')
#     submit = SubmitField('Update Pharmacy Record')

#     def __init__(self, *args, **kwargs):
#         super(PharmacyRecordUpdateForm, self).__init__(*args, **kwargs)
#         self.facility.choices = [facility.facility_name for facility in FacilityNameItem.query.order_by(FacilityNameItem.facility_name)]
#         self.facility.choices.insert(0, ('', 'Select a facility'))
#         self.client_id.choices = [('', 'Select a client ID')]

#     def update_client_id_choices(self, facility_name):
#         if facility_name != '':
#             self.client_id.choices = [client_item.client_id for client_item in DataEntry.query.filter_by(facility_name=facility_name).order_by(DataEntry.client_id)]
#         else:
#             self.client_id.choices = [('', 'Select a client ID')]


class FacilityForm(FlaskForm):
    facility_name = SelectField('Facility Name', choices=[])
    client_id = SelectField('Client ID', choices=[])

    dregimen_po = StringField('dregimen_po', validators=[DataRequired()])
    mrefill_po = IntegerField('mrefill_po', validators=[DataRequired()])
    laspud_po = DateField('laspud_po', format='%Y-%m-%d', validators=[DataRequired()])
    quantityd_po = IntegerField('quantityd_po', validators=[DataRequired()])
    client_folder = RadioField('client_folder', choices=[('yes', 'Yes'), ('no', 'No')], default='none')
    submit = SubmitField('Update Client Record')


class PhamarcyForm(FlaskForm):
    facility_name = SelectField('Facility Name', choices=[])
    client_id = SelectField('Client ID', choices=[])

    dregimen_pw = StringField('dregimen_po', validators=[DataRequired()])
    mrefill_pw = IntegerField('mrefill_po', validators=[DataRequired()])
    laspud_pw = DateField('laspud_po', format='%Y-%m-%d', validators=[DataRequired()])
    quantityd_pw = IntegerField('quantityd_po', validators=[DataRequired()])
    pharm_doc = RadioField('client_folder', choices=[('yes', 'Yes'), ('no', 'No')], default='none')
    submit = SubmitField('Update Client Record')                                                                                                    