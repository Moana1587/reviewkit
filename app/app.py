from flask import Flask, request, jsonify, render_template, current_app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from tools import *
from pdf import generate_pdf_for_location
from dotenv import load_dotenv
import os
import re
import pymysql
import time
from openai import OpenAI, BadRequestError
from tools import get_latest_message


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
    """Remove file citation references and document/file mentions from OpenAI response text"""
    import re
    
    # Remove patterns like 【4:0†source】, 【1:0†source】, etc.
    # This pattern matches 【 followed by any characters and †source】
    cleaned_text = re.sub(r'【[^】]*†source】', '', text)
    
    # Remove patterns like 【4:0†reviews_134_20251020_131556.txt】, etc.
    # This pattern matches 【 followed by any characters and †filename】
    cleaned_text = re.sub(r'【[^】]*†[^】]*】', '', cleaned_text)
    
    # Remove patterns like 【4:0†file】, etc.
    # This pattern matches 【 followed by any characters and †file】
    cleaned_text = re.sub(r'【[^】]*†file】', '', cleaned_text)
    
    # Also remove any remaining citation patterns that might be different
    # Remove patterns like [1], [2], etc. that might be citation numbers
    cleaned_text = re.sub(r'\[\d+\]', '', cleaned_text)
    
    # Replace common document/file references with natural language
    replacements = [
        (r'[Tt]he PDF file contains', 'There are'),
        (r'[Tt]he PDF contains', 'There are'),
        (r'[Tt]he PDF shows', 'The reviews show'),
        (r'[Tt]he PDF indicates', 'The analysis indicates'),
        (r'[Tt]he document contains', 'There are'),
        (r'[Tt]he document shows', 'The reviews show'),
        (r'[Tt]he document indicates', 'The analysis indicates'),
        (r'[Tt]he file contains', 'There are'),
        (r'[Tt]he file shows', 'The reviews show'),
        (r'[Tt]he file indicates', 'The analysis indicates'),
        (r'[Bb]ased on the document', 'Based on the reviews'),
        (r'[Bb]ased on the PDF', 'Based on the reviews'),
        (r'[Bb]ased on the file', 'Based on the reviews'),
        (r'[Aa]ccording to the document', 'According to the reviews'),
        (r'[Aa]ccording to the PDF', 'According to the reviews'),
        (r'[Aa]ccording to the file', 'According to the reviews'),
        (r'[Ii]n the document', 'in the reviews'),
        (r'[Ii]n the PDF', 'in the reviews'),
        (r'[Ii]n the file', 'in the reviews'),
        (r'[Tt]he data shows', 'The reviews show'),
        (r'[Tt]he data indicates', 'The analysis indicates'),
        (r'[Ff]rom the document', 'from the reviews'),
        (r'[Ff]rom the PDF', 'from the reviews'),
        (r'[Ff]rom the file', 'from the reviews'),
    ]
    
    for pattern, replacement in replacements:
        cleaned_text = re.sub(pattern, replacement, cleaned_text)
    
    # Clean up any extra spaces that might be left
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    return cleaned_text.strip()

