from calendar import c
from venv import create
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app import mongo, login_manager
from app.models import User
from bson.objectid import ObjectId
from datetime import datetime
import re, uuid
from app.routes.auth import login

doctor_bp = Blueprint('doctor', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def generate_doctor_id():
    return 'UMSD' + re.sub('-', '', str(uuid.uuid4()))[:8].upper()

def get_hospital_details(hospital_id):
    """Fetch hospital details from hospitals and users collections."""
    hospital_data = mongo.db.hospitals.find_one({'umsId': hospital_id})
    hospital_user_data = mongo.db.users.find_one({'umsId': hospital_id})
    if hospital_data and hospital_user_data:
        return {**hospital_data, **hospital_user_data}
    return None

def get_assigned_hospitals(doctor_details):
    """Get details of all assigned hospitals for a doctor."""
    assigned_hospitals = []
    if doctor_details and 'assignedHospitals' in doctor_details:
        for hospital_id in doctor_details['assignedHospitals']:
            hospital_info = get_hospital_details(hospital_id)
            if hospital_info:
                assigned_hospitals.append(hospital_info)
    return assigned_hospitals

@login_required
@doctor_bp.route('/dashboard', methods=['GET', 'POST'])
def index():
    global doctor_data
    doctor_data = mongo.db.users.find_one({'umsId': session['umsId']})
    doctor_details = mongo.db.doctorDetails.find_one({'umsId': session['umsId']})
    doctor_data = {**doctor_data, **doctor_details} if doctor_details else doctor_data
    doctor_data['phoneNumber'] = doctor_data.get('phoneNumber', [None])[0]
    
    # Add assigned hospitals information
    doctor_data['assigned_hospitals'] = get_assigned_hospitals(doctor_details)
    doctor_data['assignedHospitals'] = doctor_details.get('assignedHospitals', []) if doctor_details else []
    
    print(doctor_data) #for debugging
    return render_template('doctor/dashboard.html', doctor_data=doctor_data)


@doctor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle doctor profile view and updates."""
    global doctor_data
    doctor_data = mongo.db.users.find_one({'umsId': session['umsId']})
    doctor_details = mongo.db.doctorDetails.find_one({'umsId': session['umsId']})
    
    doctor_data = {**doctor_data, **doctor_details} if doctor_details else doctor_data
    doctor_data['phoneNumber'] = doctor_data.get('phoneNumber', [None])[0]
    doctor_data['assigned_hospitals'] = get_assigned_hospitals(doctor_details)

    if 'specialization' not in doctor_data:
        return render_template('doctor/update_profile.html', doctor_data=doctor_data)
    return render_template('doctor/profile.html', doctor_data=doctor_data)

def update_profile():
    """Update doctor profile information."""
    doctor_data = mongo.db.users.find_one({'umsId': session['umsId']})
    doctor_details = mongo.db.doctorDetails.find_one({'umsId': session['umsId']})
    doctor_data = {**doctor_data, **doctor_details} if doctor_details else doctor_data
    # Get the updated data from the form
    doctor_data['name'] = request.form.get('name')
    doctor_data['email'] = request.form.get('email')
    doctor_data['phoneNumber'] = [request.form.get('phoneNumber')]
    passw = request.form.get('password')
    cpassw = request.form.get('confirm_password')
    doctor_data['updatedAt'] = datetime.now()
    
    if passw != cpassw:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('doctor.profile'))
    else:
        doctor_data.pop('password', None)
        doctor_data['passwordHash'] = generate_password_hash(passw)
        mongo.db.users.update_one({'umsId': session['umsId']}, {'$set': doctor_data})
        mongo.db.login.update_one({'umsId': session['umsId']},
                      {'$set': {'passwordHash': [doctor_data['passwordHash']],
                            'updatedAt': doctor_data['updatedAt'],
                            'email': doctor_data['email']}})
        flash('Profile updated successfully', 'success')
    return redirect(url_for('doctor.profile'))

@doctor_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        doctor_data = {
            'name': request.form.get('name', 'not specified'),
            'email': request.form.get('email', 'not specified'),
            'phoneNumber': request.form.get('phoneNumber', 'not specified'),
            'updatedAt': datetime.now() 
        }
        print("debugger flag")
        print(doctor_data)
        mongo.db.users.update_one({'umsId': session['umsId']}, {'$set': doctor_data})

        # Update the doctor's profile in the doctors collection
        mongo.db.doctors.update_one({'umsId': session['umsId']}, {'$set': {
            'medicalId': request.form.get('medicalId', 'not specified'),
            'specialization':request.form.get('specialization', 'not specified'),
            'updatedAt': doctor_data['updatedAt']
        }})

        # Update the doctor's profile in the doctorDetails collection
        update_data = {
            'status_reason': request.form.get('status_reason', 'not specified'),
            'medicalId': request.form.get('medicalId', 'not specified test'),
            'specialization': request.form.get('specialization', 'not specified'),
            'qualification': request.form.get('qualification', 'not specified'),
            'doctor_status': request.form.get('status', 'not specified'),
            'dob': request.form.get('dob', 'not specified'),
            'address': request.form.get('address', 'not specified'),
            'updatedAt': datetime.now()
        }
        mongo.db.doctorDetails.update_one({'umsId': session['umsId']}, {'$set': update_data}, upsert=True)
        
        # Update the doctor's email and updatedAt in the users collection
        mongo.db.users.update_one({'umsId': session['umsId']}, {'$set': {
            'email': doctor_data.get('email', 'not specified'),
            'updatedAt': doctor_data.get('updatedAt', 'not specified')
        }})
        # Update the doctor's email and updatedAt in the login collection
        mongo.db.login.update_one({'umsId': session['umsId']}, {'$set': {
            'email': doctor_data.get('email', 'not specified'),
            'updatedAt': doctor_data.get('updatedAt', 'not specified')
        }})
        flash('Profile updated successfully', 'success')
        return redirect(url_for('doctor.profile'))

    doctor_data = mongo.db.users.find_one({'umsId': session['umsId']})
    doctor_details = mongo.db.doctorDetails.find_one({'umsId': session['umsId']})
    doctor_data = {**doctor_data, **doctor_details} if doctor_details else doctor_data
    return render_template('doctor/profile-edit.html', doctor_data=doctor_data)

@doctor_bp.route('/inbox')
def inbox():
    if 'doctor' not in session:
        return redirect(url_for('doctor.login'))
    doctor_id = session['doctor']
    messages = mongo.db.messages.find({'receiver': doctor_id})
    return render_template('doctor/inbox.html', messages=messages)

@doctor_bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    if request.method == 'POST':
        # Compose email logic here
        pass
    return render_template('doctor/compose.html')

@doctor_bp.route('/hospital_details')
@login_required
def hospital_details():
    
    return render_template('doctor/hospital_details.html')

@doctor_bp.route('/edit_hospital', methods=['GET', 'POST'])
@login_required
def edit_hospital():
    if request.method == 'POST':
        # Update hospital details logic here
        pass
    return render_template('doctor/edit_hospital.html')

@doctor_bp.route('/appointments')
@login_required
def appointments():
    return render_template('doctor/appointments.html')


@doctor_bp.route('/appointment_history')
@login_required
def appointment_history():
    return render_template('doctor/appointments_history.html')

@doctor_bp.route('/calendar')
@login_required
def calendar():
    return render_template('doctor/calendar.html')

@doctor_bp.route('/timeline')
@login_required
def timeline():
    return render_template('doctor/timeline.html')

@doctor_bp.route('/map')
@login_required
def map():
    return render_template('doctor/map.html')

@doctor_bp.route('/lock_screen')
@login_required
def lock_screen():
    return render_template('doctor/lock_screen.html')

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

@doctor_bp.route('/revoke_hospital', methods=['POST'])
@login_required
def revoke_hospital():
    data = request.get_json()
    hospital_id = data.get('hospital_id')
    if not hospital_id:
        return jsonify({'success': False, 'message': 'Hospital ID is required'}), 400
    doctor_details = mongo.db.doctorDetails.find_one({'umsId': session['umsId']})
    if not doctor_details or 'assignedHospitals' not in doctor_details:
        return jsonify({'success': False, 'message': 'Doctor details not found or no assigned hospitals'}), 404
    if hospital_id not in doctor_details['assignedHospitals']:
        return jsonify({'success': False, 'message': 'Hospital not found in assigned hospitals'}), 404
    # Remove the doctor from the assignedDoctors array in hospitalDetails
    mongo.db.hospitalDetails.update_one(
        {'umsId': hospital_id},
        {'$pull': {'assignedDoctors': session['umsId']}}
    )
    # Remove the hospital from the assignedHospitals array
    mongo.db.doctorDetails.update_one(
        {'umsId': session['umsId']},
        {'$pull': {'assignedHospitals': hospital_id}}
    )
    return jsonify({'success': True, 'message': 'Hospital assignment revoked successfully'})


