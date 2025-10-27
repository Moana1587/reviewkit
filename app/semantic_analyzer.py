import json
from openai import OpenAI
import os
from datetime import datetime

class SemanticAnalyzer:
    TOPICS = [
        "Tour Guide/Host Performance",
        "Tour Content and Experience",
        "Organization & Management",
        "Atmosphere and Special Effects",
        "Value for Money"
    ]
    
    def __init__(self):
        self.open_ai_key = os.getenv('OPEN_AI_KEY')
        self.client = OpenAI(api_key=self.open_ai_key) if self.open_ai_key else None
    
    def analyze_reviews(self, company_name, reviews, max_reviews=300):
        """
        Analyze reviews and categorize them into topics with sentiment analysis
        
        Args:
            company_name: Name of the company
            reviews: List of review tuples (display_name, rating, comment, create_time, review_id)
            max_reviews: Maximum number of reviews to analyze
            
        Returns:
            dict: Analysis results with topics, sentiments, and review excerpts
        """
        if not self.client:
            raise Exception("OpenAI API key not configured")
        
        if not reviews:
            return self._empty_analysis(company_name)
        
        # Limit reviews for performance
        reviews_to_analyze = reviews[:max_reviews] if len(reviews) > max_reviews else reviews
        
        # Format reviews for analysis
        formatted_reviews = self._format_reviews_for_analysis(reviews_to_analyze)
        
        # Perform semantic analysis using OpenAI
        analysis_result = self._perform_openai_analysis(company_name, formatted_reviews)
        
        return analysis_result
    
    def _format_reviews_for_analysis(self, reviews):
        """Format reviews into a structured text for OpenAI analysis"""
        formatted = []
        for idx, review in enumerate(reviews, 1):
            display_name, rating, comment, create_time, review_id = review
            formatted.append({
                "id": review_id,
                "index": idx,
                "name": display_name,
                "rating": rating,
                "comment": comment,
                "date": str(create_time) if create_time else "N/A"
            })
        return formatted
    
    def _perform_openai_analysis(self, company_name, formatted_reviews):
        """Use OpenAI to categorize and analyze reviews"""
        
        # Create the analysis prompt
        prompt = self._create_analysis_prompt(company_name, formatted_reviews)
        
        try:
            # Call OpenAI API with GPT-4 for better analysis
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4 mini for cost efficiency
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing customer reviews and categorizing them into specific topics with sentiment analysis. You provide structured JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Validate and structure the result
            return self._structure_analysis_result(result, formatted_reviews)
            
        except Exception as e:
            raise Exception(f"OpenAI analysis failed: {str(e)}")
    
    def _create_analysis_prompt(self, company_name, formatted_reviews):
        """Create a detailed prompt for OpenAI analysis"""
        
        reviews_text = "\n".join([
            f"Review {r['index']} (ID: {r['id']}):\n"
            f"  Name: {r['name']}\n"
            f"  Rating: {r['rating']} stars\n"
            f"  Date: {r['date']}\n"
            f"  Comment: {r['comment']}\n"
            for r in formatted_reviews
        ])
        
        prompt = f"""Analyze the following customer reviews for {company_name} and categorize them into these EXACT topics:

                1. Tour Guide/Host Performance
                2. Tour Content and Experience
                3. Organization & Management
                4. Atmosphere and Special Effects
                5. Value for Money

                For each review, determine:
                1. Which topic(s) it relates to (a review can relate to multiple topics)
                2. The sentiment for each topic: positive, neutral, or negative

                Guidelines:
                - "Tour Guide/Host Performance": Comments about guides, hosts, staff friendliness, knowledge, professionalism
                - "Tour Content and Experience": Comments about what they saw, did, learned, activities, attractions
                - "Organization & Management": Comments about booking, timing, scheduling, logistics, planning
                - "Atmosphere and Special Effects": Comments about ambiance, mood, setting, special features
                - "Value for Money": Comments about pricing, worth, value, cost-effectiveness

                Sentiment Classification:
                - Positive: 4-5 stars OR clearly positive language
                - Negative: 1-2 stars OR clearly negative language
                - Neutral: 3 stars OR mixed/neutral language

                Reviews:
                {reviews_text}

                Return a JSON object with this EXACT structure:
                {{
                "topics": [
                    {{
                    "name": "Tour Guide/Host Performance",
                    "review_count": <number of reviews mentioning this topic>,
                    "mention_count": <total mentions across reviews>,
                    "positive_count": <count>,
                    "neutral_count": <count>,
                    "negative_count": <count>,
                    "reviews": [
                        {{
                        "review_id": <review ID>,
                        "review_index": <review number>,
                        "reviewer_name": "<name>",
                        "rating": <stars>,
                        "date": "<date>",
                        "excerpt": "<relevant quote from review>",
                        "sentiment": "positive|neutral|negative"
                        }}
                    ]
                    }},
                    ... (repeat for all 5 topics)
                ]
                }}

                Include only reviews that actually mention each topic. The excerpt should be the most relevant sentence or phrase from the review for that topic.
                
                Note: Sentiment score will be calculated automatically using the formula: 
                ((positive_count - negative_count + neutral_count * 0.5) / total) * 5"""
                        
        return prompt
    
    def _structure_analysis_result(self, raw_result, formatted_reviews):
        """Structure and validate the OpenAI analysis result"""
        
        structured = {
            "total_reviews": len(formatted_reviews),
            "total_mentions": 0,
            "topics": []
        }
        
        # Process each topic
        for topic_data in raw_result.get("topics", []):
            positive_count = topic_data.get("positive_count", 0)
            neutral_count = topic_data.get("neutral_count", 0)
            negative_count = topic_data.get("negative_count", 0)
            
            # Calculate sentiment score using the new formula
            total = positive_count + neutral_count + negative_count
            if total > 0:
                sentiment_score = ((positive_count - negative_count + neutral_count * 0.5) / total) * 5
                # Ensure score is between 0 and 5
                sentiment_score = max(0, min(5, sentiment_score))
            else:
                sentiment_score = 0
            
            # Extract keywords from reviews
            keywords = self._extract_keywords_from_reviews(topic_data.get("reviews", []))
            
            topic = {
                "name": topic_data.get("name", "Unknown"),
                "review_count": topic_data.get("review_count", 0),
                "mention_count": topic_data.get("mention_count", 0),
                "positive_count": positive_count,
                "neutral_count": neutral_count,
                "negative_count": negative_count,
                "sentiment_score": round(sentiment_score, 2),
                "keywords": keywords,
                "reviews": topic_data.get("reviews", [])
            }
            structured["topics"].append(topic)
            structured["total_mentions"] += topic["mention_count"]
        
        # Ensure all 5 topics are present
        existing_topics = {t["name"] for t in structured["topics"]}
        for topic_name in self.TOPICS:
            if topic_name not in existing_topics:
                structured["topics"].append({
                    "name": topic_name,
                    "review_count": 0,
                    "mention_count": 0,
                    "positive_count": 0,
                    "neutral_count": 0,
                    "negative_count": 0,
                    "sentiment_score": 0,
                    "keywords": [],
                    "reviews": []
                })
        
        return structured
    
    def _extract_keywords_from_reviews(self, reviews):
        """Extract keywords from review excerpts"""
        import re
        from collections import Counter
        
        # Common words to exclude
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'his', 'her', 'its', 'our', 'their', 'am', 'to', 'from', 'tour', 'tours'
        }
        
        words = []
        for review in reviews:
            excerpt = review.get('excerpt', '')
            # Extract words (3+ characters only)
            review_words = re.findall(r'\b[a-z]{3,}\b', excerpt.lower())
            # Filter out stop words
            words.extend([w for w in review_words if w not in stop_words])
        
        # Count and return top 10 keywords
        if words:
            counter = Counter(words)
            return [word for word, count in counter.most_common(10)]
        
        return []
    
    def _empty_analysis(self, company_name):
        """Return empty analysis structure when no reviews exist"""
        return {
            "total_reviews": 0,
            "total_mentions": 0,
            "topics": [
                {
                    "name": topic,
                    "review_count": 0,
                    "mention_count": 0,
                    "positive_count": 0,
                    "neutral_count": 0,
                    "negative_count": 0,
                    "sentiment_score": 0,
                    "keywords": [],
                    "reviews": []
                }
                for topic in self.TOPICS
            ]
        }
    
    def calculate_radar_data(self, analysis_result):
        """
        Calculate radar chart data from analysis results
        
        Returns:
            dict: Radar data with normalized scores for each topic
        """
        radar_data = []
        
        for topic in analysis_result.get("topics", []):
            # Calculate a score based on sentiment (0-5 scale)
            # Formula: (positive * 1 - negative * 1 + neutral * 0.5) / total * 5
            total = topic["positive_count"] + topic["neutral_count"] + topic["negative_count"]
            if total > 0:
                score = ((topic["positive_count"] - topic["negative_count"] + topic["neutral_count"] * 0.5) / total) * 5
                # Ensure score is between 0 and 5
                score = max(0, min(5, score))
            else:
                score = 0
            
            radar_data.append({
                "topic": topic["name"],
                "score": round(score, 2),
             })
        
        return {"radar_points": radar_data}

