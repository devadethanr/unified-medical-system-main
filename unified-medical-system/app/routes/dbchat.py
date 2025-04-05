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
        self.model = GenerativeModel('gemini-2.0-flash')

    def generate_query(self, user_query: str, collection_info: dict) -> dict:
        # Handle visualization requests directly if keywords are present
        if any(word in user_query.lower() for word in ['graph', 'chart', 'visualize', 'plot', 'bargraph']):
            if 'month' in user_query.lower() and ('patient' in user_query.lower() or 'createdAt' in user_query.lower()):
                return {
                    "type": "data",
                    "pipeline": [
                        {
                            "$group": {
                                "_id": {"$month": "$createdAt"},
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"_id": 1}}
                    ],
                    "visualization_type": "bar",
                    "explanation": "Monthly distribution of patients based on creation date"
                }
        
        # Original visualization check logic
        viz_prompt = f"""Analyze if this query needs visualization: "{user_query}"
        Return only valid JSON in this exact format:
        {{"is_visualization": true/false, "chart_type": "bar", "metrics": ["count"], "aggregation_type": "time"}}"""
        
        try:
            viz_response = self.model.generate_content(viz_prompt)
            viz_text = viz_response.text.strip()
            
            # Remove any markdown formatting
            if '```' in viz_text:
                viz_text = viz_text.split('```')[1]
                if viz_text.startswith('json'):
                    viz_text = viz_text[4:]
                viz_text = viz_text.strip()
            
            viz_info = json.loads(viz_text)
            
            if viz_info["is_visualization"]:
                # Generate appropriate aggregation pipeline based on visualization needs
                agg_prompt = f"""
                Create MongoDB aggregation pipeline for:
                Chart Type: {viz_info['chart_type']}
                Metrics: {viz_info['metrics']}
                Aggregation: {viz_info['aggregation_type']}
                
                Collection Fields: {collection_info['field_names']}
                
                Return only valid JSON with:
                {{
                    "pipeline": [aggregation stages],
                    "visualization_type": "{viz_info['chart_type']}",
                    "explanation": "brief explanation"
                }}"""
                
                response = self.model.generate_content(agg_prompt)
                query_info = json.loads(response.text)
                
                return {
                    "type": "data",
                    "pipeline": query_info["pipeline"],
                    "visualization_type": query_info["visualization_type"],
                    "explanation": query_info["explanation"]
                }
            
            # Handle non-visualization queries as before
            # First, determine if this is a general chat question or a data query
            chat_prompt = f"""Determine if this is a general chat question or a data query: "{user_query}"
            Return only a JSON object with:
            1. type: Either 'chat' or 'data'
            2. requires_viz: boolean (true if visualization would be helpful)
            
            Format as valid JSON."""
            
            try:
                chat_response = self.model.generate_content(chat_prompt)
                chat_text = chat_response.text.strip()
                # Clean up the response if it contains markdown formatting
                if chat_text.startswith('```'):
                    chat_text = chat_text.split('```')[1]
                    if chat_text.startswith('json'):
                        chat_text = chat_text[4:].strip()
                
                query_type = json.loads(chat_text)
                
                if query_type['type'] == 'chat':
                    # Handle general chat questions
                    chat_prompt = f"""You are a helpful database assistant. 
                    Respond to this general question: "{user_query}"
                    Keep the response friendly and concise."""
                    
                    response = self.model.generate_content(chat_prompt)
                    return {
                        "type": "chat",
                        "response": response.text.strip(),
                        "visualization": None
                    }
                
                # For data queries, generate the appropriate MongoDB query
                prompt = f"""
                You are a MongoDB query generator. Generate an aggregation pipeline based on this request: "{user_query}"
                
                Collection Information:
                Collection Name: {collection_info['collection_name']}
                Available Fields: {collection_info['field_names']}
                Sample Documents: {json.dumps(collection_info['sample_documents'], indent=2)}
                
                Return only a JSON object with these fields:
                1. pipeline: MongoDB aggregation pipeline array
                2. visualization_type: Either 'table', 'line', 'bar', or 'pie' (use 'table' if no visualization needed)
                3. explanation: Brief explanation of what the query does
                
                Format the response as valid JSON without markdown formatting."""
                
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Clean up the response if it contains markdown formatting
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:].strip()
                
                query_info = json.loads(response_text)
                return {
                    "type": "data",
                    **query_info
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                # Fallback for chat messages
                return {
                    "type": "chat",
                    "response": "Hello! I'm your database assistant. How can I help you today?",
                    "visualization": None
                }
            except Exception as e:
                logger.error(f"Error in generate_query: {e}")
                return {
                    "type": "data",
                    "pipeline": [{"$sample": {"size": 5}}],
                    "visualization_type": "table",
                    "explanation": "Sorry, I couldn't understand your query. Here's a sample of 5 random documents."
                }
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in visualization check: {e}")
            # Default to chat response
            return {
                "type": "chat",
                "response": "I understand you're looking for insights from the data. Could you please rephrase your question?",
                "visualization": None
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
            
            # Generate response
            query_info = self.query_generator.generate_query(user_query, collection_info)
            
            if query_info['type'] == 'chat':
                return {
                    'type': 'chat',
                    'text': query_info['response'],
                    'visualization': None
                }
            
            # Execute aggregation for data queries
            results = self.db_helper.execute_aggregate(collection_name, query_info['pipeline'])
            
            # Format response
            response = {
                'type': 'data',
                'text': query_info['explanation'],
                'visualization': {
                    'type': query_info['visualization_type'],
                    'data': self._format_visualization_data(results, query_info['visualization_type'])
                }
            }
            
            logger.info(f"Query processed successfully: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'type': 'error',
                'text': f'Error processing query: {str(e)}',
                'visualization': None
            }

    def _format_visualization_data(self, results: List[dict], viz_type: str) -> dict:
        """Format MongoDB results for visualization"""
        if not results:
            return {'labels': [], 'datasets': [{'data': []}]}
        
        if viz_type == 'table':
            # Return formatted table data
            return {
                'headers': list(results[0].keys()),
                'rows': [[str(v) for v in d.values()] for d in results]
            }
            
        # For charts (line, bar, pie)
        labels = [str(r.get('_id', i)) for i, r in enumerate(results)]
        values = [r.get('value', r.get('count', 0)) for r in results]
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Value',
                'data': values,
                'backgroundColor': [
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(255, 206, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
                ],
                'borderColor': [
                    'rgb(54, 162, 235)',
                    'rgb(255, 99, 132)',
                    'rgb(255, 206, 86)',
                    'rgb(75, 192, 192)',
                    'rgb(153, 102, 255)'
                ],
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
        model = GenerativeModel('gemini-2.0-flash')
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
