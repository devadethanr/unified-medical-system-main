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
from bson.objectid import ObjectId
from datetime import datetime
from io import StringIO, BytesIO


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
    #changes
    
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

from bson import json_util


@hospital_bp.route('/appointments', methods=['GET'])
@login_required
def appointments():
    hospital_id = session['umsId']
    appointments = list(mongo.db.appointments.find({
        'hospitalId': hospital_id,
        'status': {'$ne': 'deleted'}
    }))

    # Fetch patient and doctor names, and process the appointments
    for appointment in appointments:
        patient = mongo.db.users.find_one({'umsId': appointment.get('patientId')})
        doctor = mongo.db.users.find_one({'umsId': appointment.get('doctorId')}) if 'doctorId' in appointment else None
        appointment['patientName'] = patient['name'] if patient else 'Unknown'
        appointment['doctorName'] = doctor['name'] if doctor else 'Not Assigned'
        
        # Convert ObjectId to string for JSON serialization
        appointment['_id'] = str(appointment['_id'])
        
        # Convert datetime objects to string
        if 'appointmentDate' in appointment:
            appointment['appointmentDate'] = appointment['appointmentDate'].strftime('%Y-%m-%d')
        
        # Ensure all potential fields are included, even if they're not in the database
        appointment.setdefault('appointmentTime', '')
        appointment.setdefault('reason', '')
        appointment.setdefault('status', '')

    # Fetch assigned doctors
    hospital_details = mongo.db.hospitalDetails.find_one({'umsId': hospital_id})
    assigned_doctor_ids = hospital_details.get('assignedDoctors', []) if hospital_details else []
    assigned_doctors = list(mongo.db.users.find({'umsId': {'$in': assigned_doctor_ids}}, {'umsId': 1, 'name': 1}))

    return render_template('hospital/appointments.html', 
                           appointments=json_util.dumps(appointments),
                           assigned_doctors=json_util.dumps(assigned_doctors))

