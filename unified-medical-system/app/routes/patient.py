from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session, send_file, current_app
from flask_login import login_required, current_user
from app import mongo
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re, uuid
from bson import json_util, ObjectId
from dateutil import parser
from datetime import timezone
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
import os
import io
import base64
import qrcode  # Add this import
import json
import google.generativeai as genai  # Change this import
from google.generativeai import GenerativeModel  # Add this import

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
    
    # Create a dictionary with essential patient details
    patient_qr_data = {
        'umsId': current_user.umsId,
        'name': patient_data.get('name'),
        'email': patient_data.get('email'),
        'phoneNumber': patient_data.get('phoneNumber'),
        'dateOfBirth': str(patient_data.get('dateOfBirth')) if patient_data.get('dateOfBirth') else None,
        'gender': patient_data.get('gender')
    }
    
    # Convert the dictionary to a JSON string
    qr_data = json.dumps(patient_qr_data)
    
    # Generate QR code with the JSON data
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to base64 string
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    barcode_image = base64.b64encode(buffered.getvalue()).decode()
    
    if request.method == 'POST':
        form_data = request.form.to_dict()
        form_data.pop('form_type', None)
        
        # Handle list fields (e.g., phoneNumber)
        for key, value in form_data.items():
            if ',' in value:
                form_data[key] = [item.strip() for item in value.split(',')]
        
        # Separate data for users and patients collections
        user_update_data = {k: v for k, v in form_data.items() if k not in ['dateOfBirth', 'gender']}
        patient_update_data = {k: v for k, v in form_data.items() if k in ['dateOfBirth', 'gender']}
        # Update timestamps
        current_time = datetime.now()
        user_update_data['updatedAt'] = current_time
        patient_update_data['updatedAt'] = current_time
        # Update the databases
        mongo.db.users.update_one({'umsId': current_user.umsId}, {'$set': user_update_data})
        mongo.db.patients.update_one({'umsId': current_user.umsId}, {'$set': patient_update_data})
        flash('Profile updated successfully', 'success')
        return redirect(url_for('patient.profile'))
    return render_template('patient/profile.html', patient_data=patient_data, barcode_image=barcode_image)

@patient_bp.route('/get_appointments', methods=['GET'])
@login_required
def get_appointments():
    """Fetch and return appointment data as JSON, excluding deleted appointments."""
    appointments = list(mongo.db.appointments.find({'patientId': current_user.umsId, 'status': {'$ne': 'deleted'}}))
    for appointment in appointments:
        appointment['_id'] = str(appointment['_id'])
        appointment['appointmentDate'] = appointment['appointmentDate'].strftime('%Y-%m-%d')
        hospital = mongo.db.users.find_one({'umsId': appointment['hospitalId']})
        appointment['hospitalName'] = hospital['name'] if hospital else 'Unknown Hospital'
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

@patient_bp.route('/hospitals', methods=['GET'])
@login_required
def hospitals():
    """Fetch and return hospitals data as JSON."""
    hospitals = list(mongo.db.hospitals.find({'status': 'active'}))
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
            'passwordHash':[generate_password_hash(password)],
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

