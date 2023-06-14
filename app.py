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


from flask import Flask, render_template, url_for, redirect, request, jsonify, send_file
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
from flask_migrate import Migrate
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
import zipfile
from sqlalchemy import create_engine, text


#
from app_setup import socketio, login_manager, db, app, photos, limiter, migrate
from funcs import create_db, send_email, get_error_image, pst_convert
from models import User, Thread, Comment, Tag, UpdateLog
from forms import RegisterForm, LoginForm, VerifyForm, ThreadForm, UploadForm, CommentForm, UpdateForm, AdminForm

#test
# app = Flask(__name__)
# app.register_blueprint(views, url_prefix='/')
# app.secret_key = "%23144141*(043248fsnsf)"
# socketio = SocketIO(app)

# app.jinja_env.add_extension('jinja2.ext.loopcontrols')

# login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# Do 
# {{current_user.<user-property>}}
# to get data for the current user.



# engine = create_engine('sqlite:///instance/users.db')

# with engine.connect() as conn:
#     query = 'alter table User add column activated Boolean'
#     query = 'alter table User add column password_reset_code Integer'
#     result = conn.execute(text(query))



@login_manager.unauthorized_handler
def handle_needs_login():
    return redirect(url_for('login'))

@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/")
def index():
    return redirect(url_for('threadpage', page=1))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    loginError = False
    verifyError = False
    activateError = False
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            print(user.password)

            hash_html = bcrypt.hashpw((form.password.data).encode('utf8'), bcrypt.gensalt())
            if user.password == form.password.data:
                if user.activated == False:
                    return redirect(url_for('account_deactive'))
                elif user.verified:
                    login_user(user)
                    print('holy shit it worked')
                    return redirect(url_for('threadpage', page=1))
                else:
                    verifyError = True
            else:
                loginError = True

    # for user in User.query.all():
    #     user.activated = True
    #     user.password_reset_code = random.randint(1,100000)
    #     db.session.commit()

    return render_template('login.html', form=form, login_state=loginError, verify_state=verifyError)

@app.route('/account-deactivated')
def account_deactive():
    return "Seems your account was deactivated. This may be due to it being a duplicate, or having characters that interfere with the 'aesthetic' of the website. \nIf you believe this is an error, contact the owner to reinstate your account."





@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():

        ids = [user.id for user in User.query.all()]
        id = random.randint(1,1000000)

        while id in ids:
            id = random.randint(1,1000000)

        verify_code = random.randint(1,100000)

        send_email(form.email.data, 'QForums Verification Code', f'Your verification code for QForums is {verify_code}')

        new_user = User(id=id, username=form.username.data, password=form.password.data, verification_code=verify_code, email=form.email.data, create_date=pst_convert(datetime.datetime.utcnow()))
        db.session.add(new_user)
        db.session.commit()


        
        return redirect(url_for('verifylimbo', id=id))

    return render_template('register.html', form=form)


@app.route('/verification-limbo/u/<int:id>/v/', methods=['GET', 'POST'])
def verifylimbo(id):
    form = VerifyForm()
    login_form = LoginForm()
    error = 0

    user = User.query.filter_by(id=id).first()

    db.session.commit()
    code = user.verification_code

    if form.validate_on_submit():
        user = User.query.filter_by(id=id).first()

        if user.verified == False:
            if int(form.code.data) == user.verification_code:
                user.verified = True
                db.session.commit()
                return redirect(url_for('login'))
            else:
                error = 1
        
        else:
            return redirect(url_for('login'))
        
    return render_template('verification_limbo.html', form=form, error=error, code=code)



        

def remove_duplicates(list):
    final_list = []
    for i in range(len(list)):
        if list[i] in final_list:
            continue
        else:
            final_list.append(list[i])

    return final_list




