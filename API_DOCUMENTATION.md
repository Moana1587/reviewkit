# ReviewKit API Documentation

## Base URL
```
http://YOUR_SERVER_IP:8000
```

## Overview
ReviewKit is an AI-powered review analysis API that allows you to analyze customer reviews using OpenAI's GPT models. The API provides:

- **💬 Conversational AI**: Chat with your review data using natural language
- **📊 Dynamic Semantic Analysis**: Automatically detects business type and generates relevant topics
- **🎯 Industry-Specific Insights**: Topics tailored to restaurants, hotels, tours, retail, and more
- **📈 Sentiment Scoring**: Detailed positive/neutral/negative analysis per topic
- **🔄 Streaming Responses**: Real-time chat for better user experience
- **⚡ Rate Limiting**: Built-in usage tracking and plan management

---

## Authentication
Currently, the API uses company ID-based authentication passed as query parameters. Each company has daily usage limits based on their subscription plan.

---

## API Endpoints

### 1. Chat (Regular Response)
Process a chat message and get a complete response.

**Endpoint:** `POST /chat`

**Query Parameters:**
- `company` (required): Your company ID

**Request Body:**
```json
{
  "message": "What do customers think about our service?"
}
```

**Success Response (200 OK):**
```json
{
  "response": "Based on the reviews, customers appreciate..."
}
```

**Error Responses:**

*400 Bad Request - Missing company parameter:*
```json
{
  "error": "No company parameter provided"
}
```

*429 Too Many Requests - Daily limit reached:*
```json
{
  "response": "You've reached your daily limit of 10 API calls. Please upgrade or try again tomorrow."
}
```

*500 Internal Server Error:*
```json
{
  "response": "Error: [error details]"
}
```

**Example cURL:**
```bash
curl -X POST "http://YOUR_SERVER_IP:8000/chat?company=134" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the common complaints?"}'
```

**Example JavaScript:**
```javascript
const response = await fetch('http://YOUR_SERVER_IP:8000/chat?company=134', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'What are the common complaints?'
  })
});

const data = await response.json();
console.log(data.response);
```

**Example Python:**
```python
import requests

url = "http://YOUR_SERVER_IP:8000/chat"
params = {"company": "134"}
payload = {"message": "What are the common complaints?"}

response = requests.post(url, params=params, json=payload)
data = response.json()
print(data['response'])
```

---

### 2. Chat Stream (Streaming Response)
Process a chat message and get a streaming response for real-time display.

**Endpoint:** `POST /chat-stream`

**Query Parameters:**
- `company` (required): Your company ID

**Request Body:**
```json
{
  "message": "Summarize the positive reviews"
}
```

**Response Type:** `text/event-stream` (Server-Sent Events)

**Stream Data Format:**
```
data: {"delta": "Based"}

data: {"delta": " on"}

data: {"delta": " the"}

data: {"delta": " reviews"}

data: [DONE]
```

**Error in Stream:**
```
data: {"error": "Error message"}
```

**Example JavaScript (with EventSource-like handling):**
```javascript
async function streamChat(message) {
  const response = await fetch('http://YOUR_SERVER_IP:8000/chat-stream?company=134', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          console.log('Stream complete');
          return;
        }
        try {
          const parsed = JSON.parse(data);
          if (parsed.delta) {
            process.stdout.write(parsed.delta); // Print each chunk
          } else if (parsed.error) {
            console.error('Error:', parsed.error);
          }
        } catch (e) {
          // Ignore parse errors
        }
      }
    }
  }
}

streamChat('What are the top issues?');
```

**Example Python:**
```python
import requests
import json

url = "http://YOUR_SERVER_IP:8000/chat-stream"
params = {"company": "134"}
payload = {"message": "What are the top issues?"}

response = requests.post(url, params=params, json=payload, stream=True)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = line[6:]
            if data == '[DONE]':
                break
            try:
                parsed = json.loads(data)
                if 'delta' in parsed:
                    print(parsed['delta'], end='', flush=True)
                elif 'error' in parsed:
                    print(f"\nError: {parsed['error']}")
            except json.JSONDecodeError:
                pass
```

---

### 3. Get Usage Status
Check the current usage status and limits for a company.

**Endpoint:** `GET /usage-status/<company_id>`

**Path Parameters:**
- `company_id` (required): Your company ID

