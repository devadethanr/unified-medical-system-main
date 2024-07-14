from calendar import c
from venv import create
from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app import mongo, login_manager
from app.models import User
from bson.objectid import ObjectId
from datetime import datetime
import re, uuid

from app.routes.auth import login
patient_bp = Blueprint('patient', __name__)

@login_required
@patient_bp.route('/dashboard', methods=['GET', 'POST'])
def index():
    return render_template('patient/dashboard.html')

@patient_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    return ("testing") #for debugging

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def generate_patient_id():
    return 'UMSP' + re.sub('-', '', str(uuid.uuid4()))[:8].upper()


@patient_bp.route('/register', methods=['GET', 'POST'])
def register():    

    if request.method == 'POST':
        # Check if email already exists in the database
        email = request.form['email']
        password = request.form['password']
        if password != request.form['confirm_password']:
            print('Passwords do not match. Please try again.') # For debugging
        existing_user = mongo.db.users.find_one({'email': email})
        
        if existing_user:
            flash(' already exists! Please login. ', 'error')  # For debugging
            return redirect(url_for('patient.register'))
        
        print(request.form)  # For debugging
        name = request.form['name']
        password = generate_password_hash(request.form['password']),
        phone_number = request.form['phonenumber'],
        state = request.form['state']
        user_type = 'patient'
        print(name, email, password, user_type)  # For debugging
        umsId = generate_patient_id()
        print(umsId) # For debugging
        created_at = updated_at = datetime.now()
        
        mongo.db.users.insert_one({
            'umsId': umsId,
            'name': name,
            'email': email,
            'phoneNumber': phone_number,
            'state': state,
            'status': 'active',
            'createdAt': created_at,
            'updatedAt': updated_at,
            'passwordHash': password,
            'rolesId': 4
        })

        # Insert into patients collection
        mongo.db.patients.insert_one({
            'umsId': umsId,
            'dateOfBirth': None,
            'gender': None,
            'createdAt': created_at,
            'updatedAt': updated_at
        })
        #insert into login collection
        mongo.db.login.insert_one({
            'umsId': umsId,
            'email': email,
            'passwordHash': password,
            'rolesId': 4,
            'status': 'active',
        })

        flash('User registered successfully!')
        return redirect(url_for('patient.index'))
    return render_template('patient/register.html')