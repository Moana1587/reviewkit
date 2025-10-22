from flask import Flask, request, jsonify, render_template, current_app, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from tools import *
from pdf import generate_pdf_for_location
from dotenv import load_dotenv
import os
import re
import pymysql
import time
import json
from openai import OpenAI, BadRequestError
from tools import get_latest_message, run_chat_streaming


app = Flask(__name__)
load_dotenv()

open_ai_key = os.getenv('OPEN_AI_KEY')

# SQLite configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
sqlite_db = SQLAlchemy(app)

# MySQL configuration
mysql_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('HOST'),
    'database': os.getenv('DB_NAME')
}

def get_mysql_connection():
    return pymysql.connect(
        user=mysql_config['user'],
        password=mysql_config['password'],
        host=mysql_config['host'],
        database=mysql_config['database']
    )

def fetch_reviews_for_company(conn, company_id):
    """Fetch all reviews for a company and format them for vector store"""
    with conn.cursor() as cursor:
        # Get company name
        cursor.execute("SELECT location_title FROM tbl_location WHERE location_id = %s", (company_id,))
        company_result = cursor.fetchone()
        if not company_result:
            return None, None
        
        company_name = company_result[0]
        
        # Get all reviews for the company
        cursor.execute("""
            SELECT displayName, starRating_number, comment, createTime, reviewId
            FROM tbl_location_review 
            WHERE location_id = %s AND (is_deleted = 0 OR is_deleted IS NULL)
            ORDER BY createTime DESC
        """, (company_id,))
        
        reviews = cursor.fetchall()
        return company_name, reviews

def clean_response_text(text):
    """Remove ONLY citation references like 【4:0†source】 from text - keep everything else unchanged"""
    import re
    
    # Remove patterns like 【4:0†source】, 【1:0†source】, etc.
    cleaned_text = re.sub(r'【[^】]*†source】', '', text)
    
    # Remove patterns like 【4:0†reviews_134_20251020_131556.txt】, etc.
    cleaned_text = re.sub(r'【[^】]*†[^】]*】', '', cleaned_text)
    
    # Remove patterns like 【4:0†file】, etc.
    cleaned_text = re.sub(r'【[^】]*†file】', '', cleaned_text)
    
    # Remove patterns like [1], [2], etc. that might be citation numbers
    cleaned_text = re.sub(r'\[\d+\]', '', cleaned_text)
    
    # Return the text with ONLY citations removed - no other changes
    return cleaned_text

def create_review_document(company_name, reviews, max_reviews=500):
    """Create a formatted document from reviews for vector store
    
    Args:
        company_name: Name of the company
        reviews: List of reviews (already sorted by date DESC)
        max_reviews: Maximum number of reviews to include (for speed)
    """
    if not reviews:
        return f"Company: {company_name}\nNo reviews available."
    
    # Limit reviews for speed (use most recent ones since they're already sorted DESC)
    total_reviews = len(reviews)
    reviews_to_use = reviews[:max_reviews] if len(reviews) > max_reviews else reviews
    
    # Calculate statistics from limited set
    ratings = [review[1] for review in reviews_to_use if review[1] is not None]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    # Create compact document (faster file search)
    document = f"Company: {company_name}\n"
    if total_reviews > max_reviews:
        document += f"Showing {len(reviews_to_use)} most recent of {total_reviews} reviews | Avg: {avg_rating:.1f} stars\n\n"
    else:
        document += f"Total: {len(reviews_to_use)} reviews | Avg: {avg_rating:.1f} stars\n\n"
    
    # Add individual reviews (compact format for speed)
    for review in reviews_to_use:
        display_name, rating, comment, create_time, review_id = review
        # Compact format: ID|Name|Rating|Date|Comment
        document += f"{review_id}|{display_name}|{rating}★|{create_time}|{comment}\n"
    
    return document

