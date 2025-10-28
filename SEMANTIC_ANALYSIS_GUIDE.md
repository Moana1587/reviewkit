# Semantic Analysis Implementation Guide

## Overview

The semantic analysis feature has been successfully implemented in your ReviewKit backend. This **intelligent system** automatically detects your business type and generates relevant topics specific to your industry, then performs sentiment analysis on each topic.

## 🚀 New in Version 2.0

- **🏢 Automatic Business Type Detection** - Identifies whether you're a restaurant, hotel, tour, retail store, or other business type
- **🎯 Dynamic Topic Generation** - Creates 5 industry-specific topics tailored to your business
- **📊 Industry-Specific Analysis** - Gets insights that matter to YOUR specific industry
- **🔑 Keyword Extraction** - Identifies important terms from customer feedback

## Features Implemented

### 1. **Database Model** (`app/models.py`)
- New `SemanticAnalysis` model to store analysis results
- Stores JSON data with business type, topics, sentiments, and review excerpts
- One cached analysis per company (updates on regeneration)

### 2. **Semantic Analyzer Service** (`app/semantic_analyzer.py`)
- Uses OpenAI GPT-4o-mini for intelligent categorization
- **Automatically detects business type** from company name and reviews
- **Dynamically generates 5 relevant topics** based on business type:
  - **Tour/Activity**: Guide Performance, Experience Content, Organization, Atmosphere, Value for Money
  - **Restaurant/Dining**: Food Quality, Service, Ambiance, Menu Variety, Value for Money
  - **Hotel/Accommodation**: Room Quality, Staff Service, Cleanliness, Amenities, Value for Money
  - **Retail/Shopping**: Product Quality, Customer Service, Store Experience, Product Selection, Value for Money
  - **Service/Professional**: Service Quality, Staff Expertise, Professionalism, Facility, Value for Money
  - **And more...**
- Performs sentiment classification (positive/neutral/negative)
- Extracts keywords from reviews
- Generates radar chart data for visualization
- Handles up to 300 reviews per analysis (configurable)

### 3. **API Endpoints** (`app/routes.py`)
Three new endpoints:
- `POST /semantic-analysis/<company_id>/generate` - Generate new analysis
- `GET /semantic-analysis/<company_id>` - Retrieve cached analysis
- `GET /semantic-analysis/<company_id>/summary` - Get summary (lighter response)

### 4. **Documentation** (`API_DOCUMENTATION.md`)
- Complete API documentation with examples
- Integration examples for JavaScript and Python
- Data model specifications

## How to Use

### Step 1: Start the Server

```bash
cd app
python app.py
```

Or for production:
```bash
cd app
python app.py --host 0.0.0.0 --port 8000
```

### Step 2: Generate Semantic Analysis

**Using cURL:**
```bash
curl -X POST "http://127.0.0.1:8000/semantic-analysis/134/generate"
```

**Using Python:**
```python
import requests

response = requests.post("http://127.0.0.1:8000/semantic-analysis/134/generate")
analysis = response.json()

print(f"Business Type: {analysis['analysis']['business_type']}")
print(f"Analyzed {analysis['total_reviews']} reviews")
print("\nGenerated Topics:")
for topic in analysis['analysis']['topics']:
    print(f"  {topic['name']}: {topic['sentiment_score']}/5.0")
    print(f"    ({topic['positive_count']} positive, {topic['negative_count']} negative)")
    if topic.get('keywords'):
        print(f"    Keywords: {', '.join(topic['keywords'][:5])}")
```

**Using JavaScript:**
```javascript
const response = await fetch('http://127.0.0.1:8000/semantic-analysis/134/generate', {
  method: 'POST'
});
const analysis = await response.json();
console.log(analysis);
```

### Step 3: Retrieve Analysis Results

**Get Full Analysis:**
```bash
curl "http://127.0.0.1:8000/semantic-analysis/134"
```

**Get Summary Only:**
```bash
curl "http://127.0.0.1:8000/semantic-analysis/134/summary"
```

## Response Structure

### Full Analysis Response

```json
{
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
        "keywords": ["knowledgeable", "friendly", "professional", "engaging", "helpful"],
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
        "keywords": ["interesting", "informative", "enjoyable", "historical", "educational"],
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
  }
}
```

### Example Responses by Business Type

