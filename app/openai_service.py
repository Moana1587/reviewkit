"""
OpenAI service for handling AI interactions
"""

import os
import json
from openai import OpenAI, BadRequestError
from models import db, OpenAICreds
from review_processor import create_text_file_for_vector_store, clean_response_text, log_conversation
from tools import get_latest_message, run_chat_streaming, create_assistant, get_assistant, start_new_chat, add_message, run_chat

class OpenAIService:
    def __init__(self):
        self.open_ai_key = os.getenv('OPEN_AI_KEY')
        self.client = OpenAI(api_key=self.open_ai_key) if self.open_ai_key else None

    def validate_api_key(self):
        """Validate if the OpenAI API key is valid and working"""
        validation_result = {
            "is_configured": False,
            "is_valid": False,
            "key_prefix": None,
            "error": None,
            "details": None
        }
        
        # Check if key is configured
        if not self.open_ai_key:
            validation_result["error"] = "OpenAI API key not configured in environment variables"
            validation_result["details"] = "Please set OPEN_AI_KEY in your .env file"
            return validation_result
        
        validation_result["is_configured"] = True
        validation_result["key_prefix"] = self.open_ai_key[:7] + "..." if len(self.open_ai_key) > 7 else "***"
        
        # Test the API key by making a simple API call
        try:
            # Try to list models (lightweight API call)
            response = self.client.models.list()
            
            # If we get here, the API key is valid
            validation_result["is_valid"] = True
            validation_result["details"] = "API key is valid and working"
            
            # Get some model info to confirm
            models = [model.id for model in response.data[:3]]
            validation_result["available_models_sample"] = models
            
            return validation_result
            
        except Exception as e:
            error_str = str(e)
            validation_result["error"] = "API key validation failed"
            
            # Provide helpful error messages
            if "401" in error_str or "Incorrect API key" in error_str:
                validation_result["details"] = "API key is invalid or incorrect"
            elif "429" in error_str or "rate_limit" in error_str.lower():
                validation_result["details"] = "Rate limit exceeded (but key appears valid)"
                validation_result["is_valid"] = True  # Key is valid, just rate limited
            elif "403" in error_str or "forbidden" in error_str.lower():
                validation_result["details"] = "API key doesn't have required permissions"
            elif "network" in error_str.lower() or "connection" in error_str.lower():
                validation_result["details"] = "Network connection error - cannot reach OpenAI API"
            else:
                validation_result["details"] = error_str
            
            return validation_result

    def setup_file_for_company(self, company_id, company_name, reviews):
        """Set up file for a company with their reviews"""
        try:
            from review_processor import create_review_document
            # Create review document
            document = create_review_document(company_name, reviews)
            
            # Create text file (temporarily using text instead of PDF)
            text_file = create_text_file_for_vector_store(document, company_id)
            
            # Upload text file to OpenAI
            with open(text_file, 'rb') as f:
                uploaded_file = self.client.files.create(
                    file=f,
                    purpose="assistants"
                )
            
            return uploaded_file
            
        except Exception as e:
            return None

    def get_or_create_assistant(self, company_name, record):
        """Get or create assistant for a company"""
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

        CRITICAL - CONTEXT ISOLATION:
        - ALWAYS search the file for fresh data - NEVER rely on conversation history
        - When counting reviews, ONLY count reviews from the file search, NOT from previous messages
        - Treat each question as independent - ignore reviews mentioned in previous conversation turns
        - Example: If user asks "How many reviews?", search the file and count ONLY the reviews in the file, not reviews mentioned earlier in the conversation

        GENERAL QUESTIONS:
        For questions NOT related to reviews (like "What color is the sky?", "How are you?", etc.), respond politely:
        "Sorry, I can't answer questions not related to reviews. Feel free to ask about reviews, ratings, or customer feedback for {company_name}!"

        Search the file to answer all questions about reviews, ratings, trends, and feedback."""

        # Create or reuse assistant
        if not record.assistant_id:
            assistant = create_assistant(self.client, assistant_name, assistant_description, assistant_instructions)
            record.assistant_id = assistant.id
            db.session.commit()
        else:
            try:
                assistant = get_assistant(self.client, record.assistant_id)
                # Update assistant instructions to ensure latest version is used
                # This ensures the fix for context isolation is applied to all existing assistants
                self.client.beta.assistants.update(
                    assistant_id=assistant.id,
                    instructions=assistant_instructions
                )
            except Exception as e:
                assistant = create_assistant(self.client, assistant_name, assistant_description, assistant_instructions)
                record.assistant_id = assistant.id
                db.session.commit()
        
        return assistant

    def get_or_create_thread(self, record):
        """Get or create thread for a company"""
        if not record.thread_id:
            thread_id = start_new_chat(self.client)
            record.thread_id = thread_id
            db.session.commit()
        else:
            thread_id = record.thread_id
        
        return thread_id

    def validate_file(self, file_id):
        """Validate if a file exists and is accessible in OpenAI"""
        try:
            self.client.files.retrieve(file_id)
            return True
        except Exception as e:
            return False

    def process_chat_request(self, company_id, user_input, company_name, reviews):
        """Process a chat request for a company"""
        # Check if we have existing file for this company
        record = OpenAICreds.query.filter_by(company_id=company_id).first()
        
        # Validate existing file or create new one
        file_is_valid = False
        if record and record.file_id:
            file_is_valid = self.validate_file(record.file_id)
        
        if not record or not record.file_id or not file_is_valid:
            # Create new file
            uploaded_file = self.setup_file_for_company(company_id, company_name, reviews)
            
            if not uploaded_file:
                return None, "Failed to create file"
            
            # Create or update record
            if not record:
                record = OpenAICreds(company_id=company_id)
                db.session.add(record)
            
            record.file_id = uploaded_file.id
            from datetime import datetime
            record.updated_date = datetime.utcnow()
            db.session.commit()

        # Get or create assistant
        assistant = self.get_or_create_assistant(company_name, record)
        
        # Get or create thread
        thread_id = self.get_or_create_thread(record)

        # Add user message to thread with file attachment
        try:
            add_message(self.client, thread_id, user_input, record.file_id)
        except Exception as e:
            # If adding message fails, it might be a thread issue
            # Try to create a new thread and retry
            thread_id = start_new_chat(self.client)
            record.thread_id = thread_id
            db.session.commit()
            # Retry adding the message
            add_message(self.client, thread_id, user_input, record.file_id)

        return assistant, thread_id

    def reset_resources_for_recovery(self, company_id):
        """Reset all resources for a company to recover from errors"""
        try:
            record = OpenAICreds.query.filter_by(company_id=company_id).first()
            if record:
                # Clear the IDs to force recreation
                record.assistant_id = None
                record.thread_id = None
                record.file_id = None
                db.session.commit()
                return True
        except Exception as e:
            return False
    
    def run_chat_streaming(self, company_id, user_input, company_name, reviews):
        """Run streaming chat for a company"""
        max_recovery_attempts = 1  # Allow one recovery attempt
        
        for recovery_attempt in range(max_recovery_attempts + 1):
            try:
                assistant, thread_id = self.process_chat_request(company_id, user_input, company_name, reviews)
                if not assistant:
                    yield f"data: {json.dumps({'error': 'Failed to process request'})}\n\n"
                    return

                # Stream the response
                full_response = ""
                had_server_error = False
                
                for chunk in run_chat_streaming(self.client, thread_id, assistant.id):
                    if chunk.startswith('[DONE]'):
                        # Clean the final response and send completion
                        cleaned_response = clean_response_text(full_response)
                        log_conversation(company_id, company_name, user_input, cleaned_response)
                        yield f"data: {json.dumps({'done': True})}\n\n"
                        return  # Success!
                        
                    elif chunk.startswith('[ERROR'):
                        # Check if this is a server error we can recover from
                        if 'server_error' in chunk.lower() and recovery_attempt < max_recovery_attempts:
                            had_server_error = True
                            if self.reset_resources_for_recovery(company_id):
                                yield f"data: {json.dumps({'chunk': 'Recovering from error, please wait...'})}\n\n"
                                break  # Break to retry with fresh resources
                        
                        # Not recoverable or final attempt
                        yield f"data: {json.dumps({'error': chunk})}\n\n"
                        return
                        
                    else:
                        # Send chunk to client
                        full_response += chunk
                        # Clean chunk before sending
                        cleaned_chunk = clean_response_text(chunk)
                        if cleaned_chunk:  # Only send if chunk has content after cleaning
                            yield f"data: {json.dumps({'chunk': cleaned_chunk})}\n\n"
                
                # If we broke out due to server error, continue to retry
                if had_server_error and recovery_attempt < max_recovery_attempts:
                    continue
                else:
                    return

            except Exception as e:
                error_msg = str(e)
                if recovery_attempt < max_recovery_attempts and ('server' in error_msg.lower() or 'not found' in error_msg.lower()):
                    if self.reset_resources_for_recovery(company_id):
                        yield f"data: {json.dumps({'chunk': 'Recovering from error, please wait...'})}\n\n"
                        continue
                
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                return

    def run_chat_regular(self, company_id, user_input, company_name, reviews):
        """Run regular (non-streaming) chat for a company"""
        try:
            assistant, thread_id = self.process_chat_request(company_id, user_input, company_name, reviews)
            if not assistant:
                return None, "Failed to process request"

            # Run the assistant
            run_status = run_chat(self.client, thread_id, assistant.id)
            
            if run_status.status == 'completed':
                # Get the latest message
                latest_message = get_latest_message(self.client, thread_id)
                if latest_message and latest_message.content:
                    # Extract raw response from OpenAI
                    raw_response = ""
                    for content_block in latest_message.content:
                        if hasattr(content_block, 'text') and content_block.text:
                            raw_response += content_block.text.value
                    
                    # Clean up file citation references
                    cleaned_response = clean_response_text(raw_response)
                    
                    # Log the conversation
                    log_conversation(company_id, company_name, user_input, cleaned_response)
                    
                    return cleaned_response, None
                else:
                    return None, "No response generated"
            else:
                # Build detailed error message
                error_msg = f'Assistant run failed with status: {run_status.status}'
                
                # Add specific error details if available
                if hasattr(run_status, 'last_error') and run_status.last_error:
                    error_code = getattr(run_status.last_error, 'code', 'unknown')
                    error_message = getattr(run_status.last_error, 'message', 'No details available')
                    error_msg += f'\n\nError Details:\n{error_code}: {error_message}'
                    
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
                
                log_conversation(company_id, company_name, user_input, error_msg)
                return None, error_msg

        except BadRequestError as e:
            error_msg = f'OpenAI API error: {str(e)}'
            log_conversation(company_id, company_name, user_input, error_msg)
            return None, error_msg

        except Exception as e:
            error_msg = f'Error: {str(e)}'
            log_conversation(company_id, company_name, user_input, error_msg)
            return None, error_msg

    def cleanup_all_gpt_resources(self):
        """Clean up all GPT resources including threads, assistants, files, and database records"""
        if not self.client:
            return {"error": "OpenAI client not initialized"}
        
        cleanup_report = {
            "threads_deleted": 0,
            "assistants_deleted": 0,
            "files_deleted": 0,
            "db_records_cleaned": 0,
            "errors": []
        }
        
        try:
            # Get all OpenAI credentials from database
            all_records = OpenAICreds.query.all()
            
            for record in all_records:
                # Delete thread
                if record.thread_id:
                    try:
                        self.client.beta.threads.delete(record.thread_id)
                        cleanup_report["threads_deleted"] += 1
                        print(f"✓ Deleted thread: {record.thread_id}")
                    except Exception as e:
                        cleanup_report["errors"].append(f"Failed to delete thread {record.thread_id}: {str(e)}")
                        print(f"✗ Failed to delete thread {record.thread_id}: {str(e)}")
                
                # Delete assistant
                if record.assistant_id:
                    try:
                        self.client.beta.assistants.delete(record.assistant_id)
                        cleanup_report["assistants_deleted"] += 1
                        print(f"✓ Deleted assistant: {record.assistant_id}")
                    except Exception as e:
                        cleanup_report["errors"].append(f"Failed to delete assistant {record.assistant_id}: {str(e)}")
                        print(f"✗ Failed to delete assistant {record.assistant_id}: {str(e)}")
                
                # Delete file
                if record.file_id:
                    try:
                        self.client.files.delete(record.file_id)
                        cleanup_report["files_deleted"] += 1
                        print(f"✓ Deleted file: {record.file_id}")
                    except Exception as e:
                        cleanup_report["errors"].append(f"Failed to delete file {record.file_id}: {str(e)}")
                        print(f"✗ Failed to delete file {record.file_id}: {str(e)}")
                
                # Delete vector store if exists
                if record.vector_id:
                    try:
                        self.client.beta.vector_stores.delete(record.vector_id)
                        print(f"✓ Deleted vector store: {record.vector_id}")
                    except Exception as e:
                        cleanup_report["errors"].append(f"Failed to delete vector store {record.vector_id}: {str(e)}")
                        print(f"✗ Failed to delete vector store {record.vector_id}: {str(e)}")
                
                # Delete database record
                try:
                    db.session.delete(record)
                    cleanup_report["db_records_cleaned"] += 1
                except Exception as e:
                    cleanup_report["errors"].append(f"Failed to delete DB record for company {record.company_id}: {str(e)}")
                    print(f"✗ Failed to delete DB record for company {record.company_id}: {str(e)}")
            
            # Commit all database deletions
            db.session.commit()
            
            print("\n" + "="*50)
            print("CLEANUP SUMMARY")
            print("="*50)
            print(f"Threads deleted: {cleanup_report['threads_deleted']}")
            print(f"Assistants deleted: {cleanup_report['assistants_deleted']}")
            print(f"Files deleted: {cleanup_report['files_deleted']}")
            print(f"Database records cleaned: {cleanup_report['db_records_cleaned']}")
            
            if cleanup_report['errors']:
                print(f"\nErrors encountered: {len(cleanup_report['errors'])}")
                for error in cleanup_report['errors']:
                    print(f"  - {error}")
            else:
                print("\n✓ All resources cleaned successfully!")
            print("="*50)
            
            return cleanup_report
            
        except Exception as e:
            db.session.rollback()
            cleanup_report["errors"].append(f"Critical error during cleanup: {str(e)}")
            print(f"\n✗ Critical error during cleanup: {str(e)}")
            return cleanup_report

    def cleanup_company_gpt_resources(self, company_id):
        """Clean up GPT resources for a specific company"""
        if not self.client:
            return {"error": "OpenAI client not initialized"}
        
        cleanup_report = {
            "company_id": company_id,
            "thread_deleted": False,
            "assistant_deleted": False,
            "file_deleted": False,
            "db_record_cleaned": False,
            "errors": []
        }
        
        try:
            # Get company record
            record = OpenAICreds.query.filter_by(company_id=company_id).first()
            
            if not record:
                cleanup_report["errors"].append(f"No record found for company_id: {company_id}")
                return cleanup_report
            
            # Delete thread
            if record.thread_id:
                try:
                    self.client.beta.threads.delete(record.thread_id)
                    cleanup_report["thread_deleted"] = True
                    print(f"✓ Deleted thread: {record.thread_id}")
                except Exception as e:
                    cleanup_report["errors"].append(f"Failed to delete thread: {str(e)}")
            
            # Delete assistant
            if record.assistant_id:
                try:
                    self.client.beta.assistants.delete(record.assistant_id)
                    cleanup_report["assistant_deleted"] = True
                    print(f"✓ Deleted assistant: {record.assistant_id}")
                except Exception as e:
                    cleanup_report["errors"].append(f"Failed to delete assistant: {str(e)}")
            
            # Delete file
            if record.file_id:
                try:
                    self.client.files.delete(record.file_id)
                    cleanup_report["file_deleted"] = True
                    print(f"✓ Deleted file: {record.file_id}")
                except Exception as e:
                    cleanup_report["errors"].append(f"Failed to delete file: {str(e)}")
            
            # Delete vector store if exists
            if record.vector_id:
                try:
                    self.client.beta.vector_stores.delete(record.vector_id)
                    print(f"✓ Deleted vector store: {record.vector_id}")
                except Exception as e:
                    cleanup_report["errors"].append(f"Failed to delete vector store: {str(e)}")
            
            # Delete database record
            try:
                db.session.delete(record)
                db.session.commit()
                cleanup_report["db_record_cleaned"] = True
                print(f"✓ Cleaned database record for company: {company_id}")
            except Exception as e:
                db.session.rollback()
                cleanup_report["errors"].append(f"Failed to delete DB record: {str(e)}")
            
            return cleanup_report
            
        except Exception as e:
            cleanup_report["errors"].append(f"Critical error: {str(e)}")
            return cleanup_report