def create_text_file_for_vector_store(document, company_id):
    """Create a text file from the review document for vector store"""
    filename = f"storage/reviews_{company_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Ensure storage directory exists
    os.makedirs('storage', exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(document)
    
    return filename

def create_pdf_file_for_vector_store(document, company_id):
    """Create a PDF file from the review document for vector store"""
    filename = f"storage/reviews_{company_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Ensure storage directory exists
    os.makedirs('storage', exist_ok=True)
    
    try:
        # Try to use the existing PDF generation function first
        pdf_path = generate_pdf_for_location(company_id)
        # Return the actual filename created by the function
        return pdf_path
    except Exception as e:
        print(f"Error with existing PDF function: {e}")
        # Fallback: create a simple PDF using reportlab
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Split document into paragraphs
        lines = document.split('\n')
        for line in lines:
            if line.strip():
                if line.startswith('Company:') or line.startswith('Total Reviews:') or line.startswith('Average Rating:'):
                    story.append(Paragraph(line, styles['Heading2']))
                elif line.startswith('Review #'):
                    story.append(Paragraph(line, styles['Heading3']))
                elif line.startswith('=') or line.startswith('-'):
                    story.append(Spacer(1, 12))
                else:
                    story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 6))
        
        doc.build(story)
        return filename

def setup_file_for_company(client, company_id, company_name, reviews):
    """Set up PDF file for a company with their reviews"""
    try:
        # Create review document
        document = create_review_document(company_name, reviews)
        
        # Create text file (temporarily using text instead of PDF)
        text_file = create_text_file_for_vector_store(document, company_id)
        
        # Upload text file to OpenAI
        with open(text_file, 'rb') as f:
            uploaded_file = client.files.create(
                file=f,
                purpose="assistants"
            )
        
        print(f"Text file created and uploaded: {text_file} -> {uploaded_file.id}")
        return uploaded_file
        
    except Exception as e:
        print(f"Error setting up PDF file: {e}")
        return None

def log_conversation(company_id, company_name, question, answer):
    """Log question and answer to a text file"""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = 'logs'
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create a log file per company with date
        current_date = datetime.now().strftime('%Y%m%d')
        log_filename = f"{logs_dir}/chat_log_{company_id}_{current_date}.txt"
        
        # Prepare log entry
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        separator = "=" * 80
        
        # Detect if this is an error message
        is_error = any(keyword in answer.lower() for keyword in [
            'error', 'failed', 'not found', 'no response', 'no reviews found'
        ])
        
        log_entry = f"\n{separator}\n"
        log_entry += f"Company: {company_name} (ID: {company_id})\n"
        log_entry += f"Timestamp: {timestamp}\n"
        if is_error:
            log_entry += f"Status: ⚠️ ERROR\n"
        else:
            log_entry += f"Status: ✓ SUCCESS\n"
        log_entry += f"{separator}\n\n"
        log_entry += f"QUESTION:\n{question}\n\n"
        log_entry += f"ANSWER:\n{answer}\n\n"
        log_entry += f"{separator}\n"
        
        # Append to log file
        with open(log_filename, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"Conversation logged to: {log_filename}")
        
    except Exception as e:
        print(f"Error logging conversation: {e}")


# Define the SQLite model
class OpenAICreds(sqlite_db.Model):
    __tablename__ = 'openai_creds'
    id = sqlite_db.Column(sqlite_db.Integer, primary_key=True)
    company_id = sqlite_db.Column(sqlite_db.String(80), unique=True, nullable=False)
    updated_date = sqlite_db.Column(sqlite_db.DateTime, nullable=True)
    assistant_id = sqlite_db.Column(sqlite_db.String(80), nullable=True)
    file_id = sqlite_db.Column(sqlite_db.String(80), nullable=True)
    vector_id = sqlite_db.Column(sqlite_db.String(80), nullable=True)
    thread_id = sqlite_db.Column(sqlite_db.String(80), nullable=True)

def check_and_create_table(table_name):
    inspector = sqlite_db.inspect(sqlite_db.engine)
    if not inspector.has_table(table_name):
        print(f"Table '{table_name}' does not exist. Creating table.")
        sqlite_db.create_all()
    else:
        print(f"Table '{table_name}' already exists.")

@app.before_request
def initialize_database():
    with current_app.app_context():
        check_and_create_table(OpenAICreds.__tablename__)

@app.route('/')
def index():
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
            sqlite_db.session.commit()
            
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

