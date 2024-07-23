import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for
from flask_pymongo import PyMongo
from flask_login import LoginManager
import random
from authlib.integrations.flask_client import OAuth
from flask_session import Session
from flask_mail import Mail

mongo = PyMongo()
login_manager = LoginManager()
oauth = OAuth()
mail = Mail()

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    try:
        mongo.init_app(app)
    except Exception as e:
        print(f"Error initializing Flask-PyMongo: {str(e)}")
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    #session management and storage
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'  # Directory for storing session files
    Session(app)
    
    #mail client configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'devadethanr2025@mca.ajce.in'
    app.config['MAIL_PASSWORD'] = 'MUMUbubu@2024'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    Mail(app)
    
    # Configure Google OAuth
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        refresh_token_url=None,
        redirect_uri='http://127.0.0.1:5000/auth/google_authorized',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    oauth.init_app(app)
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error/500.html'), 500

    from app.routes import admin, patient, doctor, hospital, auth
    app.register_blueprint(auth.auth_bp, url_prefix='/auth')
    app.register_blueprint(admin.admin_bp, url_prefix='/admin')
    app.register_blueprint(patient.patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor.doctor_bp, url_prefix='/doctor')
    app.register_blueprint(hospital.hospital_bp, url_prefix='/hospital')

    return app
