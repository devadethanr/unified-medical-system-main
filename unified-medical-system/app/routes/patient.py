from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_required, current_user
from app import mongo
from datetime import datetime
from werkzeug.security import generate_password_hash
import re, uuid

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard', methods=['GET'])
@login_required
def index():
    """Render the patient dashboard."""
    patient_data = mongo.db.patients.find_one({'umsId': current_user.umsId})
    user_data = mongo.db.users.find_one({'umsId': current_user.umsId})
    patient_data.update(user_data)
    return render_template('patient/dashboard.html', patient_data=patient_data)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle patient profile view and updates."""
    patient_data = mongo.db.patients.find_one({'umsId': current_user.umsId})
    user_data = mongo.db.users.find_one({'umsId': current_user.umsId})
    patient_data.update(user_data)
    if request.method == 'POST':
        if request.form.get('form_type') == 'update_profile':
            return update_profile()
    return render_template('patient/profile.html', patient_data=patient_data)

def update_profile():
    """Update patient profile information."""
    patient_data = mongo.db.patients.find_one({'umsId': current_user.umsId})
    user_data = mongo.db.users.find_one({'umsId': current_user.umsId})
    patient_data.update(user_data)
    
    patient_data['name'] = request.form.get('name')
    patient_data['email'] = request.form.get('email')
    patient_data['phoneNumber'] = [request.form.get('phoneNumber')]
    patient_data['dateOfBirth'] = request.form.get('dateOfBirth')
    patient_data['gender'] = request.form.get('gender')
    patient_data['updatedAt'] = datetime.now()
    
    passw = request.form.get('password')
    cpassw = request.form.get('confirm_password')
    
    if passw and passw != cpassw:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('patient.profile'))
    elif passw:
        patient_data['passwordHash'] = generate_password_hash(passw)
    
    mongo.db.patients.update_one({'umsId': current_user.umsId}, {'$set': patient_data})
    mongo.db.users.update_one({'umsId': current_user.umsId}, {'$set': patient_data})
    mongo.db.login.update_one({'umsId': current_user.umsId},
                  {'$set': {'passwordHash': patient_data.get('passwordHash'),
                        'updatedAt': patient_data['updatedAt'],
                        'email': patient_data['email']}})
    flash('Profile updated successfully', 'success')
    return redirect(url_for('patient.profile'))

@patient_bp.route('/api/appointments', methods=['GET'])
@login_required
def api_appointments():
    """Fetch and return appointment data as JSON."""
    appointments = list(mongo.db.appointments.find({'patientId': current_user.umsId}))
    for appointment in appointments:
        appointment['_id'] = str(appointment['_id'])
        appointment['date'] = appointment['date'].strftime('%Y-%m-%d') if appointment.get('date') else None
    return jsonify(appointments)

@patient_bp.route('/api/medical_records', methods=['GET'])
@login_required
def api_medical_records():
    """Fetch and return medical records data as JSON."""
    records = list(mongo.db.medical_records.find({'patientId': current_user.umsId}))
    for record in records:
        record['_id'] = str(record['_id'])
        record['date'] = record['date'].strftime('%Y-%m-%d') if record.get('date') else None
    return jsonify(records)

@patient_bp.route('/api/doctors', methods=['GET'])
@login_required
def api_doctors():
    """Fetch and return doctors data as JSON."""
    doctors = list(mongo.db.doctors.find())
    for doctor in doctors:
        doctor['_id'] = str(doctor['_id'])
    return jsonify(doctors)

@patient_bp.route('/api/hospitals', methods=['GET'])
@login_required
def api_hospitals():
    """Fetch and return hospitals data as JSON."""
    hospitals = list(mongo.db.hospitals.find())
    for hospital in hospitals:
        hospital['_id'] = str(hospital['_id'])
    return jsonify(hospitals)

@patient_bp.route('/api/support_requests', methods=['GET', 'POST'])
@login_required
def api_support_requests():
    """Handle support requests."""
    if request.method == 'POST':
        new_request = {
            'patientId': current_user.umsId,
            'subject': request.form.get('subject'),
            'message': request.form.get('message'),
            'status': 'open',
            'createdAt': datetime.now(),
            'updatedAt': datetime.now()
        }
        mongo.db.support_requests.insert_one(new_request)
        flash('Support request submitted successfully', 'success')
        return redirect(url_for('patient.index'))
    else:
        support_requests = list(mongo.db.support_requests.find({'patientId': current_user.umsId}))
        for request in support_requests:
            request['_id'] = str(request['_id'])
            request['createdAt'] = request['createdAt'].strftime('%Y-%m-%d %H:%M:%S') if request.get('createdAt') else None
        return jsonify(support_requests)

@patient_bp.route('/api/notifications', methods=['GET'])
@login_required
def api_notifications():
    """Fetch and return notifications data as JSON."""
    notifications = list(mongo.db.notifications.find({'userId': current_user.umsId}))
    for notification in notifications:
        notification['_id'] = str(notification['_id'])
        notification['createdAt'] = notification['createdAt'].strftime('%Y-%m-%d %H:%M:%S') if notification.get('createdAt') else None
    return jsonify(notifications)

def generate_patient_id():
    return 'UMSP' + re.sub('-', '', str(uuid.uuid4()))[:8].upper()

@patient_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if password != request.form['confirm_password']:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('patient.register'))
        
        existing_user = mongo.db.users.find_one({'email': email})
        if existing_user:
            flash('Email already exists! Please login.', 'error')
            return redirect(url_for('patient.register'))
        
        name = request.form['name']
        phone_number = request.form['phonenumber']
        state = request.form['state']
        umsId = generate_patient_id()
        created_at = updated_at = datetime.now()
        
        new_user = {
            'umsId': umsId,
            'name': name,
            'email': email,
            'phoneNumber': [phone_number],
            'state': state,
            'status': 'active',
            'createdAt': created_at,
            'updatedAt': updated_at,
            'passwordHash': generate_password_hash(password),
            'rolesId': 4
        }
        
        mongo.db.users.insert_one(new_user)
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
            'passwordHash': new_user['passwordHash'],
            'rolesId': 4,
            'status': 'active',
        })

        flash('User registered successfully!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('patient/register.html')