**Restaurant Business:**
```json
{
  "business_type": "Restaurant/Dining",
  "topics": [
    {"name": "Food Quality", "sentiment_score": 4.6, "keywords": ["delicious", "fresh", "tasty"]},
    {"name": "Service", "sentiment_score": 4.2, "keywords": ["attentive", "friendly", "quick"]},
    {"name": "Ambiance", "sentiment_score": 4.4, "keywords": ["cozy", "romantic", "modern"]},
    {"name": "Menu Variety", "sentiment_score": 3.9, "keywords": ["options", "selection", "diverse"]},
    {"name": "Value for Money", "sentiment_score": 3.7, "keywords": ["price", "worth", "expensive"]}
  ]
}
```

**Hotel Business:**
```json
{
  "business_type": "Hotel/Accommodation",
  "topics": [
    {"name": "Room Quality", "sentiment_score": 4.3, "keywords": ["comfortable", "spacious", "clean"]},
    {"name": "Staff Service", "sentiment_score": 4.5, "keywords": ["helpful", "friendly", "professional"]},
    {"name": "Cleanliness", "sentiment_score": 4.7, "keywords": ["spotless", "tidy", "immaculate"]},
    {"name": "Amenities", "sentiment_score": 4.1, "keywords": ["pool", "gym", "wifi"]},
    {"name": "Value for Money", "sentiment_score": 3.9, "keywords": ["price", "worth", "affordable"]}
  ]
}
```

## Advantages of Dynamic Topics

### Why Dynamic Topic Generation is Better

✅ **Industry Relevance** - Topics match what actually matters in each industry  
✅ **Better Insights** - Restaurant owners see "Food Quality", not "Tour Guide Performance"  
✅ **Automatic Adaptation** - Works for any business type without manual configuration  
✅ **Customer Language** - Uses terms and phrases customers actually use  
✅ **Scalability** - Add new business types without code changes  
✅ **Accuracy** - Better categorization with industry-specific terminology  

### Comparison: Static vs Dynamic Topics

| Aspect | Old (Static) | New (Dynamic) |
|--------|--------------|---------------|
| Topics | Same 5 topics for all | Industry-specific 5 topics |
| Relevance | Low for non-tour businesses | High for all business types |
| Setup | Manual configuration needed | Automatic detection |
| Accuracy | Moderate | High |
| Flexibility | Limited | Unlimited |
| Keywords | No | Yes, extracted automatically |
| Business Type | Unknown | Detected and stored |

## Frontend Integration

### Building the UI Components

Based on the reference image, you'll need to create:

#### 1. **Sentiment Radar Chart**
Use the `radar_data.radar_points` to render a pentagon radar chart:
```javascript
const radarData = analysis.radar_data.radar_points;
// Use Chart.js, Recharts, or similar library
// Points: radarData.map(p => p.score) // values 0-5
// Labels: radarData.map(p => p.topic)
```

#### 2. **Semantic Counts Bar Chart**
Horizontal stacked bar chart showing positive/neutral/negative counts:
```javascript
topics.forEach(topic => {
  const data = {
    positive: topic.positive_count,
    neutral: topic.neutral_count,
    negative: topic.negative_count
  };
  // Render as horizontal stacked bar
});
```

#### 3. **Business Type Badge**
Display the detected business type prominently:
```javascript
const businessType = analysis.analysis.business_type;
// Render as a badge: <Badge>🏢 {businessType}</Badge>
```

#### 4. **Keyword Tags**
Display extracted keywords for each topic:
```javascript
topic.keywords.forEach(keyword => {
  // Render as tag/chip: <Tag>{keyword}</Tag>
});
```

#### 5. **Semantic Sentiment Analysis List**
Display each topic with:
- Topic name and counts (e.g., "Food Quality (197)")
- Sentiment score as a horizontal bar
- Keywords as tags/badges
- List of review excerpts with highlighting

```javascript
topics.forEach(topic => {
  // Show topic header
  console.log(`${topic.name} (${topic.review_count})`);
  console.log(`Sentiment: ${topic.sentiment_score}/5.0`);
  
  // Show keywords
  if (topic.keywords && topic.keywords.length > 0) {
    console.log(`Keywords: ${topic.keywords.join(', ')}`);
  }
  
  // Show review excerpts
  topic.reviews.forEach(review => {
    console.log(`"${review.excerpt}" - ${review.reviewer_name}`);
  });
});
```

## Testing

