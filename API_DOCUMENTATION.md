# ReviewKit API Documentation

## Base URL
```
http://YOUR_SERVER_IP:8000
```

## Overview
ReviewKit is an AI-powered review analysis API that allows you to analyze customer reviews using OpenAI's GPT models. The API supports both regular and streaming chat responses.

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

### 5. Reset Company
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
```

---

## Best Practices

1. **Always check usage status** before making multiple API calls
2. **Handle rate limiting** gracefully with exponential backoff
3. **Use streaming endpoint** for better user experience in chat interfaces
4. **Cache responses** when appropriate to reduce API calls
5. **Implement error handling** for all API calls
6. **Monitor daily limits** and notify users before they're reached
7. **Reset company data** only when necessary (troubleshooting)

---

## Support

For questions or issues, please contact your ReviewKit administrator or refer to the main documentation.

**Version:** 1.0  
**Last Updated:** October 24, 2025

