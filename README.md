# ReviewKit Backend - Setup Guide

## Prerequisites

1. **Python 3.8+** installed on your system
2. **MySQL Server** running and accessible
3. **OpenAI API Key** (get from https://platform.openai.com/)

## Database Setup

### MySQL Database Structure

You need to create the following tables in your MySQL database:

```sql
-- Create database
CREATE DATABASE reviewkit_db;

-- Use the database
USE reviewkit_db;

-- Create locations table
CREATE TABLE tbl_location (
    location_id VARCHAR(80) PRIMARY KEY,
    location_title VARCHAR(255) NOT NULL
);

-- Create reviews table
CREATE TABLE tbl_location_review (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id VARCHAR(80),
    displayName VARCHAR(255),
    starRating_number INT,
    comment TEXT,
    createTime DATETIME,
    is_deleted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (location_id) REFERENCES tbl_location(location_id)
);

-- Insert sample data (optional)
INSERT INTO tbl_location (location_id, location_title) VALUES 
('1', 'Sample Restaurant'),
('2', 'Sample Hotel');

INSERT INTO tbl_location_review (location_id, displayName, starRating_number, comment, createTime) VALUES 
('1', 'John Doe', 5, 'Great food and service!', '2024-01-15 10:30:00'),
('1', 'Jane Smith', 4, 'Good experience overall', '2024-01-16 14:20:00'),
('2', 'Bob Johnson', 3, 'Average stay', '2024-01-17 09:15:00');
```

## Installation Steps

### 1. Clone and Navigate to Project
```bash
cd D:\workspace\reviewkit\backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy the template and edit with your values
copy .env.template .env
```

Edit the `.env` file with your actual values:
```
OPEN_AI_KEY=sk-your-actual-openai-key
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
HOST=localhost
DB_NAME=reviewkit_db
```

### 5. Create Required Directories
```bash
mkdir storage
```

### 6. Run the Application
```bash
# Make sure you're in the app directory
cd app
python app.py
```

The application will start on `http://localhost:5001`

## Usage

1. Open your browser and go to `http://localhost:5001`
2. Use the chat interface to ask questions about reviews
3. Include a company parameter in your requests (e.g., `?company=1`)

## API Endpoints

- `GET /` - Main chat interface
- `POST /chat?company=<company_id>` - Chat with AI about company reviews

## Troubleshooting

### Common Issues:

1. **MySQL Connection Error**: 
   - Verify your MySQL credentials in `.env`
   - Ensure MySQL server is running
   - Check if the database and tables exist

2. **OpenAI API Error**:
   - Verify your API key is correct
   - Check if you have sufficient credits
   - Ensure you have access to GPT-4

3. **PDF Generation Error**:
   - Ensure the `storage/` directory exists
   - Check if `DejaVuSans.ttf` font file is present

4. **Port Already in Use**:
   - Change the port in `app.py` (line 249)
   - Kill any process using port 5001

### File Structure:
```
backend/
├── app/
│   ├── app.py              # Main Flask application
│   ├── tools.py            # OpenAI integration functions
│   ├── pdf.py              # PDF generation
│   ├── aifunction.py       # Additional AI functions
│   ├── data.sqlite         # SQLite cache database
│   ├── DejaVuSans.ttf      # Font file for PDF generation
│   ├── storage/            # Generated PDF files
│   └── templates/
│       └── index.html      # Chat interface
├── requirements.txt        # Python dependencies
├── .env.template          # Environment variables template
└── README.md              # This file
```

## Development Notes

- The application uses both MySQL (for review data) and SQLite (for caching AI assistant configurations)
- PDFs are generated dynamically and cached in the `storage/` directory
- The system automatically updates AI assistants when new reviews are added
- All AI interactions are handled through OpenAI's Assistants API
