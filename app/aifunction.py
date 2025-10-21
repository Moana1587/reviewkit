from dotenv import load_dotenv
import os
from openai import OpenAI
import json
import sqlite3

load_dotenv()

open_ai_key = os.getenv('OPEN_AI_KEY')

def get_reviews_by_location_id(location_id):
    """Retrieve all location reviews by ID and return as JSON."""
    query = """
        SELECT 
            location_id, 
            displayName AS customer_name, 
            starRating_number AS star_rating, 
            comment, 
            createTime AS review_creation_time 
        FROM 
            tbl_location_review
        WHERE
            location_id = ?
    """

    conn = sqlite3.connect('data.sqlite')
    cursor = conn.cursor()
    cursor.execute(query, (location_id,))
    rows = cursor.fetchall()

    reviews = []
    for row in rows:
        review_data = {
            "location_id": row[0],
            "customer_name": row[1],
            "star_rating": row[2],
            "comment": row[3],
            "review_creation_time": row[4],
        }
        reviews.append(review_data)

    conn.close()

    if reviews:
        return json.dumps(reviews)
    else:
        return json.dumps({"error": "Reviews for location not found"})

def run_conversation():
    client = OpenAI(api_key=open_ai_key)
    # Step 1: send the conversation and available functions to the model
    messages = [{"role": "user", "content": "What's the longest review?"}]
    tools = [
    {
        name: 'get_review_by_location_id',
        description: 'This function returl list of reviews with fields: Review Date, Review Company, Review Author, Review Text',
        parameters: {
            type: 'object',
            properties: {
                role_users: {
                    type: 'array',
                    items: {
                        type: 'object',
                        properties: {
                            review_date: {
                                type: 'string',
                                description: 'The date field',
                            },
                            review_company: {
                                type: 'string',
                                description: 'The company that received the review',
                            },
                            review_text: {
                                type: 'string',
                                description: 'The text pf review',
                            },
                            review_author: {
                                type: 'string',
                                description: "The name of review author",
                            },
                        },
                    },
                },
            },
            required: ['location_id'],
        },
    }
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_review_by_location_id": get_review_by_location_id,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                location=function_args.get("location"),
                unit=function_args.get("unit"),
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_to_call,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response

print(get_reviews_by_location_id('19'))