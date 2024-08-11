from calendar import c
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from app import mongo
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required
from app import login_manager, mongo
from app.models import User
from datetime import datetime
import re, uuid
from app.models import User

hospital_bp = Blueprint('hospital', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@hospital_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    global hospital_data
    hospital_data = mongo.db.hospitals.find_one({'umsId': session['umsId']})
    hospital_details = mongo.db.users.find_one({'umsId': session['umsId']})
    hospital_data = {**hospital_data, **hospital_details} if hospital_details else hospital_data
    hospital_data['phoneNumber'] = hospital_data.get('phoneNumber', [None])[0]
    print(hospital_data) #for debugging
    if not hospital_data:
        flash('Hospital not found', 'error')
        return redirect(url_for('auth.login'))
    return render_template('hospital/dashboard.html', hospital_data=hospital_data)

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

@hospital_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    # if current_user.rolesId != 2:
    #     abort(403)
    # hospital = mongo.db.hospitals.find_one({'umsId': current_user.umsId})
    # if hospital:
    #     return render_template('hospital/profile.html', hospital=hospital)
    # else:
    #     abort(404)
    return render_template('hospital/profile.html')

@hospital_bp.route('/search_doctors', methods=['GET'])
@login_required
def search_doctors():
    search_term = request.args.get('term', '')
    doctors = mongo.db.doctors.find({
        'umsId': {'$regex': f'^{re.escape(search_term)}', '$options': 'i'},
        'status': 'active'
    }, {'umsId': 1, 'name': 1, '_id': 0}).limit(10)

    return jsonify(list(doctors))

@hospital_bp.route('/api/assign_doctor', methods=['POST'])
@login_required
def assign_doctor():
    data = request.json
    doctor_id = data.get('doctorId')
    hospital_id = session['umsId']

    if not doctor_id:
        return jsonify({'success': False, 'message': 'Doctor ID is required'}), 400

    # Check if the doctor exists and is active
    doctor = mongo.db.doctors.find_one({'umsId': doctor_id, 'status': 'active'})
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor not found or not active'}), 404

    # Assign the doctor to the hospital
    result = mongo.db.hospitals.update_one(
        {'umsId': hospital_id},
        {'$addToSet': {'assignedDoctors': doctor_id}}
    )

    if result.modified_count > 0:
        return jsonify({'success': True, 'message': 'Doctor assigned successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to assign doctor or doctor already assigned'}), 400