**Success Response (200 OK):**
```json
{
  "company_id": "134",
  "plan_name": "free",
  "daily_limit": 10,
  "current_usage": 5,
  "remaining_calls": 5,
  "usage_date": "2025-10-24",
  "limit_reached": false
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "error": "Error message"
}
```

**Example cURL:**
```bash
curl -X GET "http://YOUR_SERVER_IP:8000/usage-status/134"
```

**Example JavaScript:**
```javascript
const response = await fetch('http://YOUR_SERVER_IP:8000/usage-status/134');
const status = await response.json();

console.log(`Remaining calls: ${status.remaining_calls}/${status.daily_limit}`);
```

**Example Python:**
```python
import requests

url = "http://YOUR_SERVER_IP:8000/usage-status/134"
response = requests.get(url)
status = response.json()

print(f"Remaining calls: {status['remaining_calls']}/{status['daily_limit']}")
```

---

### 4. Update User Plan
Update the subscription plan and daily limits for a company.

**Endpoint:** `POST /update-plan/<company_id>`

**Path Parameters:**
- `company_id` (required): Your company ID

**Request Body:**
```json
{
  "plan_name": "premium",
  "daily_limit": 100
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "company_id": "134",
  "plan_name": "premium",
  "daily_limit": 100,
  "message": "Plan updated successfully"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "success": false,
  "error": "Error message"
}
```

**Example cURL:**
```bash
curl -X POST "http://YOUR_SERVER_IP:8000/update-plan/134" \
  -H "Content-Type: application/json" \
  -d '{"plan_name": "premium", "daily_limit": 100}'
```

**Example JavaScript:**
```javascript
const response = await fetch('http://YOUR_SERVER_IP:8000/update-plan/134', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    plan_name: 'premium',
    daily_limit: 100
  })
});

const result = await response.json();
console.log(result.message);
```

---

### 5. Generate Semantic Analysis
Generate semantic analysis for a company's reviews with **dynamic business type detection** and **intelligent topic generation**. The system automatically:
1. Detects the business type based on company name and review content
2. Generates 5 relevant topics specific to that business type
3. Analyzes reviews and categorizes them with sentiment scoring

**Endpoint:** `POST /semantic-analysis/<company_id>/generate`

**Path Parameters:**
- `company_id` (required): Your company ID

**Success Response (200 OK):**
```json
{
  "success": true,
  "company_id": "134",
  "company_name": "Sample Tour Company",
  "total_reviews": 321,
  "analysis": {
    "business_type": "Tour/Activity",
    "total_reviews": 321,
    "total_mentions": 545,
    "topics": [
      {
        "name": "Guide Performance",
        "review_count": 197,
        "mention_count": 215,
        "positive_count": 180,
        "neutral_count": 15,
        "negative_count": 2,
        "sentiment_score": 4.71,
        "keywords": ["knowledgeable", "friendly", "professional", "engaging"],
        "reviews": [
          {
            "review_id": 12345,
            "review_index": 1,
            "reviewer_name": "John D.",
            "rating": 5,
            "date": "2025-10-20",
            "excerpt": "Our tour guide was absolutely amazing!",
            "sentiment": "positive"
          }
        ]
      },
      {
        "name": "Experience Content",
        "review_count": 186,
        "mention_count": 201,
        "positive_count": 165,
        "neutral_count": 18,
        "negative_count": 3,
        "sentiment_score": 4.52,
        "keywords": ["interesting", "informative", "enjoyable", "historical"],
        "reviews": [...]
      }
    ]
  },
  "radar_data": {
    "radar_points": [
      {
        "topic": "Guide Performance",
        "score": 4.71
      },
      {
        "topic": "Experience Content",
        "score": 4.52
      }
    ]
  },
  "message": "Semantic analysis generated successfully"
}
```

**Error Responses:**

*404 Not Found - Company not found:*
```json
{
  "error": "Company not found"
}
```

*404 Not Found - No reviews:*
```json
{
  "error": "No reviews found for Sample Company"
}
```

*500 Internal Server Error:*
```json
{
  "success": false,
  "error": "Failed to generate analysis: [error details]"
}
```

**Example cURL:**
```bash
curl -X POST "http://YOUR_SERVER_IP:8000/semantic-analysis/134/generate"
```