@patient_bp.route('/medical_records', methods=['GET'])
@login_required
def medical_records():
    """Fetch and return medical records data as JSON."""
    # Find all blocks in the medicalRecords collection
    blocks = list(mongo.db.medicalRecords.find())
    patient_records = []
    for block in blocks:
        # Check each transaction in the block
        for transaction in block['transactions']:
            # If the patientId matches the current user's umsId, add it to the records
            if transaction['patientId'] == current_user.umsId:
                record = {
                    'blockId': str(block['_id']),
                    'index': block['index'],
                    'hash': block['hash'],
                    'createdAt': transaction['createdAt'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(transaction['createdAt'], datetime) else str(transaction['createdAt']),
                    'doctorId': transaction['doctorId'],
                    'hospitalId': transaction['hospitalId'],
                    'Symptoms': transaction['Symptoms'],
                    'Diagnosis': transaction['Diagnosis'],
                    'TreatmentPlan': transaction['TreatmentPlan'],
                    'Prescription': transaction['Prescription'],
                    'AdditionalNotes': transaction['AdditionalNotes'],
                    'FollowUpDate': transaction['FollowUpDate'],
                    'Attachments': transaction['Attachments']
                }
                patient_records.append(record)
    # Sort records by createdAt date, most recent first
    patient_records.sort(key=lambda x: x['createdAt'], reverse=True)
    patient_data = mongo.db.patients.find_one({'umsId': current_user.umsId})
    user_data = mongo.db.users.find_one({'umsId': current_user.umsId})
    patient_data.update(user_data)
    return render_template('patient/medicalrecords.html', records=patient_records, patient_data=patient_data)

@patient_bp.route('/appointments', methods=['GET'])
@login_required
def appointments():
    """Render the appointments page."""
    open_modal = request.args.get('open_modal', 'False')
    patient_data = mongo.db.patients.find_one({'umsId': current_user.umsId})
    user_data = mongo.db.users.find_one({'umsId': current_user.umsId})
    patient_data.update(user_data)
    return render_template('patient/appointments.html', patient_data=patient_data, open_modal=open_modal)

@patient_bp.route('/search_hospitals', methods=['GET'])
@login_required
def search_hospitals():
    search_term = request.args.get('term', '')
    if search_term:
        hospitals = mongo.db.users.find({
            'name': {'$regex': f'^{re.escape(search_term)}', '$options': 'i'},
            'status': 'active',
            'rolesId': 2  # Assuming 2 is the role ID for hospitals
        }, {
            'umsId': 1,
            'name': 1,
            '_id': 0
        }).limit(5)
        hospitals_list = list(hospitals)
        return jsonify(hospitals_list)
    else:
        return jsonify({'error': 'No search term provided'}), 400

@patient_bp.route('/get_doctors_by_hospital/<hospital_id>', methods=['GET'])
@login_required
def get_doctors_by_hospital(hospital_id):
    hospital_details = mongo.db.hospitalDetails.find_one({'umsId': hospital_id})
    if hospital_details and 'assignedDoctors' in hospital_details:
        assigned_doctors = hospital_details['assignedDoctors']
        doctors = list(mongo.db.users.find(
            {'umsId': {'$in': assigned_doctors}, 'rolesId': 3},
            {'umsId': 1, 'name': 1, '_id': 0}
        ))
        return jsonify(doctors)
    return jsonify([])

@patient_bp.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    data = request.json
    patient_id = current_user.umsId
    hospital_id = data.get('hospitalId')
    doctor_id = data.get('doctorId')
    category = data.get('category')
    appointment_date_str = data.get('appointmentDate')
    is_disabled = data.get('isDisabled', False)
    disability_id = data.get('disabilityId')
    reason = data.get('reason')
    if not all([hospital_id, doctor_id, category, appointment_date_str]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    try:
        appointment_date = parser.isoparse(appointment_date_str)
        appointment_date_utc = appointment_date.astimezone(timezone.utc)
        new_appointment = {
            'patientId': patient_id,
            'hospitalId': hospital_id,
            'doctorId': doctor_id,
            'category': category,
            'appointmentDate': appointment_date_utc,
            'status': 'pending',
            'isDisabled': is_disabled,
            'disabilityId': disability_id if is_disabled else None,
            'reason': reason,
            'createdAt': datetime.now(timezone.utc),
            'updatedAt': datetime.now(timezone.utc)
        }
        result = mongo.db.appointments.insert_one(new_appointment)
        if result.inserted_id:
            return jsonify({'success': True, 'message': 'Appointment booked successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to book appointment'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': 'An error occurred while booking the appointment'}), 500

@patient_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    form_data = request.form.to_dict()
    current_password = form_data.get('current_password')
    new_password = form_data.get('new_password')
    confirm_password = form_data.get('confirm_password')
    # Fetch user from login collection
    user = mongo.db.login.find_one({'umsId': current_user.umsId})

    if not user or not check_password_hash(user['passwordHash'][0], current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect.'})

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match.'})
    # Update password in login collection
    new_password_hash = generate_password_hash(new_password)
    mongo.db.login.update_one(
        {'umsId': current_user.umsId},
        {'$set': {'passwordHash': [new_password_hash], 'updatedAt': datetime.now()}}
    )
    # Update updatedAt in users and patients collections
    current_time = datetime.now()
    mongo.db.users.update_one({'umsId': current_user.umsId}, {'$set': {'updatedAt': current_time}})
    mongo.db.patients.update_one({'umsId': current_user.umsId}, {'$set': {'updatedAt': current_time}})

    return jsonify({'success': True, 'message': 'Password updated successfully.'})

@patient_bp.route('/revoke_appointment/<appointment_id>', methods=['POST'])
@login_required
def revoke_appointment(appointment_id):
    try:
        # Find the appointment and update its status to "deleted"
        result = mongo.db.appointments.update_one(
            {'_id': ObjectId(appointment_id), 'patientId': current_user.umsId},
            {'$set': {'status': 'deleted', 'updatedAt': datetime.now()}}
        )

        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Appointment revoked successfully'})
        else:
            return jsonify({'success': False, 'message': 'Appointment not found or you do not have permission to revoke it'})

    except Exception as e:
        print(f"Error revoking appointment: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while revoking the appointment'}), 500

@patient_bp.route('/get_unavailable_slots', methods=['GET'])
@login_required
def get_unavailable_slots():
    hospital_id = request.args.get('hospitalId')
    doctor_id = request.args.get('doctorId')
    
    if not hospital_id or not doctor_id:
        return jsonify({'error': 'Missing hospitalId or doctorId'}), 400

    unavailable_slots = list(mongo.db.appointments.find({
        'hospitalId': hospital_id,
        'doctorId': doctor_id,
        'status': {'$in': ['pending', 'approved']},
        'appointmentDate': {'$gte': datetime.now(timezone.utc)}
    }, {'appointmentDate': 1, '_id': 0}))

    return json_util.dumps(unavailable_slots)

@patient_bp.route('/api/medical_records/<block_id>/pdf', methods=['GET'])
@login_required
def download_medical_record_pdf(block_id):
    # Find the specific block
    block = mongo.db.medicalRecords.find_one({'_id': ObjectId(block_id)})
    if not block:
        return jsonify({'error': 'Record not found'}), 404
    # Find the transaction for the current user
    transaction = next((t for t in block['transactions'] if t['patientId'] == current_user.umsId), None)
    if not transaction:
        return jsonify({'error': 'Record not found for this patient'}), 404
    # Create a PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    # Container for the 'Flowable' objects
    elements = []
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=1))
    styles.add(ParagraphStyle(name='Center', alignment=1))
    # Add UMS logo
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'ums_logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
        elements.append(logo)
    # Add title
    title = Paragraph("Unified Medical System", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    # Add subtitle
    subtitle = Paragraph("Medical Certificate", styles['Heading2'])
    elements.append(subtitle)
    elements.append(Spacer(1, 24))
    # Add content
    content = f"""
    This is to certify that the patient with UMS ID: {current_user.umsId} has been examined and treated at our facility.
    The following medical record details the diagnosis, treatment, and recommendations for the patient.
    """
    elements.append(Paragraph(content, styles['Justify']))
    elements.append(Spacer(1, 12))
    # Create a table for the medical record details
    data = [
        ['Patient ID:', current_user.umsId],
        ['Date of Record:', transaction['createdAt'].strftime('%Y-%m-%d %H:%M:%S')],
        ['Doctor ID:', transaction['doctorId']],
        ['Hospital ID:', transaction['hospitalId']],
        ['Symptoms:', transaction['Symptoms']],
        ['Diagnosis:', transaction['Diagnosis']],
        ['Treatment Plan:', transaction['TreatmentPlan']],
        ['Prescription:', transaction['Prescription']],
        ['Additional Notes:', transaction['AdditionalNotes']],
        ['Follow-up Date:', transaction['FollowUpDate']],
    ]
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 1), (-1, -1), colors.lightgreen),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 24))
    # Add footer
    footer_text = f"This medical certificate is electronically generated and is valid without a signature.\nBlock Hash: {block['hash']}"
    footer = Paragraph(footer_text, styles['Center'])
    elements.append(footer)
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'medical_certificate_{block_id}.pdf', mimetype='application/pdf')