Run the included test script:

```bash
# Make sure the server is running first
python test_semantic_analysis.py
```

The test script will:
1. Check server connection
2. Generate semantic analysis
3. Retrieve the analysis
4. Get the summary
5. Display results

## How Dynamic Topic Generation Works

The semantic analysis now uses a sophisticated 3-step process:

### Step 1: Business Type Detection
```python
# Analyzes first 30 reviews + company name
# Detects from categories:
- Tour/Activity
- Restaurant/Dining  
- Hotel/Accommodation
- Retail/Shopping
- Service/Professional
- Entertainment/Recreation
- Transportation
- Healthcare
- Other
```

### Step 2: Dynamic Topic Generation
```python
# AI generates 5 industry-specific topics
# Always includes "Value for Money"
# Topics are tailored to business type
# Example: Restaurant gets "Food Quality", "Service", "Ambiance", etc.
```

### Step 3: Review Analysis
```python
# Categorizes each review into generated topics
# Extracts sentiment and keywords
# Compiles excerpts for each topic
```

## Configuration

### Adjusting Analysis Parameters

Edit `app/semantic_analyzer.py`:

```python
def analyze_reviews(self, company_name, reviews, max_reviews=300):
    # Change max_reviews to analyze more/fewer reviews
    # Default is 300 reviews for optimal performance
```

### Changing Business Type Categories

Edit `app/semantic_analyzer.py` in the `_detect_business_type` method to add more categories:

```python
def _detect_business_type(self, company_name, formatted_reviews):
    # Add new categories to the prompt
    # Categories: Tour/Activity, Restaurant/Dining, etc.
```

### Changing the AI Model

In `semantic_analyzer.py`:

**For Business Type Detection (line ~122):**
```python
model="gpt-4o-mini",  # Fast and cost-effective
```

**For Topic Generation (line ~182):**
```python
model="gpt-4o-mini",  # Good balance of cost/quality
```

**For Review Analysis (line ~258):**
```python
model="gpt-4o-mini",  # Change to "gpt-4o" for better accuracy (higher cost)
```

### Default Topics (Fallback)

If API calls fail, the system falls back to default tour topics defined in `DEFAULT_TOPICS`:

```python
DEFAULT_TOPICS = [
    "Tour Guide/Host Performance",
    "Tour Content and Experience",
    "Organization & Management",
    "Atmosphere and Special Effects",
    "Value for Money"
]
```

## Performance Considerations

1. **First Analysis**: Takes 15-40 seconds (includes business type detection + topic generation + analysis)
2. **Cached Results**: Subsequent retrievals are instant
3. **Regeneration**: Recommended when new reviews are added or business focus changes
4. **Cost**: ~$0.15-0.40 per analysis (300 reviews with GPT-4o-mini, includes 3 API calls)
   - Business type detection: ~$0.02
   - Topic generation: ~$0.03
   - Review analysis: ~$0.10-0.35

### API Calls per Analysis

The system makes **3 OpenAI API calls**:
1. **Business Type Detection** - Analyzes first 30 reviews (~500 tokens)
2. **Topic Generation** - Creates 5 relevant topics (~300 tokens)
3. **Review Analysis** - Categorizes all reviews (~5000-10000 tokens depending on review count)

### Optimization Tips

- **Cache aggressively**: Analysis results don't change unless reviews change
- **Batch processing**: Generate analysis during off-peak hours
- **Monitor usage**: Track OpenAI API costs per company
- **Review limits**: 300 reviews gives good accuracy without excessive cost

## Caching Strategy

- Analysis results are cached in the database
- Each company has ONE cached analysis
- Regenerating overwrites the cached version
- Recommended: Regenerate daily or when reviews change significantly

## Error Handling

Common errors and solutions:

### "Company not found"
- Check that the company_id exists in your database
- Verify the MySQL connection

### "No reviews found"
- Ensure the company has reviews in `tbl_location_review`
- Check that reviews aren't marked as deleted

### "OpenAI API key not configured"
- Set `OPEN_AI_KEY` in your `.env` file
- Restart the server

### "OpenAI analysis failed"
- Check your OpenAI API quota
- Verify API key permissions
- Check internet connectivity

## Next Steps

### Frontend Implementation

1. **Create React Components** (or your framework of choice):
   - `SemanticRadar.jsx` - Radar chart
   - `SemanticCounts.jsx` - Bar charts
   - `SemanticList.jsx` - Review excerpts

