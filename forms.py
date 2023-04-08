from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

#from app import User

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

# class RegistrationForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
#     submit = SubmitField('Sign Up')

#     def validate_username(self, username):
#         user = User.query.filter_by(username=username.data).first()
#         if user:
#             raise ValidationError('That username is taken. Please choose a different one.')

#     def validate_email(self, email):
#         user = User.query.filter_by(email=email.data).first()
#         if user:
#             raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
