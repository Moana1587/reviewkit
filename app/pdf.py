import hashlib
import os
import random
import time
import pymysql
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from dotenv import load_dotenv
import os

load_dotenv()

def generate_pdf_for_location(location_id):
    # Database connection setup
    connection = pymysql.connect(
        host=os.getenv('HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

    try:
        with connection.cursor() as cursor:
            # Fetch location details
            cursor.execute("SELECT location_title FROM tbl_location WHERE location_id = %s", (location_id,))
            location_result = cursor.fetchone()
            location_name = location_result[0] if location_result else "Unknown Location"

            # Fetch reviews for the given location
            cursor.execute("""
                SELECT displayName, starRating_number, comment, createTime, is_deleted 
                FROM tbl_location_review 
                WHERE location_id = %s
            """, (location_id,))
            reviews = cursor.fetchall()

    finally:
        connection.close()

    # Define the PDF path with a short unique name
    timestamp = int(time.time())
    random_number = random.randint(0, 1000)
    short_hash = hashlib.sha256(f'{timestamp}{random_number}'.encode()).hexdigest()[:7]
    pdf_name = f"{short_hash}.pdf"
    pdf_path = "storage/"+pdf_name

    # Create a PDF instance
    pdf = canvas.Canvas(pdf_path, pagesize=letter)
    pdf.setTitle("Customer Reviews")

    # Register a Unicode supporting font
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    pdf.setFont('DejaVu', 12)

    # Define starting position
    x, y = 40, 750
    line_height = 14

    # Add reviews to the PDF
    for review in reviews:
        if y < 100:  # Add a new page if space is insufficient
            pdf.showPage()
            pdf.setFont('DejaVu', 12)
            y = 750

        customer_name, star_rating, comment, review_creation_time, is_deleted = review
        pdf.drawString(x, y, f"Review Date: {review_creation_time}")
        y -= line_height
        pdf.drawString(x, y, f"Review Company: {location_name}")
        y -= line_height
        pdf.drawString(x, y, f"Review Author: {customer_name}")
        y -= line_height
        text = pdf.beginText(x, y)
        text.textLines(f"Review Text: {comment}")
        pdf.drawText(text)
        y -= line_height * (comment.count('\n') + 2)  # Adjust for multiline comments

        y -= line_height  # Add a blank line

    # Save the PDF
    pdf.save()
    print(f"PDF generated successfully and saved to {pdf_path}")

    return pdf_path