@hospital_bp.route('/update_appointment', methods=['POST'])
@login_required
def update_appointment():
    data = request.json
    appointment_id = data.get('appointmentId')
    doctor_id = data.get('doctorId')

    if not appointment_id or not doctor_id:
        return jsonify({'success': False, 'message': 'Missing required data'})

    try:
        result = mongo.db.appointments.update_one(
            {'_id': ObjectId(appointment_id)},
            {
                '$set': {
                    'doctorId': doctor_id,
                    'updatedAt': datetime.now(),
                    'status': 'Approved : ' + doctor_id
                }
            },
            upsert=True
        )
        if result.modified_count > 0 or result.upserted_id:
            return jsonify({'success': True, 'message': 'Appointment updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'No appointment found with the given ID'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@hospital_bp.route('/cancel_appointment', methods=['POST'])
@login_required
def cancel_appointment():
    data = request.json
    appointment_id = data.get('appointmentId')

    if not appointment_id:
        return jsonify({'success': False, 'message': 'Missing appointment ID'})

    try:
        result = mongo.db.appointments.update_one(
            {'_id': ObjectId(appointment_id)},
            {'$set': {'status': 'deleted'}}
        )
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Appointment cancelled successfully'})
        else:
            return jsonify({'success': False, 'message': 'No appointment found with the given ID'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@hospital_bp.route('/reports', methods=['GET'])
@login_required
def reports():
    hospital_id = session['umsId']
    
    # Get monthly appointment statistics
    current_year = datetime.now().year
    monthly_stats = []
    
    for month in range(1, 13):
        # Count appointments per month
        appointments_count = mongo.db.appointments.count_documents({
            'hospitalId': hospital_id,
            'appointmentDate': {
                '$gte': datetime(current_year, month, 1),
                '$lt': datetime(current_year, month + 1 if month < 12 else 1, 1)
            },
            'status': {'$ne': 'deleted'}
        })
        
        monthly_stats.append({
            'month': datetime(2000, month, 1).strftime('%B'),
            'count': appointments_count
        })
    
    # Get assigned doctor count
    hospital_details = mongo.db.hospitalDetails.find_one({'umsId': hospital_id})
    doctor_count = len(hospital_details.get('assignedDoctors', [])) if hospital_details else 0
    
    # Get recent appointments
    recent_appointments = list(mongo.db.appointments.find({
        'hospitalId': hospital_id,
        'status': {'$ne': 'deleted'}
    }).sort('appointmentDate', -1).limit(5))
    
    for appointment in recent_appointments:
        patient = mongo.db.users.find_one({'umsId': appointment.get('patientId')})
        doctor = mongo.db.users.find_one({'umsId': appointment.get('doctorId')}) if 'doctorId' in appointment else None
        appointment['patientName'] = patient['name'] if patient else 'Unknown'
        appointment['doctorName'] = doctor['name'] if doctor else 'Not Assigned'
    
    return render_template('hospital/reports.html', 
                           monthly_stats=monthly_stats,
                           doctor_count=doctor_count,
                           recent_appointments=recent_appointments)

@hospital_bp.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    from flask import make_response
    import csv
    from io import StringIO
    import pandas as pd
    
    hospital_id = session['umsId']
    hospital_data = get_hospital_data()
    report_type = request.form.get('report_type', 'full')
    date_start = request.form.get('date_start', '')
    date_end = request.form.get('date_end', '')
    report_format = request.form.get('format', 'csv')
    
    # Filter based on date range if provided
    query = {'hospitalId': hospital_id, 'status': {'$ne': 'deleted'}}
    if date_start and date_end:
        try:
            start_date = datetime.strptime(date_start, '%Y-%m-%d')
            end_date = datetime.strptime(date_end, '%Y-%m-%d')
            query['appointmentDate'] = {'$gte': start_date, '$lte': end_date}
        except ValueError:
            pass
    
    # Get appointment data based on report type
    if report_type == 'Monthly Appointment Summary':
        appointments = list(mongo.db.appointments.find(query))
        # Process appointments for report
        processed_data = []
        for appointment in appointments:
            patient = mongo.db.users.find_one({'umsId': appointment.get('patientId')})
            doctor = mongo.db.users.find_one({'umsId': appointment.get('doctorId')}) if 'doctorId' in appointment else None
            
            processed_data.append({
                'Date': appointment.get('appointmentDate').strftime('%Y-%m-%d') if 'appointmentDate' in appointment and appointment['appointmentDate'] else 'N/A',
                'Patient': patient['name'] if patient else 'Unknown',
                'Doctor': doctor['name'] if doctor else 'Not Assigned',
                'Status': appointment.get('status', 'Unknown')
            })
    elif report_type == 'Doctor Performance':
        # Get all doctors for this hospital
        hospital_details = mongo.db.hospitalDetails.find_one({'umsId': hospital_id})
        doctor_ids = hospital_details.get('assignedDoctors', []) if hospital_details else []
        
        processed_data = []
        for doctor_id in doctor_ids:
            doctor = mongo.db.users.find_one({'umsId': doctor_id})
            if doctor:
                # Count appointments for this doctor
                appointment_count = mongo.db.appointments.count_documents({
                    'hospitalId': hospital_id,
                    'doctorId': doctor_id,
                    'status': {'$ne': 'deleted'}
                })
                
                processed_data.append({
                    'Doctor ID': doctor_id,
                    'Doctor Name': doctor.get('name', 'Unknown'),
                    'Appointments': appointment_count
                })
    elif report_type == 'Patient Statistics':
        # Get unique patients who have appointments at this hospital
        patient_ids = mongo.db.appointments.distinct('patientId', {'hospitalId': hospital_id})
        
        processed_data = []
        for patient_id in patient_ids:
            patient = mongo.db.users.find_one({'umsId': patient_id})
            if patient:
                # Count appointments for this patient
                appointment_count = mongo.db.appointments.count_documents({
                    'hospitalId': hospital_id,
                    'patientId': patient_id,
                    'status': {'$ne': 'deleted'}
                })
                
                processed_data.append({
                    'Patient ID': patient_id,
                    'Patient Name': patient.get('name', 'Unknown'),
                    'Appointments': appointment_count
                })
    else:  # Full report
        appointments = list(mongo.db.appointments.find(query))
        
        # Process appointments for report
        processed_data = []
        for appointment in appointments:
            patient = mongo.db.users.find_one({'umsId': appointment.get('patientId')})
            doctor = mongo.db.users.find_one({'umsId': appointment.get('doctorId')}) if 'doctorId' in appointment else None
            
            processed_data.append({
                'Date': appointment.get('appointmentDate').strftime('%Y-%m-%d') if 'appointmentDate' in appointment and appointment['appointmentDate'] else 'N/A',
                'Patient': patient['name'] if patient else 'Unknown',
                'Doctor': doctor['name'] if doctor else 'Not Assigned',
                'Status': appointment.get('status', 'Unknown'),
                'Reason': appointment.get('reason', 'N/A')
            })
    
    # Generate the report based on format
    if report_format == 'csv':
        if not processed_data:
            processed_data = [{'No Data': 'No data available for the selected criteria'}]
            
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=processed_data[0].keys())
        writer.writeheader()
        writer.writerows(processed_data)
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename={hospital_data['name'].replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d')}.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    
    elif report_format == 'excel':
        if not processed_data:
            processed_data = [{'No Data': 'No data available for the selected criteria'}]
            
        df = pd.DataFrame(processed_data)
        output = StringIO()
        
        # Create a response
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)
            
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename={hospital_data['name'].replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response
    
    elif report_format == 'pdf':
        # Simple HTML to PDF conversion
        html_content = """
        <html>
        <head>
            <title>Hospital Report</title>
            <style>
                body { font-family: Arial, sans-serif; }
                h1 { color: #2563eb; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
            </style>
        </head>
        <body>
            <h1>""" + hospital_data['name'] + """ Report</h1>
            <p>Generated on: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            <table>
                <thead>
                    <tr>
        """
        
        # Add table headers
        if processed_data:
            for key in processed_data[0].keys():
                html_content += f"<th>{key}</th>"
            
            html_content += """
                    </tr>
                </thead>
                <tbody>
            """
            
            # Add table rows
            for item in processed_data:
                html_content += "<tr>"
                for value in item.values():
                    html_content += f"<td>{value}</td>"
                html_content += "</tr>"
        else:
            html_content += """
                    <th>No Data</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>No data available for the selected criteria</td></tr>
            """
            
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # Convert HTML to PDF
        from weasyprint import HTML
        pdf = HTML(string=html_content).write_pdf()
        
        response = make_response(pdf)
        response.headers["Content-Disposition"] = f"attachment; filename={hospital_data['name'].replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        response.headers["Content-type"] = "application/pdf"
        return response
    
    # Default fallback
    return jsonify({'error': 'Unsupported report format'}), 400

@hospital_bp.route('/download_full_report', methods=['GET'])
@login_required
def download_full_report():
    from flask import make_response
    import csv
    from io import StringIO
    
    hospital_id = session['umsId']
    hospital_data = get_hospital_data()
    
    # Get all appointments
    appointments = list(mongo.db.appointments.find({
        'hospitalId': hospital_id,
        'status': {'$ne': 'deleted'}
    }))
    
    # Process appointments for report
    processed_data = []
    for appointment in appointments:
        patient = mongo.db.users.find_one({'umsId': appointment.get('patientId')})
        doctor = mongo.db.users.find_one({'umsId': appointment.get('doctorId')}) if 'doctorId' in appointment else None
        
        processed_data.append({
            'Date': appointment.get('appointmentDate').strftime('%Y-%m-%d') if 'appointmentDate' in appointment and appointment['appointmentDate'] else 'N/A',
            'Patient': patient['name'] if patient else 'Unknown',
            'Doctor': doctor['name'] if doctor else 'Not Assigned',
            'Status': appointment.get('status', 'Unknown'),
            'Reason': appointment.get('reason', 'N/A')
        })
    
    # Generate CSV report
    if not processed_data:
        processed_data = [{'No Data': 'No data available'}]
        
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=processed_data[0].keys())
    writer.writeheader()
    writer.writerows(processed_data)
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={hospital_data['name'].replace(' ', '_')}_full_report_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-type"] = "text/csv"
    return response