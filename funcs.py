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