**Example JavaScript:**
```javascript
const response = await fetch('http://YOUR_SERVER_IP:8000/semantic-analysis/134/generate', {
  method: 'POST'
});

const data = await response.json();
console.log(`Analysis generated for ${data.total_reviews} reviews`);
console.log(`Total mentions: ${data.analysis.total_mentions}`);
```

**Example Python:**
```python
import requests

url = "http://YOUR_SERVER_IP:8000/semantic-analysis/134/generate"
response = requests.post(url)
data = response.json()

print(f"Business Type: {data['analysis']['business_type']}")
print(f"Analysis generated for {data['total_reviews']} reviews")
for topic in data['analysis']['topics']:
    print(f"{topic['name']}: {topic['sentiment_score']}/5.0 ({topic['positive_count']} positive, {topic['negative_count']} negative)")
```

**Example Business-Specific Topics:**

*Tour/Activity Business:*
```json
{
  "business_type": "Tour/Activity",
  "topics": [
    {"name": "Guide Performance", "sentiment_score": 4.5},
    {"name": "Experience Content", "sentiment_score": 4.3},
    {"name": "Organization", "sentiment_score": 4.2},
    {"name": "Atmosphere", "sentiment_score": 4.4},
    {"name": "Value for Money", "sentiment_score": 3.8}
  ]
}
```

*Restaurant/Dining Business:*
```json
{
  "business_type": "Restaurant/Dining",
  "topics": [
    {"name": "Food Quality", "sentiment_score": 4.6},
    {"name": "Service", "sentiment_score": 4.2},
    {"name": "Ambiance", "sentiment_score": 4.4},
    {"name": "Menu Variety", "sentiment_score": 3.9},
    {"name": "Value for Money", "sentiment_score": 3.7}
  ]
}
```

*Hotel/Accommodation Business:*
```json
{
  "business_type": "Hotel/Accommodation",
  "topics": [
    {"name": "Room Quality", "sentiment_score": 4.3},
    {"name": "Staff Service", "sentiment_score": 4.5},
    {"name": "Cleanliness", "sentiment_score": 4.7},
    {"name": "Amenities", "sentiment_score": 4.1},
    {"name": "Value for Money", "sentiment_score": 3.9}
  ]
}
```

---

### 6. Get Semantic Analysis
Retrieve the cached semantic analysis for a company.

**Endpoint:** `GET /semantic-analysis/<company_id>`

**Path Parameters:**
- `company_id` (required): Your company ID

**Success Response (200 OK):**
```json
{
  "company_id": "134",
  "company_name": "Sample Tour Company",
  "total_reviews": 321,
  "analysis": {
    "total_reviews": 321,
    "total_mentions": 545,
    "topics": [...]
  },
  "radar_data": {
    "radar_points": [...]
  },
  "created_date": "2025-10-24T10:30:00",
  "updated_date": "2025-10-24T10:30:00"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "No analysis found. Please generate analysis first."
}
```

**Example cURL:**
```bash
curl -X GET "http://YOUR_SERVER_IP:8000/semantic-analysis/134"
```

**Example JavaScript:**
```javascript
const response = await fetch('http://YOUR_SERVER_IP:8000/semantic-analysis/134');
const analysis = await response.json();

// Display radar chart data
analysis.radar_data.radar_points.forEach(point => {
  console.log(`${point.topic}: ${point.score}/5`);
});
```

---

### 7. Get Semantic Analysis Summary
Get a quick summary of semantic analysis with counts only (lighter response). This endpoint provides just the key metrics without review excerpts or keywords.

**Endpoint:** `GET /semantic-analysis/<company_id>/summary`

**Path Parameters:**
- `company_id` (required): Your company ID

**Success Response (200 OK):**
```json
{
  "company_id": "134",
  "company_name": "Sample Restaurant",
  "total_reviews": 321,
  "total_mentions": 545,
  "topics_summary": [
    {
      "name": "Food Quality",
      "review_count": 197,
      "positive": 180,
      "neutral": 15,
      "negative": 2,
      "sentiment_score": 4.71
    },
    {
      "name": "Service",
      "review_count": 186,
      "positive": 165,
      "neutral": 18,
      "negative": 3,
      "sentiment_score": 4.52
    },
    {
      "name": "Ambiance",
      "review_count": 175,
      "positive": 160,
      "neutral": 12,
      "negative": 3,
      "sentiment_score": 4.63
    }
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "No analysis found"
}
```

