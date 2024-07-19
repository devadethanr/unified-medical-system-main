import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required
from app import mongo
from app.models import User
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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
    admin_data = mongo.db.users.find_one({'umsId': session['umsId']})
    print(admin_data) #for debugging
    return render_template('admin/dashboard.html', admin_data=admin_data, global_admin_data=global_admin_data)

#admin profile
@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    admin_data = mongo.db.users.find_one({'umsId': session['umsId']})
    admin_data['phoneNumber'] = admin_data.get('phoneNumber', [None])[0]
    if request.method == 'POST':
         if request.form.get('form_type') == 'update_profile':
            return update_profile()
    return render_template('admin/profile.html', admin_data=admin_data, global_admin_data=global_admin_data)

def update_profile():
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