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

doctor_bp = Blueprint('doctor', __name__)

@login_required
@doctor_bp.route('/dashboard', methods=['GET', 'POST'])
def index():
    return render_template('doctor/dashboard.html')

@doctor_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    return ("testing") #for debugging

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def generate_doctor_id():
    return 'UMSD' + re.sub('-', '', str(uuid.uuid4()))[:8].upper()


@doctor_bp.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('doctor.register'))
        
        print(request.form)  # For debugging
        name = request.form['name']
        password = generate_password_hash(request.form['password']),
        phone_number = request.form['phonenumber'],
        state = request.form['state']
        user_type = 'doctor'
        print(name, email, password, user_type)  # For debugging
        umsId = generate_doctor_id()
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
            'rolesId': 3
        })

        # Insert into doctors collection
        mongo.db.doctors.insert_one({
            'umsId': umsId,
            'specialization': None,
            'createdAt': created_at,
            'updatedAt': updated_at
        })
        #insert into login collection
        mongo.db.login.insert_one({
            'umsId': umsId,
            'email': email,
            'passwordHash': password,
            'rolesId': 3,
            'status': 'awaiting_approval',
        })

        flash('Doctor registered successfully!')
        return redirect(url_for('doctor.index'))
    return render_template('doctor/register.html')
