import os
import sqlite3
#from pdf import generate_pdf
import requests
import pandas as pd
from openai import OpenAI
from tools import *
import re
from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import Error

#load_dotenv()

#open_ai_key = os.getenv('OPEN_AI_KEY')

#client = OpenAI(api_key=open_ai_key)

#file = upload_file(client, "review.pdf")

#print(file)

#print(file.id)

#result = create_vector_store_from_file(client, file.id, "test01")

#print(result)

#result = update_assistant(client, "asst_BKYwEuNPXMx8hXtXyOxBdsas", result.id)

#print(result)


# Database connection details
hostname = '35.214.36.137'
username = 'ursajda4eqbre'
password = 'mv@{A1@c5%4%'
database = 'dbhvo6177kzjng'

connection = None
try:
    # Establish the connection
    connection = mysql.connector.connect(
        host=hostname,
        user=username,
        password=password,
        database=database
    )

    if connection.is_connected():
        print("Connection to the database was successful!")
        
        cursor = connection.cursor()

        company = 102

        with cursor:
            # Fetch reviews for the given location
            cursor.execute("""
                SELECT displayName, starRating_number, comment, createTime, is_deleted 
                FROM tbl_location_review 
                WHERE location_id = %s
            """, (company,))
            reviews = cursor.fetchall()

            print(reviews)

except Error as e:
    print("Error while connecting to MySQL", e)

finally:
    # Close the connection
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")