**Example cURL:**
```bash
curl -X GET "http://YOUR_SERVER_IP:8000/semantic-analysis/134/summary"
```

**Example JavaScript:**
```javascript
const response = await fetch('http://YOUR_SERVER_IP:8000/semantic-analysis/134/summary');
const summary = await response.json();

// Display semantic counts
summary.topics_summary.forEach(topic => {
  const total = topic.positive + topic.neutral + topic.negative;
  console.log(`${topic.name}: ${topic.positive}/${total} positive (${Math.round(topic.positive/total*100)}%)`);
});
```

---

### 8. Reset Company
Reset the OpenAI assistant and thread for a company (useful for troubleshooting).

**Endpoint:** `POST /reset-company/<company_id>`

**Path Parameters:**
- `company_id` (required): Your company ID

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Reset complete for company 134",
  "old_assistant_id": "asst_xxx",
  "old_thread_id": "thread_xxx"
}
```

**No Records Response (200 OK):**
```json
{
  "success": true,
  "message": "No records found for company 134 (nothing to reset)"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "success": false,
  "error": "Error message"
}
```

**Example cURL:**
```bash
curl -X POST "http://YOUR_SERVER_IP:8000/reset-company/134"
```

**Example JavaScript:**
```javascript
const response = await fetch('http://YOUR_SERVER_IP:8000/reset-company/134', {
  method: 'POST'
});

const result = await response.json();
console.log(result.message);
```

---

### 9. Clear Thread
Clear the conversation thread for a company to start fresh (preserves assistant and files).

**Endpoint:** `POST /clear-thread/<company_id>`

**Path Parameters:**
- `company_id` (required): Your company ID

**Description:**
This endpoint creates a new conversation thread, effectively clearing the conversation history. Previous questions and answers will no longer affect new responses. The assistant and uploaded review files are preserved, only the conversation context is reset.

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Thread cleared for company 134. Previous conversations will not affect new questions.",
  "old_thread_id": "thread_xxx",
  "new_thread_id": "thread_yyy"
}
```

**No Records Response (200 OK):**
```json
{
  "success": true,
  "message": "No records found for company 134 (nothing to clear)"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "success": false,
  "error": "Error message"
}
```

**Example cURL:**
```bash
curl -X POST "http://YOUR_SERVER_IP:8000/clear-thread/134"
```

**Example JavaScript:**
```javascript
const response = await fetch('http://YOUR_SERVER_IP:8000/clear-thread/134', {
  method: 'POST'
});

const result = await response.json();
console.log(result.message);
// Output: "Thread cleared for company 134. Previous conversations will not affect new questions."
```

**Example Python:**
```python
import requests

url = "http://YOUR_SERVER_IP:8000/clear-thread/134"
response = requests.post(url)
result = response.json()

print(result['message'])
# Output: "Thread cleared for company 134. Previous conversations will not affect new questions."
```

**Use Cases:**
- Start a new conversation session without previous context
- Reset conversation when switching topics
- Clear context after a series of related questions
- Troubleshoot issues with context affecting responses

**Difference from Reset Company:**
- `clear-thread`: Only clears conversation history (fast, preserves assistant and files)
- `reset-company`: Clears everything including assistant and files (slower, full reset)

---

## Rate Limiting

The API implements daily usage limits based on subscription plans:

| Plan | Daily Limit |
|------|-------------|
| Free | 10 calls |
| Premium | 100 calls (customizable) |
| Enterprise | Unlimited (customizable) |

When you reach your daily limit, you'll receive a `429 Too Many Requests` response. Limits reset at midnight UTC.

---

## Data Models

### Company Record
```json
{
  "company_id": "string",
  "assistant_id": "string",
  "file_id": "string",
  "vector_id": "string",
  "thread_id": "string",
  "updated_date": "datetime"
}
```

### User Plan
```json
{
  "company_id": "string",
  "plan_name": "string",
  "daily_limit": "integer",
  "created_date": "datetime",
  "updated_date": "datetime"
}
```

### Daily Usage
```json
{
  "company_id": "string",
  "usage_date": "date",
  "call_count": "integer",
  "last_reset": "datetime"
}
```

