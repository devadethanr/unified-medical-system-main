from calendar import c
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from app import mongo
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required
from app import login_manager, mongo
from app.models import User
from datetime import datetime
import re, uuid, json
from app.models import User
from bson import json_util

hospital_bp = Blueprint('hospital', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def get_hospital_global_data():
    hospital_id = session['umsId']
    hospital_details = mongo.db.hospitalDetails.find_one({'umsId': hospital_id})
    assigned_doctors_count = len(hospital_details.get('assignedDoctors', [])) if hospital_details else 0
    # Get pending appointments count (dummy for now, replace with actual logic later)
    pending_appointments_count = 5  # Dummy value
    return {
        'new_patients': 25,  # Dummy value
        'total_appointments': 150,  # Dummy value
        'available_doctors': assigned_doctors_count,
        'pending_approvals': pending_appointments_count
    }

def get_hospital_data():
    hospital_data = mongo.db.hospitals.find_one({'umsId': session['umsId']})
    hospital_details = mongo.db.users.find_one({'umsId': session['umsId']})
    hospital_data = {**hospital_data, **hospital_details} if hospital_details else hospital_data
    hospital_data['phoneNumber'] = hospital_data.get('phoneNumber', [None])[0]
    return hospital_data

@hospital_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    global_data = get_hospital_global_data()
    hospital_data = get_hospital_data()
    if not hospital_data:
        flash('Hospital not found', 'error')
        return redirect(url_for('auth.login'))
    return render_template('hospital/dashboard.html', hospital_data=hospital_data, global_data=global_data)


def generate_hospital_id():
    return 'UMSH' + re.sub('-', '', str(uuid.uuid4()))[:8].upper()

@hospital_bp.route('/register', methods=['GET',  'POST'])
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
    hospital_data = get_hospital_data()
    return render_template('hospital/profile.html', hospital_data=hospital_data)


@hospital_bp.route('/search_doctors', methods=['GET'])
@login_required
def search_doctors():
    search_term = request.args.get('term', '')
    if search_term:
        doctors = mongo.db.users.find({
            'umsId': {'$regex': f'^{re.escape(search_term)}', '$options': 'i'},
            'status': 'active',
            'rolesId': 3
        }, {
            'umsId': 1,
            'name': 1
        }).limit(5)
        doctors_list = list(doctors)
        return json.loads(json_util.dumps(doctors_list))
    else:
        return jsonify({'error': 'No search term provided'}), 400
    
@hospital_bp.route('/assign_doctor', methods=['POST'])
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

    try:
        # Update or insert into the hospital_details collection
        hospital_details_result = mongo.db.hospitalDetails.update_one(
            {'umsId': hospital_id},
            {'$addToSet': {'assignedDoctors': doctor_id}},
            upsert=True
        )

        # Update the doctorDetails collection
        doctor_details_result = mongo.db.doctorDetails.update_one(
            {'umsId': doctor_id},
            {'$addToSet': {'assignedHospitals': hospital_id}},
            upsert=True
        )

        if (hospital_details_result.modified_count > 0 or 
            hospital_details_result.upserted_id or
            doctor_details_result.modified_count > 0 or
            doctor_details_result.upserted_id):
            return jsonify({'success': True, 'message': 'Doctor assigned successfully'})
        else:
            return jsonify({'success': False, 'message': 'Doctor already assigned or hospital not found'}), 400

    except Exception as e:
        print(f"Error assigning doctor: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while assigning the doctor'}), 500

@hospital_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    hospital_id = session['umsId']
    update_data = {
        'name': request.form['name'],
        'email': request.form['email'],
        'phoneNumber': request.form['phoneNumber'],
        'state': request.form['state'],
        'address': request.form['address'],
        'licenseNumber': request.form['licenseNumber'],
        'updatedAt': datetime.now()
    }
    
    mongo.db.users.update_one({'umsId': hospital_id}, {'$set': update_data})
    mongo.db.hospitals.update_one({'umsId': hospital_id}, {'$set': {
        'licenseNumber': update_data['licenseNumber'],
        'updatedAt': update_data['updatedAt']
    }})
    flash('Profile updated successfully', 'success')
    return redirect(url_for('hospital.profile'))

@hospital_bp.route('/doctors', methods=['GET'])
@login_required
def doctors():
    hospital_id = session['umsId']
    hospital_details = mongo.db.hospitalDetails.find_one({'umsId': hospital_id})
    assigned_doctors = hospital_details.get('assignedDoctors', []) if hospital_details else []

    doctors_details = list(mongo.db.users.find({
        'umsId': {'$in': assigned_doctors},
        'rolesId': 3  # Assuming 3 is the role ID for doctors
    }, {
        'umsId': 1,
        'name': 1,
        'email': 1,
        'phoneNumber': 1,
        'specialization': 1
    }))
    return render_template('hospital/doctors.html', doctors=doctors_details)

@hospital_bp.route('/relieve_doctor', methods=['POST'])
@login_required
def relieve_doctor():
    data = request.json
    doctor_id = data.get('doctorId')
    hospital_id = session['umsId']
    if not doctor_id:
        return jsonify({'success': False, 'message': 'Doctor ID is required'}), 400
    try:
        # Remove doctor from hospital's assigned doctors
        mongo.db.hospitalDetails.update_one(
            {'umsId': hospital_id},
            {'$pull': {'assignedDoctors': doctor_id}}
        )
        # Remove hospital from doctor's assigned hospitals
        mongo.db.doctorDetails.update_one(
            {'umsId': doctor_id},
            {'$pull': {'assignedHospitals': hospital_id}}
        )
        return jsonify({'success': True, 'message': 'Doctor relieved successfully'})
    except Exception as e:
        print(f"Error relieving doctor: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while relieving the doctor'}), 500