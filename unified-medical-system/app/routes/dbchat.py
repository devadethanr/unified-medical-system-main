from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required
from datetime import datetime, timedelta
import json

dbchat_bp = Blueprint('dbchat', __name__)

def get_admin_data():
    """Get admin data from the database."""
    from app import mongo  # Import mongo here to avoid circular import
    return mongo.db.users.find_one({'umsId': session['umsId']})

def process_natural_language_query(query):
    """Process natural language query and return appropriate database results."""
    from app import mongo  # Import mongo here to avoid circular import
    
    query = query.lower()
    
    try:
        if "patient admissions trend" in query:
            # Get patient admissions over time
            pipeline = [
                {
                    "$group": {
                        "_id": {"$dateToString": {"format": "%Y-%m", "date": "$createdAt"}},
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            results = list(mongo.db.patients.aggregate(pipeline))
            
            return {
                'text': 'Here\'s the patient admissions trend over time:',
                'visualization': {
                    'type': 'chart',
                    'data': {
                        'type': 'line',
                        'data': {
                            'labels': [r['_id'] for r in results],
                            'datasets': [{
                                'label': 'Patient Admissions',
                                'data': [r['count'] for r in results],
                                'borderColor': 'rgb(75, 192, 192)',
                                'tension': 0.1
                            }]
                        }
                    }
                }
            }
            
        elif "hospital occupancy" in query:
            # Get hospital occupancy rates
            pipeline = [
                {
                    "$group": {
                        "_id": "$hospitalId",
                        "occupancy": {"$sum": 1}
                    }
                }
            ]
            results = list(mongo.db.patients.aggregate(pipeline))
            
            return {
                'text': 'Current hospital occupancy rates:',
                'visualization': {
                    'type': 'chart',
                    'data': {
                        'type': 'bar',
                        'data': {
                            'labels': [f'Hospital {i+1}' for i in range(len(results))],
                            'datasets': [{
                                'label': 'Occupancy',
                                'data': [r['occupancy'] for r in results],
                                'backgroundColor': 'rgba(54, 162, 235, 0.5)'
                            }]
                        }
                    }
                }
            }
            
        elif "top 5 doctors" in query:
            # Get top 5 doctors by patient count
            pipeline = [
                {
                    "$group": {
                        "_id": "$doctorId",
                        "patientCount": {"$sum": 1}
                    }
                },
                {"$sort": {"patientCount": -1}},
                {"$limit": 5}
            ]
            results = list(mongo.db.appointments.aggregate(pipeline))
            
            # Get doctor names
            doctor_ids = [r['_id'] for r in results]
            doctors = {d['umsId']: d['name'] for d in mongo.db.users.find(
                {'umsId': {'$in': doctor_ids}}
            )}
            
            return {
                'text': 'Here are the top 5 doctors by patient count:',
                'visualization': {
                    'type': 'chart',
                    'data': {
                        'type': 'bar',
                        'data': {
                            'labels': [doctors.get(r['_id'], 'Unknown') for r in results],
                            'datasets': [{
                                'label': 'Patient Count',
                                'data': [r['patientCount'] for r in results],
                                'backgroundColor': 'rgba(153, 102, 255, 0.5)'
                            }]
                        }
                    }
                }
            }
        
        else:
            return {
                'text': 'I\'m not sure how to process that query. Try asking about patient admissions trends, hospital occupancy rates, or top doctors.',
                'visualization': None
            }
            
    except Exception as e:
        return {
            'text': f'Error processing query: {str(e)}',
            'visualization': None
        }

@dbchat_bp.route('/dbchat', methods=['GET'])
@login_required
def dbchat():
    """Render the database chat interface."""
    admin_data = get_admin_data()
    return render_template('admin/dbchat.html', admin_data=admin_data)

@dbchat_bp.route('/api/dbchat', methods=['POST'])
@login_required
def process_dbchat():
    """Process database chat queries and return results."""
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
        
    try:
        result = process_natural_language_query(query)
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to process query'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
