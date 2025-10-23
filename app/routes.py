"""
API routes for ReviewKit application
"""

import json
from flask import request, jsonify, Response, stream_with_context, current_app
from models import db, OpenAICreds
from db_utils import get_mysql_connection, fetch_reviews_for_company
from daily_limits import (
    reset_daily_usage_if_needed, 
    check_daily_limit, 
    increment_daily_usage,
    get_usage_status,
    update_user_plan
)
from openai_service import OpenAIService
from review_processor import log_conversation

def register_routes(app):
    """Register all API routes with the Flask app"""
    
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    @app.route('/reset-company/<company_id>', methods=['POST'])
    def reset_company(company_id):
        """Reset assistant and thread for a company (useful for troubleshooting)"""
        try:
            record = OpenAICreds.query.filter_by(company_id=company_id).first()
            if record:
                old_assistant = record.assistant_id
                old_thread = record.thread_id
                
                # Clear the assistant and thread
                record.assistant_id = None
                record.thread_id = None
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Reset complete for company {company_id}',
                    'old_assistant_id': old_assistant,
                    'old_thread_id': old_thread
                })
            else:
                return jsonify({
                    'success': True,
                    'message': f'No records found for company {company_id} (nothing to reset)'
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/usage-status/<company_id>', methods=['GET'])
    def get_usage_status_endpoint(company_id):
        """Get current usage status for a company"""
        try:
            status = get_usage_status(company_id)
            return jsonify(status)
        except Exception as e:
            return jsonify({
                'error': str(e)
            }), 500

    @app.route('/update-plan/<company_id>', methods=['POST'])
    def update_user_plan_endpoint(company_id):
        """Update user plan for a company"""
        try:
            data = request.get_json()
            plan_name = data.get('plan_name', 'free')
            daily_limit = data.get('daily_limit', 10)
            
            result = update_user_plan(company_id, plan_name, daily_limit)
            return jsonify(result)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/chat-stream', methods=['POST'])
    def chat_stream():
        """Streaming chat endpoint for real-time responses"""
        company = request.args.get('company')
        user_input = request.json.get('message')

        if not company:
            return jsonify({'error': 'No company parameter provided'}), 400

        # Check daily limit before processing
        reset_daily_usage_if_needed(company)
        can_proceed, current_usage, daily_limit = check_daily_limit(company)
        
        if not can_proceed:
            return jsonify({
                'error': f"You've reached your daily limit of {daily_limit} API calls. Please upgrade or try again tomorrow."
            }), 429

        openai_service = OpenAIService()
        if not openai_service.client:
            return jsonify({'error': 'OpenAI API key not configured'}), 500

        conn = None
        company_name = None

        def generate():
            nonlocal conn, company_name
            try:
                # Connect to MySQL and fetch reviews
                conn = get_mysql_connection()
                company_name, reviews = fetch_reviews_for_company(conn, company)
                
                if not company_name:
                    yield f"data: {json.dumps({'error': 'Company not found'})}\n\n"
                    return
                
                if not reviews:
                    yield f"data: {json.dumps({'error': f'No reviews found for {company_name}'})}\n\n"
                    return

                # Increment daily usage count
                increment_daily_usage(company)

                # Process the chat request
                for chunk in openai_service.run_chat_streaming(company, user_input, company_name, reviews):
                    yield chunk

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                if conn:
                    conn.close()

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    @app.route('/chat', methods=['POST'])
    def check_company():
        """Regular chat endpoint"""
        company = request.args.get('company')
        user_input = request.json.get('message')

        if not company:
            return jsonify({'error': 'No company parameter provided'}), 400

        # Check daily limit before processing
        reset_daily_usage_if_needed(company)
        can_proceed, current_usage, daily_limit = check_daily_limit(company)
        
        if not can_proceed:
            return jsonify({
                'response': f"You've reached your daily limit of {daily_limit} API calls. Please upgrade or try again tomorrow."
            }), 429

        openai_service = OpenAIService()
        if not openai_service.client:
            return jsonify({'error': 'OpenAI API key not configured'}), 500

        conn = None
        company_name = None

        try:
            # Connect to MySQL and fetch reviews
            conn = get_mysql_connection()
            company_name, reviews = fetch_reviews_for_company(conn, company)
            
            if not company_name:
                error_msg = 'Company not found'
                log_conversation(company, 'Unknown Company', user_input, error_msg)
                return jsonify({'response': error_msg}), 200
            
            if not reviews:
                error_msg = f'No reviews found for {company_name}'
                log_conversation(company, company_name, user_input, error_msg)
                return jsonify({'response': error_msg}), 200

            # Increment daily usage count
            increment_daily_usage(company)

            # Process the chat request
            response, error = openai_service.run_chat_regular(company, user_input, company_name, reviews)
            
            if error:
                return jsonify({'response': error}), 500
            else:
                return jsonify({'response': response})

        except Exception as e:
            error_msg = f'Error: {str(e)}'
            log_conversation(company, company_name or 'Unknown', user_input, error_msg)
            return jsonify({'response': error_msg}), 500

        finally:
            if conn:
                conn.close()
