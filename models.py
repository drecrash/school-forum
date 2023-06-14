"""
MIT License

Copyright (c) 2023 Andre Prakash

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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
from app_setup import app, db
from funcs import pst_convert

class User(db.Model, UserMixin):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    create_date = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    admin = db.Column(db.Boolean, nullable=False, default=False)
    verification_code = db.Column(db.Integer, nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    email = db.Column(db.String(80), nullable=False)

    password_reset_code = db.Column(db.Integer, nullable=False, default=0)
    activated = db.Column(db.Boolean, nullable=False, default=True)

class Thread(db.Model):
    __bind_key__ = 'threads'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=True)
    author = db.Column(db.String(20), nullable=True)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    tags = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(100))
    


class Comment(db.Model):
    __bind_key__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    
    thread_id = db.Column(db.Integer, db.ForeignKey(Thread.id))
    thread = db.relationship('Thread', backref='comments')




class Tag(db.Model):
    __bind_key__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    times_used = db.Column(db.Integer, default=0)


class UpdateLog(db.Model):
    __bind_key__ = 'update_log'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow().date())