@patient_bp.route('/api/verify_blockchain/<block_id>', methods=['GET'])
@login_required
def verify_blockchain(block_id):
    # Implement the blockchain verification logic here
    # This should interact with your Blockchain class from meddata.py
    # For now, we'll return a dummy response
    verified = True  # Replace this with actual verification logic
    return jsonify({'verified': verified})

@patient_bp.route('/medical_insights', methods=['GET'])
@login_required
def medical_insights():
    """Render the medical insights page with summarized records."""
    # Get patient's medical records
    blocks = list(mongo.db.medicalRecords.find())
    patient_records = []
    
    for block in blocks:
        for transaction in block['transactions']:
            if transaction['patientId'] == current_user.umsId:
                record = {
                    'date': transaction['createdAt'],
                    'diagnosis': transaction['Diagnosis'],
                    'treatment': transaction['TreatmentPlan'],
                    'prescription': transaction['Prescription'],
                    'notes': transaction['AdditionalNotes']
                }
                patient_records.append(record)
    
    # Sort records by date
    patient_records.sort(key=lambda x: x['date'], reverse=True)
    
    # Get patient data for the template
    patient_data = mongo.db.patients.find_one({'umsId': current_user.umsId})
    user_data = mongo.db.users.find_one({'umsId': current_user.umsId})
    patient_data.update(user_data)
    
    return render_template('patient/medical_insights.html', 
                         patient_data=patient_data,
                         records=patient_records)