@app.route('/create-thread/p/<int:page>', methods=['GET', 'POST'])
@login_required
def createthread(page):
    form = ThreadForm()
    upload_form = UploadForm()

    user = current_user

    if user.activated == False:
        return redirect(url_for('user_logout'))
    elif user.verified:

        if request.method == "GET":
            all_tags = Tag.query.order_by(Tag.times_used.desc()).all()

            all_tags = [tag.name for tag in all_tags]

            print(all_tags)

        if form.validate_on_submit():
            ids = [thread.id for thread in Thread.query.all()]
            id = random.randint(1,1000000)

            while id in ids:
                id = random.randint(1,1000000)

            print(request.files)

            if request.files['image']:

                print(request.files)

                file = request.files['image']

                if '.png' not in file.filename and '.jpg' not in file.filename:
                    print(file.filename)
                    image_name = None
                else:
                    image_name = ""

                    for i in range(9):
                        num = random.randint(1,10)
                        image_name += str(num)

                    all_images = [thread.image for thread in Thread.query.all()]
                    
                    while image_name in all_images:
                        num = random.randint(1,1000000)
                        image_name += str(num)

                    image_name = 'static/thread-images/'+image_name+'.png'


                    file.save(image_name)

            else:
                image_name = None


            print(image_name)



            all_tags = [tag.name for tag in Tag.query.all()]
            # tags = request.form.get('tag-search')
            print(request.form)
            tags = form.tags.data
            tags = tags.replace(" ", "")
            tags = tags.split(',')

            tags = remove_duplicates(tags)
            print('tags no dupes: '+str(tags))



            for i in range(len(tags)):
                if tags[i] in all_tags:
                    tag = Tag.query.filter_by(name=tags[i]).first()
                    tag.times_used = tag.times_used + 1
                    db.session.add(tag)
                    db.session.commit()                    
                    continue
                else:
                    tag_ids = [tag.id for tag in Tag.query.all()]
                    tag_id = random.randint(1,1000000)

                    while tag_id in tag_ids:
                        tag_id = random.randint(1,1000000)

                    new_tag = Tag(id=tag_id, name=tags[i], times_used=1)
                    db.session.add(new_tag)
                    db.session.commit()

                print('tags: '+str(tags[i]))

            tags = str(tags)
            tags = tags[1:-1]
            print('tags2 no dupes: '+str(tags))
            tags.replace("'",'')
            

            new_post = Thread(id=id, title=form.title.data, content=form.content.data, author=current_user.username, date=pst_convert(datetime.datetime.utcnow()), tags = tags, image=image_name)
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('threadpage', page=1))
        
        else:
            print(form.errors)
        
        return render_template('create_thread.html', form=form, page=page, all_tags=all_tags, upload_form=upload_form)
    
    elif user.verified == False:
        return redirect(url_for('verifylimbo', id=user.id))
    



@app.route('/thread-page/p/<int:page>/', methods=['GET', 'POST'])
@login_required
def threadpage(page):

    user = current_user

    if user.activated == False:
        return redirect(url_for('user_logout'))
    
    elif user.verified:

        threads_per_page = 5
        search = None

        all_tags = Tag.query.order_by(Tag.times_used.desc()).all()

        all_tags = [tag.name for tag in all_tags]
        


        
        all_threads = Thread.query.order_by(Thread.date.desc()).paginate(page=page, per_page=threads_per_page, error_out=False)
        all_comments = Comment.query.order_by(Comment.date.desc()).all()
        all_updates = UpdateLog.query.order_by(UpdateLog.date.desc()).all()
        comment_form = CommentForm()

        # print_images = [print(thread.image+' - ') for thread in all_threads]

        num_pages = all_threads.pages

        

        def print_in_console(message):
            print(str(message))



        if request.method == "GET":
            all_tags = Tag.query.order_by(Tag.times_used.desc()).all()

            all_tags = [tag.name for tag in all_tags]



        try:
            if request.args['test']:
                search = request.args['test']
        except KeyError:
            pass



        if request.method == 'POST':
            tags_search = request.form.get('tag-search')
            print(tags_search)
            tags_search = tags_search.replace(" ", "")
            tags_search = tags_search.split(',')

            tags_search = remove_duplicates(tags_search)

            all_threads = Thread.query.order_by(Thread.date.desc())

            for tag in tags_search:
                all_threads = all_threads.filter(Thread.tags.like(f"%{tag}%"))
            
            all_threads = all_threads.filter(and_(*(Thread.tags.like(f"%{tag}%") for tag in tags_search)))

            all_threads = all_threads.paginate(page=page, per_page=threads_per_page, error_out=False)

            page = 1 

            search = tags_search

            return redirect(url_for('threadpage', page=page, num_pages=num_pages, search_args = search))

        if request.args.get('search_args'):
            print('search is real')
            tags_search = request.args.get('search_args')
            all_threads = Thread.query.order_by(Thread.date.desc())

            for tag in tags_search:
                all_threads = all_threads.filter(Thread.tags.like(f"%{tag}%"))
            
            all_threads = all_threads.filter(and_(*(Thread.tags.like(f"%{tag}%") for tag in tags_search)))

            all_threads = all_threads.paginate(page=page, per_page=threads_per_page, error_out=False)
        else:
            search = None
        

        return render_template('thread_page.html', all_threads=all_threads.items, comment_form=comment_form, all_comments = all_comments, mprint = print_in_console, all_updates=all_updates, page=page, num_pages=num_pages, all_tags=all_tags, search = search)
    elif user.verified == False:
        return redirect(url_for('verifylimbo', id=user.id))

    


def find_page(threads, val):
    # Split list into sublists of 10 each
    sublists = [threads[i:i+10] for i in range(0, len(threads), 10)]
    
    # Find which sublist the value is in
    sublist_idx = -1
    for i, sublist in enumerate(sublists):
        if val in sublist:
            sublist_idx = i
            break
    
    return sublist_idx


