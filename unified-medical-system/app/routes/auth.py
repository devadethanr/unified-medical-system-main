from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app import mongo, login_manager
from app.models import User
from bson.objectid import ObjectId

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
    return redirect(url_for('auth.login'))
