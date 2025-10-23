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

    def process_chat_request(self, company_id, user_input, company_name, reviews):
        """Process a chat request for a company"""
        # Check if we have existing file for this company
        record = OpenAICreds.query.filter_by(company_id=company_id).first()
        
        if not record or not record.file_id:
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
            raise

        return assistant, thread_id

    def run_chat_streaming(self, company_id, user_input, company_name, reviews):
        """Run streaming chat for a company"""
        try:
            assistant, thread_id = self.process_chat_request(company_id, user_input, company_name, reviews)
            if not assistant:
                yield f"data: {json.dumps({'error': 'Failed to process request'})}\n\n"
                return

            # Stream the response
            full_response = ""
            for chunk in run_chat_streaming(self.client, thread_id, assistant.id):
                if chunk.startswith('[DONE]'):
                    # Clean the final response and send completion
                    cleaned_response = clean_response_text(full_response)
                    log_conversation(company_id, company_name, user_input, cleaned_response)
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
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

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