2. **Add Filtering** (as shown in image):
   - Filter by review profile
   - Filter by platform
   - Filter by language
   - Date range filtering
   - Content filtering

3. **Add Search**:
   - Keyword search through topics
   - Search within review excerpts

4. **Export Features**:
   - Export analysis as PDF
   - Export data as CSV/Excel

### Backend Enhancements

1. **Scheduled Analysis**:
   ```python
   # Add cron job or scheduled task
   # Regenerate analysis daily for active companies
   ```

2. **Batch Processing**:
   ```python
   # Analyze multiple companies at once
   @app.route('/semantic-analysis/batch', methods=['POST'])
   def batch_generate_analysis():
       company_ids = request.json.get('company_ids', [])
       # Process all companies
   ```

3. **Webhook Notifications**:
   ```python
   # Notify when analysis completes
   # Useful for long-running analyses
   ```

## Example Frontend Code

### React Component (Semantic Analysis Dashboard)

```javascript
import React, { useEffect, useState } from 'react';
import { Radar } from 'react-chartjs-2';

function SemanticAnalysisDashboard({ companyId }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAnalysis() {
      try {
        const response = await fetch(`/semantic-analysis/${companyId}`);
        const data = await response.json();
        setAnalysis(data);
      } catch (error) {
        console.error('Failed to load analysis:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadAnalysis();
  }, [companyId]);

  if (loading) return <div>Analyzing reviews...</div>;
  if (!analysis) return <div>No analysis available</div>;

  const radarData = {
    labels: analysis.radar_data.radar_points.map(p => p.topic),
    datasets: [{
      label: 'Sentiment Score',
      data: analysis.radar_data.radar_points.map(p => p.score),
      backgroundColor: 'rgba(54, 162, 235, 0.2)',
      borderColor: 'rgba(54, 162, 235, 1)',
    }]
  };

  return (
    <div className="semantic-analysis-dashboard">
      {/* Business Type Badge */}
      <div className="business-type-badge">
        <span className="icon">🏢</span>
        <span className="type">{analysis.analysis.business_type}</span>
      </div>

      {/* Sentiment Radar Chart */}
      <div className="semantic-radar">
        <h3>Sentiment Radar</h3>
        <Radar 
          data={radarData} 
          options={{ 
            scale: { min: 0, max: 5 },
            plugins: {
              legend: { display: true }
            }
          }} 
        />
      </div>

      {/* Topics with Keywords */}
      <div className="topics-list">
        <h3>Analysis by Topic</h3>
        {analysis.analysis.topics.map((topic, idx) => (
          <div key={idx} className="topic-card">
            <div className="topic-header">
              <h4>{topic.name}</h4>
              <span className="sentiment-score">{topic.sentiment_score}/5.0</span>
            </div>
            
            {/* Keywords */}
            {topic.keywords && topic.keywords.length > 0 && (
              <div className="keywords">
                {topic.keywords.map((keyword, i) => (
                  <span key={i} className="keyword-tag">{keyword}</span>
                ))}
              </div>
            )}
            
            {/* Sentiment Breakdown */}
            <div className="sentiment-bar">
              <div className="positive" style={{width: `${(topic.positive_count / (topic.positive_count + topic.neutral_count + topic.negative_count)) * 100}%`}}>
                {topic.positive_count}
              </div>
              <div className="neutral" style={{width: `${(topic.neutral_count / (topic.positive_count + topic.neutral_count + topic.negative_count)) * 100}%`}}>
                {topic.neutral_count}
              </div>
              <div className="negative" style={{width: `${(topic.negative_count / (topic.positive_count + topic.neutral_count + topic.negative_count)) * 100}%`}}>
                {topic.negative_count}
              </div>
            </div>
            
            {/* Review Excerpts */}
            <div className="review-excerpts">
              {topic.reviews.slice(0, 3).map((review, i) => (
                <div key={i} className={`review-excerpt ${review.sentiment}`}>
                  <p>"{review.excerpt}"</p>
                  <small>{review.reviewer_name} - {review.rating}★</small>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SemanticAnalysisDashboard;
```

### CSS Styling Example