@app.route('/add-comment/', methods=['POST', 'GET'])
def add_comment():
    # Get the comment data from the form

    url = str(request.url)

    print(url)

    parsed_url = urlparse(url)

    params = parse_qs(parsed_url.query)

    page = params.get('page_num', [''])[0] 

    content = request.form['content']
    author = current_user.username
    thread_id = request.form['thread_id']
    threads = list(Thread.query.with_entities(Thread.id))
    print(threads)

    if len(content) > 1000:
        doNothing = 1
    else:
        ids = [comment.id for comment in Comment.query.all()]
        id = random.randint(1,1000000)

        while id in ids:
            id = random.randint(1,1000000)

        # Create a new Comment object
        new_comment = Comment(id=id, content=content, author=author, date=pst_convert(datetime.datetime.utcnow()), thread_id=thread_id)
        # new_post = Thread(id=random.randint(1,1000000), title=form.title.data, content=form.content.data, author=current_user.username)
        # Add the new comment to the database
        db.session.add(new_comment)
        db.session.commit()
        

        # id = db.Column(db.Integer, primary_key=True)
        # content = db.Column(db.Text, nullable=False)
        # author = db.Column(db.String(20), nullable=False)
        # date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
        
        # thread_id = db.Column(db.Integer, db.ForeignKey(Thread.id))
        # thread = db.relationship('Thread', backref='comments')

        # Redirect the user back to the thread page
    return redirect(url_for('threadpage', page=page))


@app.route('/delete-post/t/<int:thread_id>', methods=['POST', 'GET'])
def delete_post(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    db.session.delete(thread)
    db.session.commit()

    return redirect(url_for('threadpage', page=1))


@app.route('/logout-user/', methods=['POST', 'GET'])
def user_logout():
    logout_user()
    return redirect(url_for('login'))





@app.route('/thread-page/t/<int:thread_id>')
def view_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    page = 1
    all_updates = UpdateLog.query.order_by(UpdateLog.date.desc()).all()
    all_comments = Comment.query.order_by(Comment.date.desc()).all()
    comment_form = CommentForm()
    if thread.tags != None:
        tags = str(thread.tags)
    else:
        tags = ''

    admin_status = current_user.admin
    user_id = (User.query.filter_by(username=thread.author).first()).id
    user_email = (User.query.filter_by(username=thread.author).first()).email

    if (current_user.username == 'lemonade'):
        admin_status = True

    return render_template('thread_main.html', thread=thread, all_updates = all_updates, page=page, comment_form=comment_form, all_comments=all_comments, tags=tags, admin=admin_status, user_id=user_id, email=user_email)



@app.route('/admin-panel', methods=['GET', 'POST'])
@login_required
def adminpanel():
    update_form = UpdateForm()
    admin_form = AdminForm()
    all_updates = UpdateLog.query.order_by(UpdateLog.date.desc()).all()




    username = current_user.username
    admin = current_user.admin
    if username == 'lemonade' or admin:

        if update_form.validate_on_submit():
            new_log = UpdateLog(content = update_form.content.data, date=pst_convert(datetime.datetime.utcnow()))
            db.session.add(new_log)
            db.session.commit()

        if admin_form.is_submitted():
            if admin_form.admin_id.data != '':
                new_admin = User.query.filter_by(id=int(admin_form.admin_id.data)).first()
                new_admin.admin = True
                db.session.commit()
            if admin_form.deactivate_id.data != '':
                account = User.query.filter_by(id=int(admin_form.deactivate_id.data)).first()
                print('deactivate account ',str(account.username))
                account.activated = False
                db.session.commit() 

            print(admin_form.deactivate_id.data)

        

        return render_template('admin_panel.html', update_form=update_form, all_updates=all_updates, admin_form = admin_form)
    else:
        return redirect(url_for('threadpage', page=1))
    

@app.route('/update-log/', methods=['GET', 'POST'])
@login_required
def update_log():
    all_updates = UpdateLog.query.order_by(UpdateLog.date.desc()).all()

    update_dates = [ update.date for update in all_updates]
    updates = [ update.content for update in all_updates]

    return render_template('update_page.html', update_dates = update_dates, updates=updates)


@app.errorhandler(429)
def rate_limit_exceeded(e):
    image_dir = get_error_image()
    return render_template('error.html', image=image_dir, error='429'), 429

@app.errorhandler(404)
def rate_limit_exceeded(e):
    image_dir = get_error_image()
    return render_template('error.html', image=image_dir, error='404'), 404

@socketio.on('message')
def handle_message(data):
    message = data['message']
    username = data['username']
    socketio.emit('update', data)





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=80, debug=True)
    socketio.run(app, debug=True) 
    
