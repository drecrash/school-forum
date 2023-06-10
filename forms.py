from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_socketio import SocketIO
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
import flask_wtf
from flask_wtf import FlaskForm
import wtforms
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, TextAreaField
from wtforms.validators import InputRequired, Length, ValidationError, Optional
from flask_wtf.file import FileAllowed, FileField
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_bcrypt import bcrypt
import datetime
import random
import paginate
import smtplib, ssl
import json
import os
from urllib.parse import urlparse, parse_qs
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pytz
from app_setup import app, db, photos
from funcs import pst_convert
from models import User

#
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    email = StringField(validators=[InputRequired(), Length(min=4, max=80)], render_kw={"placeholder": "Email"})

    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username = username.data).first()
        

        if existing_user_username:
            raise ValidationError(
                "Username already in use"
            )
        
    def validate_email(self, email):
        existing_email = User.query.filter_by(email = email.data).first()

        if existing_email:
            raise ValidationError(
                "Email already in use. Please check your inbox and spam folder."
            )              
        elif ('@' not in email.data or '.' not in email.data):
            raise ValidationError(
                "Invalid email"
            )                   

        # elif ('@*******.academy' not in email.data):
        #     raise ValidationError(
        #         "Invalid email. Please use your school provided email address."
        #     )     

        elif ('+' in email.data):
            raise ValidationError(
                "Please use an email that does not have '+' in it"
            )                           
        

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Login")

class VerifyForm(FlaskForm):
    code = StringField(validators=[InputRequired()], render_kw={"placeholder": "Code"})

    submit = SubmitField("Submit Code")




class ThreadForm(FlaskForm):
    title = StringField(validators=[InputRequired(), Length(min=4, max=100)], render_kw={"placeholder": "Title"})
    content = TextAreaField(validators=[InputRequired(), Length(min=4, max=2000)], render_kw={"placeholder": "Content", "style": "height: 100px;", "class": "form-control"})
    tags = StringField(validators=[InputRequired(), Length(min=4, max=200)], render_kw={"placeholder": "Tags [seperate with commas and use underscores instead of spaces]", "id":"tag-search"})

    submit = SubmitField("Post")


class UploadForm(FlaskForm):
    image = FileField(validators=[FileAllowed(photos, 'Only images are allowed')])

    submit = SubmitField('Upload')


class CommentForm(FlaskForm):
    content = StringField(validators=[InputRequired(), Length(min=4, max=1000)], render_kw={"placeholder": "Comment"})

    def validate_content(self, content):

        if len(content) > 1000:
            raise ValidationError(
                "1000 character limit"
            )    

    submit = SubmitField("Comment")




class UpdateForm(FlaskForm):
    content = StringField(validators=[InputRequired(), Length(min=4, max=2000)], render_kw={"placeholder": "Update"})

    submit = SubmitField("Create Log")



class AdminForm(FlaskForm):
    admin_id = StringField(validators=[Length(min=4, max=2000)], render_kw={"placeholder": "Admin User ID"})
    deactivate_id = StringField(validators=[Length(min=1, max=2000)], render_kw={"placeholder": "Deactivate Account ID"})

    submit = SubmitField("Make Admin")