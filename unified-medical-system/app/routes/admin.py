from pydoc import doc
import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required
from app import mongo
from app.models import User
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes.auth import login
from app.synthbot_ai.nlp_models.outbreak_detection import analyze_outbreak
from bson import ObjectId

admin_bp = Blueprint('admin', __name__)

def get_global_admin_data():
    """Get global admin data from the database."""
    try:
        return {
            'patients_count': mongo.db.patients.count_documents({}),
            'doctors_count': mongo.db.doctors.count_documents({}),
            'hospitals_count': mongo.db.hospitals.count_documents({}),
            'new_hospitals_24h': mongo.db.hospitals.count_documents({'createdAt': {'$gte': datetime.now() - timedelta(hours=24)}}),
            'new_doctors_24h': mongo.db.doctors.count_documents({'createdAt': {'$gte': datetime.now() - timedelta(hours=24)}}),
            'new_patients_24h': mongo.db.patients.count_documents({'createdAt': {'$gte': datetime.now() - timedelta(hours=24)}}),
            'new_appointments_24h': mongo.db.appointments.count_documents({'createdAt': {'$gte': datetime.now() - timedelta(hours=24)}})
        }
    except Exception as e:
        print(f"Error getting global admin data: {str(e)}")
        return {
            'patients_count': 0,
            'doctors_count': 0,
            'hospitals_count': 0,
            'new_hospitals_24h': 0,
            'new_doctors_24h': 0,
            'new_patients_24h': 0,
            'new_appointments_24h': 0
        }

def get_admin_data():
    """Get admin data from the database."""
    try:
        return mongo.db.users.find_one({'umsId': session['umsId']})
    except Exception as e:
        print(f"Error getting admin data: {str(e)}")
        return None

#admin dashboard
@admin_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Render the admin dashboard."""
    admin_data = get_admin_data()
    global_admin_data = get_global_admin_data()
    return render_template('admin/dashboard.html', admin_data=admin_data, global_admin_data=global_admin_data)

#admin profile
@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle admin profile view and updates."""
    admin_data = get_admin_data()
    if admin_data:
        admin_data['phoneNumber'] = admin_data.get('phoneNumber', [None])[0]
    global_admin_data = get_global_admin_data()
    
    if request.method == 'POST':
        if request.form.get('form_type') == 'update_profile':
            return update_profile()
    return render_template('admin/profile.html', admin_data=admin_data, global_admin_data=global_admin_data)


def update_profile():
    """Update admin profile information."""
    admin_data = get_admin_data()
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
            }
    return jsonify(patients)


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
        return render_template('admin/patient-profile.html', patient_data=patient_data, admin_data = admin_data)
    else:
        flash('Patient not found', 'danger')
        return redirect(url_for('admin.index'))
    
    
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
            }
    return jsonify(doctors)

