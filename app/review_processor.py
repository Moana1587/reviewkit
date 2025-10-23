"""
Review processing and document generation utilities
"""

import os
import re
from datetime import datetime
from pdf import generate_pdf_for_location

def clean_response_text(text):
    """Remove ONLY citation references like 【4:0†source】 from text - keep everything else unchanged"""
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
        
    except Exception as e:
        pass
