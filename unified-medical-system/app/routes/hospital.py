from flask import Blueprint, render_template, request, flash, redirect, url_for
from app import mongo
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required
from datetime import datetime
import re, uuid


hospital_bp = Blueprint('hospital', __name__)

@hospital_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return "Hospital Dashboard"

def generate_hospital_id():
    return 'UMSH' + re.sub('-', '', str(uuid.uuid4()))[:8].upper()

@hospital_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Extract form data
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        confirm_password = request.form['confirm_password']
        state = request.form['state']
        phone_number = request.form['phonenumber']
        address = request.form['address']
        license_number = request.form['license']

        # Validate form data
        if request.form['password'] != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('hospital.register'))

        existing_hospital = mongo.db.users.find_one({'email': email})
        if existing_hospital:
            flash('Email already exists', 'error')
            return redirect(url_for('hospital.register'))

        # Validate license number format
        license_pattern = re.compile(r'^[A-Z]{2}-\d{2}-\d{4}-\d{7}$')
        if not license_pattern.match(license_number):
            flash('Invalid license number format', 'error')
            return redirect(url_for('hospital.register'))

        # Create new hospital
        umsId = generate_hospital_id()
        created_at = updated_at = datetime.now()

        new_hospital = {
            'umsId': umsId,
            'name': name,
            'email': email,
            'phoneNumber': phone_number,
            'state': state,
            'address': address,
            'licenseNumber': license_number,
            'status': 'awaiting_approval',
            'createdAt': created_at,
            'updatedAt': updated_at,
            'passwordHash': [password],  # Store as a list
            'rolesId': 2  # 2 is the role ID for hospitals
        }
        mongo.db.users.insert_one(new_hospital)

        # Insert into hospitals collection
        mongo.db.hospitals.insert_one({
            'umsId': umsId,
            'licenseNumber': license_number,
            'createdAt': created_at,
            'updatedAt': updated_at
        })

        # Insert into login collection
        mongo.db.login.insert_one({
            'umsId': umsId,
            'email': email,
            'passwordHash': [password],  # Store as a list
            'rolesId': 2,
            'status': 'awaiting_approval',
        })

        flash('Registration successful. Please wait for approval.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('hospital/register.html')