@patient_bp.route('/api/medical_insights/query', methods=['POST'])
@login_required
def query_medical_insights():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        # Get patient's medical records
        blocks = list(mongo.db.medicalRecords.find())
        patient_records = []
        
        for block in blocks:
            for transaction in block['transactions']:
                if transaction['patientId'] == current_user.umsId:
                    patient_records.append(transaction)
        
        # Initialize Gemini model
        model = GenerativeModel('gemini-pro')
        
        # Create improved context and prompt
        context = f"""
        You are an advanced medical AI assistant, designed to help patients understand their medical history and provide valuable insights. You have access to the patient's medical records and can analyze them to answer questions and provide visualizations when appropriate.

        When responding:
        1. Be conversational and empathetic
        2. If the user asks who you are, introduce yourself as a medical AI assistant
        3. Always try to reference relevant medical records when answering questions
        4. Suggest follow-up questions when appropriate
        5. If no medical records are relevant to the query, still provide a helpful response

        Current medical records:
        {json.dumps(patient_records, default=str)}

        User query: "{query}"

        If the response needs visualization, return JSON in this format:
        {{
            "needs_visualization": true,
            "chartType": "bar"/"line"/"pie",
            "data": {{
                "labels": [...],
                "datasets": [{{
                    "label": "...",
                    "data": [...]
                }}]
            }},
            "explanation": "..."
        }}

        Otherwise, provide a natural, conversational response that helps the user understand their medical history.
        """
        
        response = model.generate_content(context)
        response_text = response.text.strip()
        
        # Try to parse as JSON for visualization
        try:
            viz_data = json.loads(response_text)
            return jsonify(viz_data)
        except json.JSONDecodeError:
            # If not JSON, return as regular text response
            return jsonify({
                "needs_visualization": False,
                "explanation": response_text
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

