# Description: "Create a new Assistant"
import re
from datetime import datetime
import time

def create_assistant(client, name, description, instructions):
    assistant = client.beta.assistants.create(
    name=name,
    description=description,
    instructions=instructions,
    tools=[{"type": "file_search"}],
    model="gpt-4o"
    )
    return assistant

# Description: "Get an already made assistant"

def get_assistant(client, assistant_id):
    assistant = client.beta.assistants.retrieve(assistant_id)
    return assistant

# Description: "Start a new chat with a user"

def start_new_chat(client):
    empty_thread = client.beta.threads.create()
    return empty_thread.id

# Description: Retrieve previous chat/Thread

def get_chat(client, thread_id):
    thread = client.beta.threads.retrieve(thread_id)
    return thread

# Description: "Add a message to a chat/Thread" 

def add_message(client, thread, content, file_id):
    thread_message = client.beta.threads.messages.create(
    thread_id = thread,
    role="user",
    content=content,
    attachments=[
            {
                "file_id": file_id.id if hasattr(file_id, "id") else file_id,
                "tools": [{"type": "file_search"}]
            }
        ],
    )
    return thread_message

# Description: "Get the previous messages in a chat/Thread"
def get_messages_in_chat(client, thread):
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages

# Description: "Run the thread with the assistant"
def run_chat(client, thread, assistant):
    run = client.beta.threads.runs.create(
        thread_id=thread,
        assistant_id=assistant,
    )

# Wait for the run to complete
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread,
            run_id=run.id
        )
        if run_status.status in ['completed', 'failed', 'cancelled', 'expired']:
            break
        time.sleep(1)

    return run_status

#Upload file
def upload_file(client, file):
    run = client.files.create(
    file=open(file, "rb"),
    purpose="assistants"
    )
    return run

#Upload file
def create_vector_store_from_file(client, file_id, name):
    # Create vector store
    vector_store = client.beta.vector_stores.create(
        name=name
    )
    
    # Add file to vector store
    client.beta.vector_stores.files.create(
        vector_store_id=vector_store.id,
        file_id=file_id.id if hasattr(file_id, "id") else file_id
    )
    
    return vector_store

#Update assistant with new file
def update_assistant(client, assistant_id, file_id):
    run = client.beta.assistants.update(
    assistant_id=assistant_id,
    tool_resources={"file_search": {"vector_store_ids": [file_id]}},
    )
    return run

def find_and_convert_dates(text):
    # Regular expressions for different date formats, including ordinal dates
    date_patterns = [
        r'\b\d{1,2}[a-z]{2} \w{3,9} \d{4}\b',   # matches 12th June 2024
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',         # matches dd/mm/yyyy or d/m/yy, etc.
        r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',         # matches dd-mm-yyyy or d-m-yy, etc.
        r'\b\d{1,2} \w{3,9} \d{2,4}\b',         # matches d Month yyyy or dd Month yyyy
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',           # matches yyyy-mm-dd
        r'\b\w{3,9} \d{1,2}, \d{4}\b',          # matches Month dd, yyyy
    ]

    # Combined regex pattern to find any date format
    combined_pattern = re.compile('|'.join(date_patterns))

    # Find all dates in the text
    found_dates = combined_pattern.findall(text)

    # Function to remove ordinal suffixes (st, nd, rd, th) from dates
    def remove_ordinal_suffix(date_str):
        return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

    # Function to convert found date strings to desired format
    def convert_date(date_str):
        date_str = remove_ordinal_suffix(date_str)
        for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d %B %Y', '%Y-%m-%d', '%B %d, %Y',
                    '%d/%m/%y', '%d-%m-%y', '%d %b %Y', '%d %b %y', '%b %d, %Y'):
            try:
                return datetime.strptime(date_str, fmt).strftime('%d-%m-%Y %H:%M:%S')
            except ValueError:
                pass
        return None

    converted_dates = {date: convert_date(date) for date in found_dates}

    return converted_dates

def get_latest_message(client, thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    if messages.data:
        # Return the latest assistant message, not user message
        for message in reversed(messages.data):
            if message.role == 'assistant':
                return message
        # If no assistant message found, return the latest message
        return messages.data[-1]
    return None