def create_review_document(company_name, reviews):
    """Create a formatted document from reviews for vector store"""
    if not reviews:
        return f"Company: {company_name}\nNo reviews available."
    
    document = f"Company: {company_name}\n"
    document += f"Total Reviews: {len(reviews)}\n\n"
    
    # Calculate basic statistics
    ratings = [review[1] for review in reviews if review[1] is not None]
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        document += f"Average Rating: {avg_rating:.2f}\n"
        document += f"Rating Distribution:\n"
        for i in range(1, 6):
            count = sum(1 for r in ratings if r == i)
            document += f"  {i} stars: {count} reviews\n"
        document += "\n"
    
    # Add individual reviews
    document += "Individual Reviews:\n"
    document += "=" * 50 + "\n\n"
    
    for i, review in enumerate(reviews, 1):
        display_name, rating, comment, create_time, review_id = review
        
        document += f"Review #{i}:\n"
        document += f"Review ID: {review_id}\n"
        document += f"Author: {display_name}\n"
        document += f"Rating: {rating} stars\n"
        document += f"Date: {create_time}\n"
        document += f"Comment: {comment}\n"
        document += "-" * 30 + "\n\n"
    
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
        assistant_instructions = f"""
        You are a specialized AI assistant for analyzing customer reviews for {company_name}.
        
        CRITICAL INSTRUCTION: You have direct access to {company_name}'s customer review database. You MUST use the file search tool to analyze the reviews.
        
        The review database contains:
        - Customer names and review IDs
        - Star ratings (1-5 stars)
        - Detailed customer comments
        - Review dates and timestamps
        - Overall statistics and rating distributions
        
        Your capabilities include:
        1. **Sentiment Analysis**: Analyze the emotional tone and sentiment of reviews
        2. **Trend Analysis**: Identify patterns over time in customer feedback
        3. **Topic Analysis**: Extract key themes and topics from review content
        4. **Customer Insights**: Provide actionable insights for business improvement
        5. **Statistical Analysis**: Calculate and interpret review metrics
        6. **Recommendation Engine**: Suggest specific improvements based on review analysis
        
        ⚠️ ABSOLUTE RESPONSE RULES - FOLLOW THESE EXACTLY OR YOUR RESPONSE WILL BE REJECTED:
        
        🚫 FORBIDDEN WORDS - NEVER USE THESE:
        - "document" / "documents"
        - "file" / "files" / "PDF" / "text file"
        - "data" (when referring to the review source)
        - "attachment" / "uploaded"
        - "provided information"
        
        🚫 FORBIDDEN PHRASES - NEVER SAY:
        - "The document contains..." ❌
        - "The PDF file contains..." ❌
        - "The PDF shows..." ❌
        - "According to the file..." ❌
        - "Based on the data..." ❌
        - "The file indicates..." ❌
        - "In the document..." ❌
        - "From the document..." ❌
        
        ✅ REQUIRED PHRASES - USE THESE INSTEAD:
        - "There are X reviews..." ✓
        - "The reviews show..." ✓
        - "Based on customer feedback..." ✓
        - "The analysis reveals..." ✓
        - "Customers have mentioned..." ✓
        - "I found X reviews..." ✓
        - "Looking at the reviews..." ✓
        - "Customer feedback indicates..." ✓
        - "The ratings show..." ✓
        
        EXAMPLES OF CORRECT RESPONSES:
        ❌ Wrong: "The PDF file contains a total of 11 reviews."
        ✅ Correct: "There are 11 reviews in total."
        
        ❌ Wrong: "Based on the document, the average rating is 4.5 stars."
        ✅ Correct: "The average rating is 4.5 stars."
        
        ❌ Wrong: "The file shows positive sentiment."
        ✅ Correct: "The reviews show positive sentiment."
        
        OTHER REQUIREMENTS:
        - Provide specific examples from actual reviews when relevant
        - Use concrete numbers and percentages
        - Format dates as d-m-Y h:i:s when referencing specific reviews
        - Highlight both positive and negative feedback patterns
        - Suggest actionable recommendations for management
        - Be concise but comprehensive in your analysis
        - Always base answers on actual review content
        
        Remember: You are a review analyst with direct access to customer feedback. Speak naturally about the reviews themselves, NEVER about documents or files.
        """

        # Create assistant with file search capability
        assistant = create_assistant(client, assistant_name, assistant_description, assistant_instructions)
        
        # Store assistant ID in database
        if not record.assistant_id:
            record.assistant_id = assistant.id
            sqlite_db.session.commit()
        else:
            # Use existing assistant
            assistant.id = record.assistant_id
        
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
        add_message(client, thread_id, user_input, record.file_id)
        
        # Run the assistant
        run_status = run_chat(client, thread_id, assistant.id)
        
        if run_status.status == 'completed':
            # Get the latest message
            latest_message = get_latest_message(client, thread_id)
            if latest_message and latest_message.content:
                response_text = ""
                for content_block in latest_message.content:
                    if hasattr(content_block, 'text') and content_block.text:
                        response_text += content_block.text.value
                
                # Clean up file citation references
                response_text = clean_response_text(response_text)
                
                # Log the conversation
                log_conversation(company, company_name, user_input, response_text)
                
                return jsonify({'response': response_text})
            else:
                error_msg = 'No response generated'
                log_conversation(company, company_name, user_input, error_msg)
                return jsonify({'response': error_msg}), 500
        else:
            error_msg = f'Assistant run failed with status: {run_status.status}'
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
