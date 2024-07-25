from pydoc import doc
import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required
from app import mongo
from app.models import User
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes.auth import login


admin_bp = Blueprint('admin', __name__)

# global data for admin
global_admin_data = {
    'patients_count': mongo.db.patients.count_documents({}),
    'doctors_count': mongo.db.doctors.count_documents({}),
    'hospitals_count': mongo.db.hospitals.count_documents({})
}

#admin dashboard
@admin_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Render the admin dashboard."""
    global admin_data
    admin_data = mongo.db.users.find_one({'umsId': session['umsId']})
    print(admin_data) #for debugging
    return render_template('admin/dashboard.html', admin_data=admin_data, global_admin_data=global_admin_data)


#admin profile
@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle admin profile view and updates."""
    global admin_data
    admin_data = mongo.db.users.find_one({'umsId': session['umsId']})
    admin_data['phoneNumber'] = admin_data.get('phoneNumber', [None])[0]
    if request.method == 'POST':
         if request.form.get('form_type') == 'update_profile':
            return update_profile()
    return render_template('admin/profile.html', admin_data=admin_data, global_admin_data=global_admin_data)

def update_profile():
    """Update admin profile information."""
    admin_data = mongo.db.users.find_one({'umsId': session['umsId']})
    # Get the updated data from the form
    admin_data['name'] = request.form.get('name')
    admin_data['email'] = request.form.get('email')
    admin_data['phoneNumber'] = [request.form.get('phoneNumber')]
    passw = request.form.get('password')
    cpassw = request.form.get('confirm_password')
    admin_data['updatedAt'] = datetime.now()
    
    if passw != cpassw:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('admin.profile'))
    else:
        print('flag2') #for debugging
        admin_data.pop('password', None)
        admin_data['passwordHash'] = generate_password_hash(passw)
        mongo.db.users.update_one({'umsId': session['umsId']}, {'$set': admin_data})
        mongo.db.login.update_one({'umsId': session['umsId']},
                      {'$set': {'passwordHash': [admin_data['passwordHash']],
                            'updatedAt': admin_data['updatedAt'],
                            'email': admin_data['email']}})
        flash('Profile updated successfully', 'success')
    return redirect(url_for('admin.profile'))

# patients list view
@admin_bp.route('/api/patients', methods=['GET'])
@login_required
def api_patients():
    """Fetch and return patient data as JSON."""
    # Fetch patients and user information
    patients = list(mongo.db.patients.find())
    patients__user_info = list(mongo.db.users.find({'rolesId': 4}))
    # Create a dictionary to map userId to user information
    patient_info_dict = {patient['umsId']: patient for patient in patients__user_info}
    for patient in patients:
        patient['_id'] = str(patient['_id'])  # Convert ObjectId to string
        patient['createdAt'] = patient['createdAt'].strftime('%Y-%m-%d %H:%M:%S') if patient.get('createdAt') else None
        patient['updatedAt'] = patient['updatedAt'].strftime('%Y-%m-%d %H:%M:%S') if patient.get('updatedAt') else None
        # Add user information to the patient object
        patient_info = patient_info_dict.get(patient['umsId'])
        if patient_info:
            patient['user_info'] = {
                'name': patient_info.get('name'),
                'email': patient_info.get('email'),
                # Add more fields as needed
            }
    return jsonify(patients)

#doctor list view
@admin_bp.route('/api/doctors', methods=['GET'])
@login_required
def api_doctors():
    """Fetch and return doctor data as JSON."""
    # Fetch doctors and user information
    doctors = list(mongo.db.doctors.find())
    doctors__user_info = list(mongo.db.users.find({'rolesId': 3}))
    doctor_info_dict = {doctor['umsId']: doctor for doctor in doctors__user_info}
    for doctor in doctors:
        doctor['_id'] = str(doctor['_id'])
        doctor['createdAt'] = doctor['createdAt'].strftime('%Y-%m-%d %H:%M:%S') if doctor.get('createdAt') else None
        doctor['updatedAt'] = doctor['updatedAt'].strftime('%Y-%m-%d %H:%M:%S') if doctor.get('updatedAt') else None
        doctor_info = doctor_info_dict.get(doctor['umsId'])
        if doctor_info:
            doctor['user_info'] = {
                'name': doctor_info.get('name'),
                'email': doctor_info.get('email'),
                'gender': doctor_info.get('gender'),
                'specialization': doctor_info.get('specialization'),
                # Add more fields as needed
            }
    return jsonify(doctors)

@admin_bp.route('/api/doctors/awaiting-approval', methods=['GET'])
@login_required
def api_doctors_awaiting_approval():
    """Fetch and return data of doctors awaiting approval as JSON."""
    # Fetch doctors awaiting approval from the login collection
    awaiting_approval = list(mongo.db.login.find({'rolesId': 3, 'status': 'awaiting_approval'}))
    print(f"Found {len(awaiting_approval)} doctors awaiting approval")
    
    doctors_data = []
    for login_entry in awaiting_approval:
        umsId = login_entry['umsId']
        # Fetch user info
        user_info = mongo.db.users.find_one({'umsId': umsId})
        # Fetch doctor info
        doctor_info = mongo.db.doctors.find_one({'umsId': umsId}) 
        if user_info and doctor_info:
            doctor_data = {
                'umsId': umsId,
                'name': user_info.get('name'),
                'email': user_info.get('email'),
                'gender': user_info.get('gender'),
                'phoneNumber': user_info.get('phoneNumber', [None])[0],
                'specialization': doctor_info.get('specialization'),
                'qualification': doctor_info.get('qualification'),
                'experience': doctor_info.get('experience'),
                'createdAt': login_entry.get('createdAt'),
                'updatedAt': login_entry.get('updatedAt')
            } 
            # Convert ObjectId to string and format dates
            doctor_data['_id'] = str(doctor_info['_id'])
            doctor_data['createdAt'] = doctor_data['createdAt'].strftime('%Y-%m-%d %H:%M:%S') if doctor_data.get('createdAt') else None
            doctor_data['updatedAt'] = doctor_data['updatedAt'].strftime('%Y-%m-%d %H:%M:%S') if doctor_data.get('updatedAt') else None
            doctors_data.append(doctor_data)
    print(f"Returning {len(doctors_data)} doctors data")
    print(doctors_data) #for debugging
    return jsonify(doctors_data)

#single patient view
@admin_bp.route('/patient_profile/<string:patient_id>', methods=['POST', 'GET'])
@login_required
def patient_profile(patient_id):
    """Retrieve and display patient profile information."""
    patient_data = []
    patient = mongo.db.patients.find_one({'umsId': patient_id})
    patient_user_info = mongo.db.users.find_one({'umsId': patient_id})
    
    if patient and patient_user_info:
        patient_data.append(patient)
        patient_data.append(patient_user_info)
        print(patient_data) #for debugging
        return render_template('admin/patient-profile.html', patient_data=patient_data, admin_data = admin_data)
    else:
        flash('Patient not found', 'danger')
        return redirect(url_for('admin.index'))