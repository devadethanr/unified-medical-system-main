from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def index():
    return "Admin Dashboard"