@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint for real-time responses"""
    company = request.args.get('company')
    user_input = request.json.get('message')

    if not company:
        return jsonify({'error': 'No company parameter provided'}), 400

    if not open_ai_key:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    client = OpenAI(api_key=open_ai_key)
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

            # Check if we have existing file for this company
            record = OpenAICreds.query.filter_by(company_id=company).first()
            
            if not record or not record.file_id:
                # Create new file
                uploaded_file = setup_file_for_company(client, company, company_name, reviews)
                
                if not uploaded_file:
                    yield f"data: {json.dumps({'error': 'Failed to create file'})}\n\n"
                    return
                
                # Create or update record
                if not record:
                    record = OpenAICreds(company_id=company)
                    sqlite_db.session.add(record)
                
                record.file_id = uploaded_file.id
                record.updated_date = datetime.utcnow()
                sqlite_db.session.commit()

            # Create assistant with vector store
            assistant_name = f"Review Analyst for {company_name}"
            assistant_description = f"AI assistant specialized in analyzing customer reviews for {company_name}"
            assistant_instructions = f"""You are a review analyst for {company_name}. Use file search to analyze customer reviews.

            GREETINGS: Respond warmly (e.g., "Hi! How can I help you with {company_name}'s reviews today?")

            LANGUAGE RULES:
            ✓ Say: "The reviews show...", "Customers mentioned...", "I found X reviews..."
            ✗ Never say: "document", "file", "PDF", "data", "attachment"

            FORMAT RULES:
            - List reviews on separate lines with blank lines between them
            - Example: "1. **Name** - X stars on DD-MM-YYYY:\n   \"Comment...\"\n\n2. **Name**..."
            - Be concise but specific
            - Include reviewer names, ratings, dates from the data

            GENERAL QUESTIONS:
            For questions NOT related to reviews (like "What color is the sky?", "How are you?", etc.), respond politely:
            "Sorry, I can't answer questions not related to reviews. Feel free to ask about reviews, ratings, or customer feedback for {company_name}!"

            Search the file to answer all questions about reviews, ratings, trends, and feedback."""

            # Create or reuse assistant
            if not record.assistant_id:
                assistant = create_assistant(client, assistant_name, assistant_description, assistant_instructions)
                record.assistant_id = assistant.id
                sqlite_db.session.commit()
            else:
                try:
                    assistant = get_assistant(client, record.assistant_id)
                except Exception as e:
                    assistant = create_assistant(client, assistant_name, assistant_description, assistant_instructions)
                    record.assistant_id = assistant.id
                    sqlite_db.session.commit()
            
            # Reuse existing thread to maintain conversation history
            if not record.thread_id:
                thread_id = start_new_chat(client)
                record.thread_id = thread_id
                sqlite_db.session.commit()
            else:
                thread_id = record.thread_id

            # Add user message to thread with file attachment
            add_message(client, thread_id, user_input, record.file_id)
            
            # Stream the response
            full_response = ""
            for chunk in run_chat_streaming(client, thread_id, assistant.id):
                if chunk.startswith('[DONE]'):
                    # Clean the final response and send completion
                    cleaned_response = clean_response_text(full_response)
                    log_conversation(company, company_name, user_input, cleaned_response)
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break
                elif chunk.startswith('[ERROR'):
                    yield f"data: {json.dumps({'error': chunk})}\n\n"
                    break
                else:
                    # Send chunk to client
                    full_response += chunk
                    # Clean chunk before sending
                    cleaned_chunk = clean_response_text(chunk)
                    if cleaned_chunk:  # Only send if chunk has content after cleaning
                        yield f"data: {json.dumps({'chunk': cleaned_chunk})}\n\n"

        except Exception as e:
            print(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if conn:
                conn.close()

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/chat', methods=['POST'])
def check_company():
    company = request.args.get('company')
    user_input = request.json.get('message')

    if not company:
        return jsonify({'error': 'No company parameter provided'}), 400

    if not open_ai_key:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    client = OpenAI(api_key=open_ai_key)
    conn = None
    company_name = None  # Initialize company_name for error handling

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

        # Check if we have existing file for this company
        record = OpenAICreds.query.filter_by(company_id=company).first()
        
        if not record or not record.file_id:
            # Create new file
            print(f"Creating file for {company_name}...")
            uploaded_file = setup_file_for_company(client, company, company_name, reviews)
            
            if not uploaded_file:
                error_msg = 'Failed to create file'
                log_conversation(company, company_name, user_input, error_msg)
                return jsonify({'response': error_msg}), 500
            
            # Create or update record
            if not record:
                record = OpenAICreds(company_id=company)
                sqlite_db.session.add(record)
            
            record.file_id = uploaded_file.id
            record.updated_date = datetime.utcnow()
            sqlite_db.session.commit()
            
            print(f"File created: {uploaded_file.id}")
        else:
            # Use existing file
            print(f"Using existing file: {record.file_id}")
            uploaded_file_id = record.file_id

        # Create assistant with vector store
        assistant_name = f"Review Analyst for {company_name}"
        assistant_description = f"AI assistant specialized in analyzing customer reviews for {company_name}"
        assistant_instructions = f"""You are a review analyst for {company_name}. Use file search to analyze customer reviews.

        GREETINGS: Respond warmly (e.g., "Hi! How can I help you with {company_name}'s reviews today?")

        LANGUAGE RULES:
        ✓ Say: "The reviews show...", "Customers mentioned...", "I found X reviews..."
        ✗ Never say: "document", "file", "PDF", "data", "attachment"

        FORMAT RULES:
        - List reviews on separate lines with blank lines between them
        - Example: "1. **Name** - X stars on DD-MM-YYYY:\n   \"Comment...\"\n\n2. **Name**..."
        - Be concise but specific
        - Include reviewer names, ratings, dates from the data

        GENERAL QUESTIONS:
        For questions NOT related to reviews (like "What color is the sky?", "How are you?", etc.), respond politely:
        "Sorry, I can't answer questions not related to reviews. Feel free to ask about reviews, ratings, or customer feedback for {company_name}!"

        Search the file to answer all questions about reviews, ratings, trends, and feedback."""

        # Create or reuse assistant
        if not record.assistant_id:
            # Create new assistant only if one doesn't exist
            print(f"Creating new assistant for {company_name}...")
            assistant = create_assistant(client, assistant_name, assistant_description, assistant_instructions)
            record.assistant_id = assistant.id
            sqlite_db.session.commit()
            print(f"Assistant created: {assistant.id}")
        else:
            # Reuse existing assistant
            print(f"Reusing existing assistant: {record.assistant_id}")
            try:
                assistant = get_assistant(client, record.assistant_id)
                print(f"✓ Successfully retrieved assistant {record.assistant_id}")
            except Exception as e:
                print(f"✗ Failed to retrieve assistant {record.assistant_id}: {e}")
                print(f"Creating new assistant...")
                assistant = create_assistant(client, assistant_name, assistant_description, assistant_instructions)
                record.assistant_id = assistant.id
                sqlite_db.session.commit()
                print(f"New assistant created: {assistant.id}")
        
        # Reuse existing thread to maintain conversation history
        if not record.thread_id:
            # Create new thread only if one doesn't exist
            thread_id = start_new_chat(client)
            record.thread_id = thread_id
            sqlite_db.session.commit()
            print(f"Created new thread: {thread_id}")
        else:
            # Reuse existing thread to maintain context
            thread_id = record.thread_id
            print(f"Reusing existing thread: {thread_id}")

        # Add user message to thread with file attachment
        print(f"Adding message to thread {thread_id} with file {record.file_id}")
        try:
            add_message(client, thread_id, user_input, record.file_id)
            print(f"✓ Message added successfully")
        except Exception as e:
            print(f"✗ Error adding message: {e}")
            raise
        
        # Run the assistant
        print(f"Running assistant {assistant.id} on thread {thread_id}")
        run_status = run_chat(client, thread_id, assistant.id)
        print(f"Run completed with status: {run_status.status}")
        
        if run_status.status == 'completed':
            # Get the latest message
            latest_message = get_latest_message(client, thread_id)
            if latest_message and latest_message.content:
                # Extract raw response from OpenAI
                raw_response = ""
                for content_block in latest_message.content:
                    if hasattr(content_block, 'text') and content_block.text:
                        raw_response += content_block.text.value
                
                # Print raw response for debugging
                print("\n" + "="*80)
                print("RAW AI RESPONSE:")
                print("="*80)
                print(raw_response)
                print("="*80 + "\n")
                
                # Clean up file citation references
                cleaned_response = clean_response_text(raw_response)
                
                # Print cleaned response
                print("CLEANED RESPONSE:")
                print("="*80)
                print(cleaned_response)
                print("="*80 + "\n")
                
                # Log the conversation
                log_conversation(company, company_name, user_input, cleaned_response)
                
                # Return both raw and cleaned responses
                return jsonify({
                    'response': cleaned_response
                })
            else:
                error_msg = 'No response generated'
                log_conversation(company, company_name, user_input, error_msg)
                return jsonify({'response': error_msg}), 500
        else:
            # Build detailed error message
            error_msg = f'Assistant run failed with status: {run_status.status}'
            
            # Add specific error details if available
            if hasattr(run_status, 'last_error') and run_status.last_error:
                error_code = getattr(run_status.last_error, 'code', 'unknown')
                error_message = getattr(run_status.last_error, 'message', 'No details available')
                error_msg += f'\n\nError Details:\n{error_code}: {error_message}'
                
                print(f"✗ Assistant Run Failed:")
                print(f"   Status: {run_status.status}")
                print(f"   Error Code: {error_code}")
                print(f"   Error Message: {error_message}")
                
                # Add helpful suggestions based on error type
                if 'rate_limit' in error_code.lower():
                    error_msg += '\n\nSuggestion: Please try again in a few moments (rate limit exceeded).'
                elif 'token' in error_code.lower() or 'length' in error_code.lower():
                    error_msg += '\n\nSuggestion: Try asking a more specific question (message too long).'
                elif 'server' in error_code.lower() or 'internal' in error_code.lower():
                    error_msg += '\n\nSuggestion: OpenAI service may be experiencing issues. Please try again in a moment.'
                elif 'invalid' in error_code.lower():
                    error_msg += '\n\nSuggestion: There may be an issue with the assistant configuration. Please contact support.'
            else:
                error_msg += '\n\nThis is usually a temporary issue. Please try your question again.'
                print(f"✗ Assistant Run Failed: {run_status.status} (no error details available)")
            
            log_conversation(company, company_name, user_input, error_msg)
            return jsonify({'response': error_msg}), 500

    except BadRequestError as e:
        print(f"OpenAI BadRequestError: {e}")
        error_msg = f'OpenAI API error: {str(e)}'
        log_conversation(company, company_name or 'Unknown', user_input, error_msg)
        return jsonify({'response': error_msg}), 400

    except Exception as e:
        print(f"An error occurred: {e}")
        error_msg = f'Error: {str(e)}'
        log_conversation(company, company_name or 'Unknown', user_input, error_msg)
        return jsonify({'response': error_msg}), 500

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    import sys
    
    with app.app_context():
        sqlite_db.create_all()  # create tables if they don't exist
    
    # Check if running with --host and --port arguments for public access
    host = '127.0.0.1'  # Default to localhost
    port = 8000
    debug = True
    
    if '--host' in sys.argv:
        host_idx = sys.argv.index('--host')
        if host_idx + 1 < len(sys.argv):
            host = sys.argv[host_idx + 1]
            debug = False  # Disable debug in production
    
    if '--port' in sys.argv:
        port_idx = sys.argv.index('--port')
        if port_idx + 1 < len(sys.argv):
            port = int(sys.argv[port_idx + 1])
    
    print(f"\n{'='*60}")
    print(f"  ReviewKit Server Starting")
    print(f"{'='*60}")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Debug: {debug}")
    print(f"  Access at: http://{host if host != '0.0.0.0' else 'YOUR_SERVER_IP'}:{port}")
    print(f"{'='*60}\n")
    
    app.run(debug=debug, host=host, port=port, use_reloader=False, threaded=True)
