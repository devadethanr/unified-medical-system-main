from flask import Blueprint, render_template, request, jsonify, session, current_app
from flask_login import login_required
from datetime import datetime, timedelta
import json
import logging
import google.generativeai as genai
from google.generativeai import GenerativeModel
import os
from typing import Dict, List, Any
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

dbchat_bp = Blueprint('dbchat', __name__)

class MongoDBHelper:
    def __init__(self, mongo_instance):
        self.mongo = mongo_instance  # Pass mongo instance instead of importing

    def get_collection_info(self, collection_name: str) -> dict:
        """Get collection metadata and sample documents"""
        logger.info(f"Getting collection info for: {collection_name}")
        collection = self.mongo.db[collection_name]
        sample_docs = list(collection.find().limit(2))
        return {
            "collection_name": collection_name,
            "sample_documents": json.loads(json.dumps(sample_docs, default=str)),
            "field_names": list(sample_docs[0].keys()) if sample_docs else []
        }

    def execute_aggregate(self, collection_name: str, pipeline: List[dict]) -> List[dict]:
        """Execute a MongoDB aggregation pipeline"""
        logger.info(f"Executing aggregation on {collection_name}: {pipeline}")
        collection = self.mongo.db[collection_name]
        return list(collection.aggregate(pipeline))

class QueryGenerator:
    def __init__(self):
        self.model = GenerativeModel('gemini-pro')

    def generate_query(self, user_query: str, collection_info: dict) -> dict:
        """Generate MongoDB aggregation pipeline using Gemini"""
        logger.info(f"Generating query for: {user_query}")
        
        prompt = f"""
        You are a MongoDB query generator. Generate an aggregation pipeline based on this request: "{user_query}"
        
        Collection Information:
        Collection Name: {collection_info['collection_name']}
        Available Fields: {collection_info['field_names']}
        Sample Documents: {json.dumps(collection_info['sample_documents'], indent=2)}
        
        Return only a JSON object with these fields:
        1. pipeline: MongoDB aggregation pipeline array
        2. visualization_type: Either 'line', 'bar', or 'pie'
        3. explanation: Brief explanation of what the query does
        
        Format the response as valid JSON without any markdown formatting or code blocks.
        """
        
        response = self.model.generate_content(prompt)
        logger.info(f"Raw Gemini response: {response.text}")
        
        try:
            # Clean up the response text to extract only the JSON part
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove ```
            
            # Clean any remaining whitespace
            response_text = response_text.strip()
            
            logger.info(f"Cleaned response text: {response_text}")
            return json.loads(response_text)
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            # Return a default query if parsing fails
            return {
                "pipeline": [{"$sample": {"size": 5}}],
                "visualization_type": "bar",
                "explanation": "Sorry, I couldn't understand your query. Here's a sample of 5 random documents."
            }

class QuerySystem:
    def __init__(self, mongo_instance):
        self.db_helper = MongoDBHelper(mongo_instance)
        self.query_generator = QueryGenerator()

    def process_query(self, user_query: str, collection_name: str) -> Dict[str, Any]:
        try:
            logger.info(f"Processing query: {user_query} for collection: {collection_name}")
            
            # Get collection information
            collection_info = self.db_helper.get_collection_info(collection_name)
            
            # Generate MongoDB query
            query_info = self.query_generator.generate_query(user_query, collection_info)
            
            # Execute aggregation
            results = self.db_helper.execute_aggregate(collection_name, query_info['pipeline'])
            
            # Format response for visualization
            response = {
                'text': query_info['explanation'],
                'visualization': {
                    'type': query_info['visualization_type'],
                    'data': self._format_chart_data(results)
                }
            }
            
            logger.info(f"Query processed successfully: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'text': f'Error processing query: {str(e)}',
                'visualization': None
            }

    def _format_chart_data(self, results: List[dict]) -> dict:
        """Format MongoDB results for Chart.js"""
        # Extract labels and data from results
        if not results:
            return {'labels': [], 'datasets': [{'data': []}]}
            
        labels = [str(r.get('_id', i)) for i, r in enumerate(results)]
        values = [r.get('value', r.get('count', 0)) for r in results]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Value',
                'data': values,
                'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                'borderColor': 'rgb(54, 162, 235)',
                'tension': 0.1
            }]
        }

# Move query_system initialization to after Blueprint registration
query_system = None

def init_dbchat(mongo_instance):
    """Initialize the query system with mongo instance"""
    global query_system
    query_system = QuerySystem(mongo_instance)

# Add this function for Gemini API health check
def check_gemini_api():
    try:
        model = GenerativeModel('gemini-pro')
        response = model.generate_content("Hello, are you working?")
        logger.info("Gemini API connection successful!")
        return True
    except Exception as e:
        logger.error(f"Gemini API connection failed: {e}")
        return False

def get_admin_data(mongo_instance):
    """Get admin data from the database."""
    return mongo_instance.db.users.find_one({'umsId': session['umsId']})

@dbchat_bp.route('/dbchat', methods=['GET'])
@login_required
def dbchat():
    """Render the database chat interface."""
    from app import mongo  # Import here to avoid circular import
    admin_data = get_admin_data(mongo)
    return render_template('admin/dbchat.html', admin_data=admin_data)

@dbchat_bp.route('/api/dbchat', methods=['POST'])
@login_required
def process_dbchat():
    """Process database chat queries using Gemini and return results."""
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
        
    try:
        # Process query for the patients collection
        result = query_system.process_query(query, 'patients')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in process_dbchat: {e}")
        return jsonify({'error': str(e)}), 500
