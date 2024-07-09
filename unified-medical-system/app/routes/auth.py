from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app import mongo, login_manager, oauth
from app.models import User
from bson.objectid import ObjectId
from app.utils import generate_patient_id
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username, password)  # For debugging
        user = User.find_by_email(username)
        print(user, password)  # For debugging
        if user and check_password_hash(user.password, password) and user.user_type == 'patient':
            login_user(user)
            return redirect(url_for('patient.index'), code=302)
        else:
            flash('Invalid username or password')
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