```css
.business-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  background: #f0f0f0;
  border-radius: 20px;
  margin-bottom: 20px;
}

.keyword-tag {
  display: inline-block;
  padding: 4px 12px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 12px;
  margin: 4px;
  font-size: 0.875rem;
}

.sentiment-bar {
  display: flex;
  height: 30px;
  border-radius: 4px;
  overflow: hidden;
  margin: 10px 0;
}

.sentiment-bar .positive { background: #4caf50; color: white; }
.sentiment-bar .neutral { background: #ff9800; color: white; }
.sentiment-bar .negative { background: #f44336; color: white; }

.review-excerpt {
  padding: 12px;
  margin: 8px 0;
  border-left: 3px solid #ddd;
  background: #f9f9f9;
}

.review-excerpt.positive { border-left-color: #4caf50; }
.review-excerpt.neutral { border-left-color: #ff9800; }
.review-excerpt.negative { border-left-color: #f44336; }
```

## Support

For detailed API documentation, see `API_DOCUMENTATION.md`.

For questions or issues:
1. Check the logs in `app/logs/`
2. Review error messages in server output
3. Verify database tables were created: `semantic_analysis`

## Summary

### ✅ Version 2.0 - Fully Implemented

**Core Features:**
- ✨ **Dynamic business type detection** - Automatically identifies your industry
- ✨ **Intelligent topic generation** - Creates relevant topics for your business type
- ✨ **Keyword extraction** - Identifies important terms from customer feedback
- ✨ **Industry-specific analysis** - Tailored insights for restaurants, hotels, tours, retail, and more
- 💾 Database model for storing analysis results
- 🤖 AI-powered semantic analyzer using OpenAI GPT-4o-mini
- 🔌 3 REST API endpoints for analysis operations
- 📚 Complete API documentation

### 🎯 Ready to Use

**API Endpoints:**
- Generate analysis: `POST /semantic-analysis/{company_id}/generate`
- Retrieve analysis: `GET /semantic-analysis/{company_id}`
- Get summary: `GET /semantic-analysis/{company_id}/summary`

**Response Includes:**
- `business_type` - Detected industry category
- `topics` - 5 dynamically generated topics with sentiment scores
- `keywords` - Extracted keywords per topic
- `radar_data` - Data for visualization
- `reviews` - Categorized review excerpts

### 📝 Next Steps for Frontend

**Essential Components:**
1. **Business Type Display** - Show detected business type with an icon/badge
2. **Sentiment Radar Chart** - Pentagon chart with 5 dynamic topics
3. **Semantic Counts** - Horizontal stacked bars (positive/neutral/negative)
4. **Keyword Tags** - Display extracted keywords as clickable tags
5. **Review Excerpts** - List of categorized reviews with sentiment

**Enhanced Features:**
- Filter by review profile, platform, language, date range
- Search through topics and keywords
- Export analysis as PDF or CSV
- Scheduled regeneration for active companies
- Comparison across time periods

### 🚀 What Makes Version 2.0 Special

| Feature | Benefit |
|---------|---------|
| **Auto-Detection** | No manual setup needed for different business types |
| **Dynamic Topics** | Always relevant to your specific industry |
| **Keywords** | Quick insights into what customers are saying |
| **Scalability** | Works for any business type automatically |
| **Accuracy** | Better categorization with industry-specific AI prompts |

### 💡 Use Cases by Business Type

- **Restaurants**: Track food quality, service speed, ambiance issues
- **Hotels**: Monitor room cleanliness, staff service, amenity satisfaction
- **Tours**: Analyze guide performance, experience quality, organization
- **Retail**: Understand product quality, customer service, store experience
- **Services**: Evaluate service quality, staff expertise, professionalism

The semantic analysis backend (Version 2.0) is complete with dynamic business detection and ready for frontend integration! 🎉

---

## Version History

### Version 2.0 (October 28, 2025) - Current
- ✨ Added dynamic business type detection
- ✨ Added intelligent topic generation based on business type
- ✨ Added keyword extraction per topic
- 📝 Updated response structure to include `business_type`
- 📝 Updated response structure to include `keywords` array
- 🎯 Support for 9 business type categories
- ⚡ Optimized for industry-specific analysis
- 📊 Enhanced sentiment scoring accuracy

### Version 1.1 (October 27, 2025)
- Initial semantic analysis implementation
- Fixed 5 topics for all businesses
- Basic sentiment classification
- Radar chart data generation
- Database caching

---

**Current Version:** 2.0  
**Last Updated:** October 28, 2025