#doctor profile view
@admin_bp.route('/edit_doctor/<string:doctor_id>', methods=['POST','GET'])
@login_required
def edit_doctor(doctor_id):
    """Fetch and display doctor profile for editing."""
    doctor_data = mongo.db.doctors.find_one({'umsId': doctor_id})
    if not doctor_data:
        flash('Doctor not found', 'danger')
        return redirect(url_for('admin.index'))
    # Fetch user information from users collection for not specified values
    user_info = mongo.db.users.find_one({'umsId': doctor_id})
    doctor_data['name'] = doctor_data.get('name', user_info.get('name', 'None'))
    doctor_data['email'] = doctor_data.get('email', user_info.get('email', 'None'))
    doctor_data['phone'] = doctor_data.get('phone', user_info.get('phoneNumber', ['None'])[0])
    doctor_data['specialization'] = doctor_data.get('specialization', 'None')
    doctor_data['state'] = doctor_data.get('state', user_info.get('state', 'None'))
    doctor_data['address'] = doctor_data.get('address', user_info.get('address', 'None'))
    doctor_data['updatedAt'] = doctor_data.get('updatedAt', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    doctor_data['createdAt'] = doctor_data.get('createdAt', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    doctor_data['status'] = doctor_data.get('status', 'None')
    return render_template('admin/doctor-profile.html', doctor_data=doctor_data, admin_data=admin_data)

#approve doctor
@admin_bp.route('/api/approve_doctor', methods=['POST'])
@login_required
def approve_doctor():
    """Approve a doctor and update their status and updatedAt time."""
    umsId = request.form.get('umsId')
    current_time = datetime.now()
    mongo.db.login.update_one({'umsId': umsId}, {'$set': {'status': 'active', 'updatedAt': current_time}})
    mongo.db.doctors.update_one({'umsId': umsId}, {'$set': {'status': 'active', 'updatedAt': current_time}})
    mongo.db.users.update_one({'umsId': umsId}, {'$set': {'status': 'active', 'updatedAt': current_time}})
    return jsonify({'message': 'Doctor approved successfully'})

#reject doctor
@admin_bp.route('/api/reject_doctor', methods=['POST'])
@login_required
def reject_doctor():
    """Reject a doctor and update their status and updatedAt time."""
    umsId = request.form.get('umsId')
    current_time = datetime.now()
    mongo.db.login.update_one({'umsId': umsId}, {'$set': {'status': 'rejected', 'updatedAt': current_time}})
    mongo.db.doctors.update_one({'umsId': umsId}, {'$set': {'status': 'rejected', 'updatedAt': current_time}})
    mongo.db.users.update_one({'umsId': umsId}, {'$set': {'status': 'rejected', 'updatedAt': current_time}})
    return jsonify({'message': 'Doctor rejected successfully'})

#doctot awaiting approval list
@admin_bp.route('/api/doctors/awaiting-approval', methods=['GET'])
@login_required
def api_doctors_awaiting_approval():
    """Fetch and return data of doctors awaiting approval as JSON."""
    # Fetch doctors awaiting approval from the login collection
    awaiting_approval = list(mongo.db.login.find({'rolesId': 3, 'status': 'awaiting_approval'}))
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
    return jsonify(doctors_data)

#hospitals list view with status "active"
@admin_bp.route('/api/hospitals', methods=['GET'])
@login_required
def api_hospitals():
    """Fetch and return active hospital data as JSON."""
    hospitals = list(mongo.db.hospitals.find())
    hospitals_user_info = list(mongo.db.users.find({'rolesId': 2, 'status': 'active'}))
    
    hospital_info_dict = {hospital['umsId']: hospital for hospital in hospitals_user_info}
    
    for hospital in hospitals:
        hospital['_id'] = str(hospital['_id'])  # Convert ObjectId to string
        hospital_info = hospital_info_dict.get(hospital['umsId'])
        if hospital_info:
            hospital['name'] = hospital_info.get('name')  # Ensure this field exists
            hospital['email'] = hospital_info.get('email')
            hospital['state'] = hospital_info.get('state')
            hospital['status'] = hospital_info.get('status')
    return jsonify(hospitals)

@admin_bp.route('/api/hospitals/awaiting_approval', methods=['GET'])
@login_required
def api_hospitals_awaiting_approval():
    """Fetch and return hospital data with status 'awaiting_approval' as JSON."""
    hospitals = list(mongo.db.users.find({'rolesId': 2, 'status': 'awaiting_approval'}))
    for hospital in hospitals:
        hospital['_id'] = str(hospital['_id'])  # Convert ObjectId to string
    return jsonify(hospitals)

@admin_bp.route('/api/hospitals/approve', methods=['POST'])
@login_required
def approve_hospital():
    """Approve a hospital."""
    if request.method == 'POST':
        umsId = request.form.get('umsId')
        if umsId:
            mongo.db.users.update_one({'umsId': umsId}, {'$set': {'status': 'active', 'updatedAt': datetime.now()}})
            mongo.db.hospitals.update_one({'umsId': umsId}, {'$set': {'status': 'active', 'updatedAt': datetime.now()}})
            return jsonify({'message': 'Hospital approved successfully.'})
        else:
            return jsonify({'error': 'UMS ID not provided.'}), 400
    else:
        return jsonify({'error': 'Invalid request method.'}), 405
    
@admin_bp.route('/api/hospitals/reject', methods=['POST'])
@login_required
def reject_hospital():
    """Reject a hospital."""
    if request.method == 'POST':
        umsId = request.form.get('umsId')
        if umsId:
            mongo.db.users.update_one({'umsId': umsId}, {'$set': {'status': 'rejected', 'updatedAt': datetime.now()}})
            mongo.db.hospitals.update_one({'umsId': umsId}, {'$set': {'status': 'rejected', 'updatedAt': datetime.now()}})
            return jsonify({'message': 'Hospital rejected successfully.'})
        else:
            return jsonify({'error': 'UMS ID not provided.'}), 400
    else:
        return jsonify({'error': 'Invalid request method.'}), 405

@admin_bp.route('/outbreakmap', methods=['GET'])
@login_required
def outbreakmap():
    return render_template('admin/outbreak_map.html')
#database chat
@admin_bp.route('/dbchat', methods=['GET'])
@login_required
def dbchat():
    """Render the database chat interface."""
    admin_data = get_admin_data()
    return render_template('admin/dbchat.html', admin_data=admin_data)

@admin_bp.route('/api/dbchat', methods=['POST'])
@login_required
def process_dbchat():
    """Process database chat queries and return results."""
    query = request.json.get('query')
    try:
        # TODO: Implement actual database query processing logic
        # This is a placeholder response
        return jsonify({
            'text': f'Processing query: {query}',
            'visualization': {
                'type': 'chart',
                'data': {
                    'type': 'bar',
                    'data': {
                        'labels': ['Sample'],
                        'datasets': [{
                            'label': 'Sample Data',
                            'data': [1]
                        }]
                    }
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Calendar view route
@admin_bp.route('/calendar', methods=['GET'])
@login_required
def calendar():
    """Render the admin calendar view."""
    admin_data = get_admin_data()
    global_admin_data = get_global_admin_data()
    return render_template('admin/calendar.html', 
                         admin_data=admin_data,
                         global_admin_data=global_admin_data)

# Calendar events API
@admin_bp.route('/api/events', methods=['GET'])
@login_required
def get_events():
    """Get all calendar events."""
    # Get start and end date from query parameters (if provided)
    start = request.args.get('start', None)
    end = request.args.get('end', None)
    
    # Convert string dates to datetime if provided
    if start:
        start = datetime.fromisoformat(start.replace('Z', '+00:00'))
    if end:
        end = datetime.fromisoformat(end.replace('Z', '+00:00'))
    
    # Query events from MongoDB
    query = {}
    if start:
        query['start'] = {'$gte': start}
    if end:
        query['end'] = {'$lte': end}
        
    events = list(mongo.db.events.find(query))
    
    # Format events for FullCalendar
    formatted_events = []
    for event in events:
        formatted_events.append({
            'id': str(event['_id']),
            'title': event.get('title'),
            'start': event.get('start').isoformat(),
            'end': event.get('end').isoformat() if event.get('end') else None,
            'allDay': event.get('allDay', False),
            'backgroundColor': event.get('backgroundColor', '#3788d8'),
            'borderColor': event.get('borderColor', '#3788d8')
        })
    
    return jsonify(formatted_events)

@admin_bp.route('/api/add_event', methods=['POST'])
@login_required
def add_event():
    """Add a new event to the calendar."""
    try:
        event_data = request.json
        event = {
            'title': event_data['title'],
            'start': datetime.fromisoformat(event_data['start'].replace('Z', '+00:00')),
            'end': datetime.fromisoformat(event_data['end'].replace('Z', '+00:00')),
            'allDay': event_data['allDay'],
            'createdBy': session['umsId'],
            'createdAt': datetime.now(),
            'updatedAt': datetime.now()
        }
        result = mongo.db.events.insert_one(event)
        return jsonify({'success': True, 'id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/delete_event', methods=['POST'])
@login_required
def delete_event():
    """Delete an event from the calendar."""
    try:
        event_id = request.json['id']
        mongo.db.events.delete_one({'_id': ObjectId(event_id)})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
