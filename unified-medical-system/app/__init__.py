from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager

mongo = PyMongo()
login_manager = LoginManager()

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    try:
        mongo.init_app(app)
    except Exception as e:
        print(f"Error initializing Flask-PyMongo: {str(e)}")
    login_manager.init_app(app)
    # login_manager.login_view = 'login'
    login_manager.login_view = 'auth.login'

    from app.routes import admin, patient, doctor, hospital, auth
    app.register_blueprint(auth.auth_bp, url_prefix='/auth')
    app.register_blueprint(admin.admin_bp, url_prefix='/admin')
    app.register_blueprint(patient.patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor.doctor_bp, url_prefix='/doctor')
    app.register_blueprint(hospital.hospital_bp, url_prefix='/hospital')

    return app
