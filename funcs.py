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

from email.mime.text import MIMEText
import smtplib, ssl
import random
import pytz
from app_setup import app, db
import os



def create_db():
    with app.app_context():
        db.create_all()
    print('Created Database!')

def send_email(receiver, subject, contents):
    sender_email = 'example@gmail.com'
    recipient_email = receiver
    message = contents

    username = 'example@gmail.com'
    password = 'password'

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(sender_email, recipient_email, msg.as_string())

    print("sent email!")
#
def get_error_image():
    image_directory = 'static/error-images'
    image_files = [os.path.join(image_directory, f) for f in os.listdir(image_directory) if os.path.isfile(os.path.join(image_directory, f))]

    image_dir = random.choice(image_files)
    print(image_dir)
    image_dir = str(image_dir)
    image_dir = f"\{image_dir}"

    return image_dir

def pst_convert(utc):
    timezone = pytz.timezone('US/Pacific')
    pst = utc.replace(tzinfo=pytz.utc).astimezone(timezone)

    return pst
