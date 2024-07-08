from flask import Blueprint

hospital_bp = Blueprint('hospital', __name__)

@hospital_bp.route('/')
def index():
    return "Hospital Dashboard"
