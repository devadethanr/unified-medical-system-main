import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required
from app import mongo
from app.models import User
from datetime import datetime

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
    return render_template('admin/profile.html', admin_data=admin_data, global_admin_data=global_admin_data)

#admin update and edit profile
@admin_bp.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        admin_data = mongo.db.users.find_one({'umsId': session['umsId']})
    return render_template('admin/profile-edit.html', admin_data=admin_data, global_admin_data=global_admin_data)