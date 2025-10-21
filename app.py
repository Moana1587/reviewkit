from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from tools import *
from pdf import generate_pdf_for_location
from dotenv import load_dotenv
import os
import re
import pymysql
from openai import OpenAI, BadRequestError

app = Flask(__name__)

from flask import Flask, request, jsonify, current_app, render_template
load_dotenv()

open_ai_key = os.getenv('OPEN_AI_KEY')

# SQLite configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
sqlite_db = SQLAlchemy(app)

# MySQL configuration (replace placeholders with actual values)
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

    client = OpenAI(api_key=open_ai_key)

    try:
        # Query the MySQL database to get the location_title
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT location_title FROM tbl_location WHERE location_id = %s", (company,))
            result = cursor.fetchone()
            if result:
                company_name = result[0]
            else:
                return jsonify({'response': 'Company not found'}), 200

        # Define these variables with appropriate values
        name = "Assistant for company " + company_name
        print(name)
        description = "Assistant for company " + company_name
        instructions = f"""
        You are a data analytics specialist. You have a file with information about users' reviews for {company_name}. The file is a PDF and every review contains fields:

        Review Date:
        Review Company:
        Review Author:
        Review Text:

        You need to ask management questions. If you need answer with data or time always use format d-m-Y h:i:s
        """

        # Query the SQLite database to check if the company exists
        record = OpenAICreds.query.filter_by(company_id=company).first()
        updated_date = sqlite_db.session.query(OpenAICreds.updated_date).order_by(OpenAICreds.updated_date.desc()).first()

        with conn.cursor() as cursor:
            # Fetch reviews for the given location
            cursor.execute("""
                SELECT displayName, starRating_number, comment, createTime, is_deleted 
                FROM tbl_location_review 
                WHERE location_id = %s
            """, (company,))
            reviews = cursor.fetchall()

        if not reviews:
            return jsonify({'response': 'Reviews for selected company id not found'}), 200
        
        # Query the MySQL database for the latest createTime
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(createTime) FROM tbl_location_review WHERE location_id = %s", (company,))
            latest_create_time_str = cursor.fetchone()[0]
            latest_create_time = datetime.strptime(latest_create_time_str, '%Y-%m-%d %H:%M:%S')

        if not record:
            print("Create new assistant")
            assistant_id = create_assistant(client, name, description, instructions)
            print(assistant_id)
            file = generate_pdf_for_location(company)
            file_id = upload_file(client, file)
            print(file_id)
            vector_id = create_vector_store_from_file(client, file_id.id, name)
            print(vector_id)
            thread_id = start_new_chat(client)
            print(thread_id)

            record = OpenAICreds(
                company_id=company,
                assistant_id=assistant_id.id,
                file_id=file_id.id,
                vector_id=vector_id.id,
                thread_id=thread_id.id,
                updated_date=datetime.utcnow()
            )
            sqlite_db.session.add(record)
            sqlite_db.session.commit()

        if updated_date and latest_create_time:
            print(f"updated_date: {updated_date[0]}, latest_create_time: {latest_create_time}")
            if updated_date[0] > latest_create_time:
                # Code for the condition where pdf file is actual, no new reviews
                print('Old file')
                assistant_id = record.assistant_id
                file_id = record.file_id
                vector_id = record.vector_id
                thread_id = record.thread_id

                aimessage = add_message(client, thread_id, user_input, file_id)
                print(aimessage)

                res = run_chat(client, thread_id, assistant_id)

                if res.status == 'completed':
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    text = messages.data[0].content[0].text.value
                    cleaned_answer = re.sub(r'【.*?】', '', text)
                    return jsonify({'response': cleaned_answer})
                else:
                    print(res.status)
                    return jsonify({'response': res.status})

            else:
                # Code for the condition when pdf file is outdated
                print('Regenerate')
                assistant_id = create_assistant(client, name, description, instructions)
                file = generate_pdf_for_location(company)
                file_id = upload_file(client, file)
                vector_id = create_vector_store_from_file(client, file_id, name)
                thread_id = start_new_chat(client)

                record.assistant_id = assistant_id.id
                record.file_id = file_id.id
                record.vector_id = vector_id.id
                record.thread_id = thread_id.id
                record.updated_date = datetime.utcnow()
                sqlite_db.session.commit()

                aimessage = add_message(client, thread_id, user_input, file_id)
                print(aimessage)

                res = run_chat(client, thread_id, assistant_id)

                if res.status == 'completed':
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    text = messages.data[0].content[0].text.value
                    cleaned_answer = find_and_convert_dates(re.sub(r'【.*?】', '', text))
                    print(cleaned_answer)
                    return jsonify({'response': cleaned_answer})
                else:
                    print(res.status)
                    return jsonify({'response': res.status})

        else:
            return jsonify({'response': 'Date retrieval error. Could not retrieve dates from one or both databases'}), 200

except BadRequestError as e:
    if 'expired' in str(e).lower():
        print("Vector store expired. Regenerating...")

        # Regenerate the assistant + PDF + vector store
        assistant_id = create_assistant(client, name, description, instructions)
        file = generate_pdf_for_location(company)
        file_id = upload_file(client, file)
        vector_id = create_vector_store_from_file(client, file_id.id, name)
        thread_id = start_new_chat(client)

        # Save to DB
        record.assistant_id = assistant_id.id
        record.file_id = file_id.id
        record.vector_id = vector_id.id
        record.thread_id = thread_id.id
        record.updated_date = datetime.utcnow()
        sqlite_db.session.commit()

        # Try the message again
        aimessage = add_message(client, thread_id, user_input, file_id.id)
        print(aimessage)

        res = run_chat(client, thread_id, assistant_id.id)

        if res.status == 'completed':
            final = get_latest_message(client, thread_id)
            return jsonify({'response': final.content[0].text.value})

        return jsonify({'response': res.status})

    else:
        print("OpenAI request error:", e)
        return jsonify({'response': str(e)}), 400


    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'response': str(e)}), 500

    finally:
        conn.close()

if __name__ == '__main__':
    with app.app_context():
        sqlite_db.create_all()  # This will create the tables if they don't exist
    app.run(debug=True, host='0.0.0.0', port=5001)