### Semantic Analysis
```json
{
  "company_id": "string",
  "company_name": "string",
  "total_reviews": "integer",
  "analysis_data": {
    "business_type": "string",
    "total_reviews": "integer",
    "total_mentions": "integer",
    "topics": [
      {
        "name": "string",
        "review_count": "integer",
        "mention_count": "integer",
        "positive_count": "integer",
        "neutral_count": "integer",
        "negative_count": "integer",
        "sentiment_score": "float",
        "keywords": ["string"],
        "reviews": [
          {
            "review_id": "integer",
            "review_index": "integer",
            "reviewer_name": "string",
            "rating": "integer",
            "date": "string",
            "excerpt": "string",
            "sentiment": "positive|neutral|negative"
          }
        ]
      }
    ]
  },
  "created_date": "datetime",
  "updated_date": "datetime"
}
```

---

## Error Handling

All endpoints follow consistent error response formats:

**Client Errors (4xx):**
- `400` - Bad Request (missing parameters)
- `429` - Too Many Requests (daily limit exceeded)

**Server Errors (5xx):**
- `500` - Internal Server Error

Example error response:
```json
{
  "error": "Detailed error message",
  "response": "User-friendly error message"
}
```

---

## Integration Examples

### React/Next.js Integration

```javascript
// api/reviewkit.js
class ReviewKitAPI {
  constructor(baseURL, companyId) {
    this.baseURL = baseURL;
    this.companyId = companyId;
  }

  async chat(message) {
    const response = await fetch(
      `${this.baseURL}/chat?company=${this.companyId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      }
    );
    return response.json();
  }

  async *chatStream(message) {
    const response = await fetch(
      `${this.baseURL}/chat-stream?company=${this.companyId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      }
    );

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          try {
            const parsed = JSON.parse(data);
            if (parsed.delta) yield parsed.delta;
            if (parsed.error) throw new Error(parsed.error);
          } catch (e) {
            if (e.message) throw e;
          }
        }
      }
    }
  }

  async getUsageStatus() {
    const response = await fetch(
      `${this.baseURL}/usage-status/${this.companyId}`
    );
    return response.json();
  }

  async updatePlan(planName, dailyLimit) {
    const response = await fetch(
      `${this.baseURL}/update-plan/${this.companyId}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_name: planName, daily_limit: dailyLimit })
      }
    );
    return response.json();
  }

  async generateSemanticAnalysis() {
    const response = await fetch(
      `${this.baseURL}/semantic-analysis/${this.companyId}/generate`,
      { method: 'POST' }
    );
    return response.json();
  }

  async getSemanticAnalysis() {
    const response = await fetch(
      `${this.baseURL}/semantic-analysis/${this.companyId}`
    );
    return response.json();
  }

  async getSemanticSummary() {
    const response = await fetch(
      `${this.baseURL}/semantic-analysis/${this.companyId}/summary`
    );
    return response.json();
  }
}

export default ReviewKitAPI;
```

**Usage:**
```javascript
import ReviewKitAPI from './api/reviewkit';

const api = new ReviewKitAPI('http://YOUR_SERVER_IP:8000', '134');

// Regular chat
const result = await api.chat('What are the common issues?');
console.log(result.response);

// Streaming chat
for await (const chunk of api.chatStream('Summarize positive feedback')) {
  console.log(chunk);
}

// Check usage
const status = await api.getUsageStatus();
console.log(`${status.remaining_calls} calls remaining`);

// Generate and display semantic analysis
const analysis = await api.generateSemanticAnalysis();
console.log(`Analyzed ${analysis.total_reviews} reviews`);

// Display radar chart data
analysis.radar_data.radar_points.forEach(point => {
  console.log(`${point.topic}: ${point.score}/5 (${point.total_mentions} mentions)`);
});
```

### Python SDK Example

```python
# reviewkit_client.py
import requests
import json
from typing import Iterator

