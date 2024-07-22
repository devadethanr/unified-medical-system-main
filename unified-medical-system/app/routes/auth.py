import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app import mongo, login_manager, oauth, mail
from app.models import User
from bson.objectid import ObjectId
from flask_mail import Message
from app.utils import generate_patient_id
from datetime import datetime
import random

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        user = User.find_by_identifier(identifier)
        if user:
            if user.passwordHash is None:
                flash('User password is missing')
                return redirect(url_for('auth.login'))
            
            #role selection
            if check_password_hash(user.passwordHash, password):
                session['umsId'] = user.umsId
                if user.rolesId == 4:
                    login_user(user)
                    return redirect(url_for('patient.index'), code=302)
                elif user.rolesId == 3:
                    login_user(user)
                    if user.status == 'awaiting_approval':
                        flash('Your account is waiting for admin approval')
                        return render_template('common/awaiting_response.html')
                    elif user.status == 'active':
                        return redirect(url_for('doctor.index'), code=302)
                elif user.rolesId == 2:
                    login_user(user)
                    return redirect(url_for('hospital.index'), code=302)
                elif user.rolesId == 1:
                    login_user(user)
                    return redirect(url_for('admin.index'), code=302)
            else:
                flash('Invalid identifier or password')
        else:
            flash('User not found, please create an account')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/google_login')
def google_login():
    redirect_uri = url_for('auth.google_authorized', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/google_authorized')
def google_authorized():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token)
    
    session["google_id"] = user_info['sub']
    session["name"] = user_info['name']
    session["email"] = user_info['email']

    user = mongo.db.users.find_one({'email': session['email']})
    if not user:
        name = session["name"]
        email = session["email"]
        umsId = generate_patient_id()
        created_at = updated_at = datetime.now()

        mongo.db.users.insert_one({
            'umsId': umsId,
            'name': name,
            'email': email,
            'phoneNumber': None,
            'state': None,
            'status': 'active',
            'createdAt': created_at,
            'updatedAt': updated_at,
            'passwordHash': None,
            'rolesId': 4
        })

        mongo.db.patients.insert_one({
            'umsId': umsId,
            'dateOfBirth': None,
            'gender': None,
            'createdAt': created_at,
            'updatedAt': updated_at
        })

        mongo.db.login.insert_one({
            'umsId': umsId,
            'email': email,
            'passwordHash': None,
            'rolesId': 4,
            'status': 'active',
        })

    return redirect(url_for('patient.index'))

#routes for password reset
#forget password page
@auth_bp.route("/forgot_password")
def password():
    return render_template('auth/forgot_password.html')

#for otp generation and sending mail
@auth_bp.route("/email_verify", methods=['GET','POST'])
def email_verification():
    if request.method == 'POST':
        email = request.form['email']
        #wants to implement umsId verification also
        user = mongo.db.users.find_one({'email': email})
        if user:
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            session['otp_code'] = otp_code
            session['email'] = email
            msg = Message('Password Reset', recipients=[email])
            msg = Message('Forgot Password', sender='devadethanr@mca.ajce.in', recipients=[email])
            msg.html = render_template('auth/otp_design.html', name=user['name'], otp_code=otp_code)
            try:
                mail.send(msg)
                flash('OTP successfully mailed', 'success')
                return redirect(url_for('auth.otp_verify'))
            except Exception as e:
                print(f"Error sending email: {e}")  
                flash('Email not sent: ' + str(e), 'danger')
        else:
            flash('Email not found', 'danger')
    return render_template('auth/forgot_password.html')

#for otp verification
@auth_bp.route("/otp_verify", methods=['GET','POST'])
def otp_verify():
    if request.method == 'POST':
        print('OTP verification started') #for debugging
        otp = request.form['otp']
        print('OTP entered:', otp) #for debugging
        print(otp, session.get('otp_code')) #for debugging
        if otp == session.get('otp_code'):
            print ('OTP verified successfully') #for debugging
            flash('OTP verified successfully', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('Invalid OTP', 'danger')
    return render_template('auth/otp_verify.html')

#reset password page
@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        password = request.form['password']
        email = session.get('email')

        if not email:
            flash('No email in session', 'danger')
            return redirect(url_for('auth/forgot_password'))
        # Hash the new password
        hashed_password = generate_password_hash(password)

        mongo.db.users.update_one({'email': email}, {'$set': {'passwordHash': [hashed_password]}})
        mongo.db.login.update_one({'email': email}, {'$set': {'passwordHash': [hashed_password]}})

        flash('Your password has been reset successfully', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html')