class ReviewKitClient:
    def __init__(self, base_url: str, company_id: str):
        self.base_url = base_url.rstrip('/')
        self.company_id = company_id
    
    def chat(self, message: str) -> dict:
        """Send a chat message and get a complete response"""
        url = f"{self.base_url}/chat"
        params = {"company": self.company_id}
        payload = {"message": message}
        
        response = requests.post(url, params=params, json=payload)
        response.raise_for_status()
        return response.json()
    
    def chat_stream(self, message: str) -> Iterator[str]:
        """Send a chat message and get streaming response"""
        url = f"{self.base_url}/chat-stream"
        params = {"company": self.company_id}
        payload = {"message": message}
        
        response = requests.post(url, params=params, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        parsed = json.loads(data)
                        if 'delta' in parsed:
                            yield parsed['delta']
                        elif 'error' in parsed:
                            raise Exception(parsed['error'])
                    except json.JSONDecodeError:
                        pass
    
    def get_usage_status(self) -> dict:
        """Get current usage status"""
        url = f"{self.base_url}/usage-status/{self.company_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def update_plan(self, plan_name: str, daily_limit: int) -> dict:
        """Update subscription plan"""
        url = f"{self.base_url}/update-plan/{self.company_id}"
        payload = {"plan_name": plan_name, "daily_limit": daily_limit}
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def reset_company(self) -> dict:
        """Reset company's assistant and thread"""
        url = f"{self.base_url}/reset-company/{self.company_id}"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()
    
    def clear_thread(self) -> dict:
        """Clear conversation thread (preserves assistant and files)"""
        url = f"{self.base_url}/clear-thread/{self.company_id}"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()
    
    def generate_semantic_analysis(self) -> dict:
        """Generate semantic analysis for company reviews"""
        url = f"{self.base_url}/semantic-analysis/{self.company_id}/generate"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()
    
    def get_semantic_analysis(self) -> dict:
        """Get cached semantic analysis"""
        url = f"{self.base_url}/semantic-analysis/{self.company_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_semantic_summary(self) -> dict:
        """Get semantic analysis summary"""
        url = f"{self.base_url}/semantic-analysis/{self.company_id}/summary"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == "__main__":
    client = ReviewKitClient("http://YOUR_SERVER_IP:8000", "134")
    
    # Regular chat
    result = client.chat("What are the common issues?")
    print(result['response'])
    
    # Streaming chat
    print("\nStreaming response:")
    for chunk in client.chat_stream("Summarize positive feedback"):
        print(chunk, end='', flush=True)
    print()
    
    # Check usage
    status = client.get_usage_status()
    print(f"\nRemaining calls: {status['remaining_calls']}/{status['daily_limit']}")
    
    # Clear conversation thread (start fresh)
    print("\nClearing conversation thread...")
    clear_result = client.clear_thread()
    print(clear_result['message'])
    
    # Generate semantic analysis
    print("\nGenerating semantic analysis...")
    analysis = client.generate_semantic_analysis()
    print(f"Business Type: {analysis['analysis']['business_type']}")
    print(f"Analyzed {analysis['total_reviews']} reviews")
    
    # Display topics
    print("\nGenerated Topics:")
    for topic in analysis['analysis']['topics']:
        emoji = "🟢" if topic['sentiment_score'] >= 4 else "🟡" if topic['sentiment_score'] >= 2.5 else "🔴"
        print(f"  {emoji} {topic['name']}: {topic['sentiment_score']}/5.0")
        if topic.get('keywords'):
            print(f"     Keywords: {', '.join(topic['keywords'][:5])}")
    
    # Get summary
    summary = client.get_semantic_summary()
    print("\nTopic Summary:")
    for topic in summary['topics_summary']:
        total = topic['positive'] + topic['neutral'] + topic['negative']
        if total > 0:
            pos_pct = round(topic['positive']/total*100)
            print(f"  {topic['name']}: {pos_pct}% positive ({topic['review_count']} reviews)")
```

---

## Best Practices

1. **Always check usage status** before making multiple API calls
2. **Handle rate limiting** gracefully with exponential backoff
3. **Use streaming endpoint** for better user experience in chat interfaces
4. **Cache responses** when appropriate to reduce API calls
5. **Implement error handling** for all API calls
6. **Monitor daily limits** and notify users before they're reached
7. **Clear thread context** when switching conversation topics or starting new sessions
8. **Reset company data** only when necessary (troubleshooting)
9. **Regenerate semantic analysis** after significant changes to reviews or business focus
10. **Use business_type field** to customize UI/UX based on industry
11. **Display keywords** to give users quick insights about topics
12. **Cache semantic analysis** to avoid unnecessary regeneration (it's computationally expensive)

---

## Support

For questions or issues, please contact your ReviewKit administrator or refer to the main documentation.

## Semantic Analysis: Dynamic Topic Generation

### Overview

The semantic analysis system uses **AI-powered business type detection** and **intelligent topic generation** to provide the most relevant insights for each business. Unlike static categories, topics are dynamically generated based on what matters most to your specific industry.

### How It Works

1. **Business Type Detection** (First 30 reviews analyzed)
   - Analyzes company name and review content
   - Identifies the primary business category
   - Supported types: Tour/Activity, Restaurant/Dining, Hotel/Accommodation, Retail/Shopping, Service/Professional, Entertainment/Recreation, Transportation, Healthcare, and more

2. **Dynamic Topic Generation**
   - Generates 5 topics specifically relevant to your business type
   - Topics are created using AI to match industry standards
   - Always includes "Value for Money" as a universal concern
   - Topics are distinct and non-overlapping

3. **Review Analysis**
   - Each review is categorized into relevant topics
   - Multiple topics can be assigned to a single review
   - Sentiment is analyzed separately for each topic
   - Extracts key excerpts and keywords

### Topic Examples by Business Type

| Business Type | Typical Topics |
|---------------|----------------|
| **Tour/Activity** | Guide Performance, Experience Content, Organization, Atmosphere, Value for Money |
| **Restaurant/Dining** | Food Quality, Service, Ambiance, Menu Variety, Value for Money |
| **Hotel/Accommodation** | Room Quality, Staff Service, Cleanliness, Amenities, Value for Money |
| **Retail/Shopping** | Product Quality, Customer Service, Store Experience, Product Selection, Value for Money |
| **Service/Professional** | Service Quality, Staff Expertise, Professionalism, Facility, Value for Money |
| **Entertainment** | Show Quality, Venue, Staff, Experience, Value for Money |

*Note: Actual topics are generated dynamically and may vary based on your specific business and customer feedback patterns.*

### Sentiment Classification

- **Positive**: 4-5 stars OR clearly positive language
- **Negative**: 1-2 stars OR clearly negative language
- **Neutral**: 3 stars OR mixed/neutral language

### Sentiment Score Calculation

The sentiment score (0-5) for each topic is calculated as:
```
sentiment_score = ((positive_count - negative_count + neutral_count * 0.5) / total_count) * 5
```

**Score Interpretation:**
- **4.5 - 5.0**: Excellent (strong positive sentiment)
- **3.5 - 4.4**: Good (mostly positive)
- **2.5 - 3.4**: Mixed (balanced or neutral)
- **1.5 - 2.4**: Poor (mostly negative)
- **0.0 - 1.4**: Very Poor (strong negative sentiment)

This provides a normalized view of sentiment across all topics for easy comparison and visualization in radar charts.

### Response Fields

Each topic in the analysis includes:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Dynamically generated topic name |
| `review_count` | integer | Number of reviews mentioning this topic |
| `mention_count` | integer | Total mentions (a review can mention multiple times) |
| `positive_count` | integer | Count of positive mentions |
| `neutral_count` | integer | Count of neutral mentions |
| `negative_count` | integer | Count of negative mentions |
| `sentiment_score` | float | Overall sentiment score (0-5) |
| `keywords` | array | Top keywords extracted from reviews |
| `reviews` | array | Individual review excerpts with sentiment |

### Advantages of Dynamic Topics

✅ **Relevance**: Topics match what actually matters in your industry  
✅ **Accuracy**: Better categorization with industry-specific terms  
✅ **Flexibility**: Works for any business type automatically  
✅ **Insights**: More actionable feedback aligned with industry standards  
✅ **Scalability**: No manual configuration needed for different business types

---

## Version History

### Version 2.0 (October 28, 2025)
- ✨ **NEW**: Dynamic business type detection
- ✨ **NEW**: Intelligent topic generation based on business type
- ✨ **NEW**: Industry-specific analysis for restaurants, hotels, tours, and more
- ✨ **NEW**: Keywords field in topic analysis
- 📝 Enhanced semantic analysis with `business_type` field
- 📝 Updated topic structure to be dynamically generated
- 📝 Improved sentiment scoring accuracy

### Version 1.1 (October 27, 2025)
- Initial semantic analysis implementation
- Fixed topics for tour/activity businesses
- Basic sentiment analysis

---

**Current Version:** 2.0  
**Last Updated:** October 28, 2025

