import json
from openai import OpenAI
import os
from datetime import datetime

class SemanticAnalyzer:
    # Default topics as fallback
    DEFAULT_TOPICS = [
        "Tour Guide/Host Performance",
        "Tour Content and Experience",
        "Organization & Management",
        "Atmosphere and Special Effects",
        "Value for Money"
    ]
    
    def __init__(self):
        self.open_ai_key = os.getenv('OPEN_AI_KEY')
        # Add timeout to OpenAI client (60 seconds)
        self.client = OpenAI(
            api_key=self.open_ai_key,
            timeout=60.0,  # 60 second timeout
            max_retries=2  # Retry failed requests
        ) if self.open_ai_key else None
        self.detected_business_type = None
        self.dynamic_topics = None
    
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
        
        # Step 1: Detect business type
        self.detected_business_type = self._detect_business_type(company_name, formatted_reviews)
        
        # Step 2: Generate topics based on business type
        self.dynamic_topics = self._generate_topics_for_business_type(self.detected_business_type)
        
        # Step 3: Perform semantic analysis using OpenAI with dynamic topics
        analysis_result = self._perform_openai_analysis(company_name, formatted_reviews)
        
        # Add business type to result
        analysis_result['business_type'] = self.detected_business_type
        
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
    
    def _detect_business_type(self, company_name, formatted_reviews):
        """
        Detect the business type based on company name and review content
        
        Args:
            company_name: Name of the company
            formatted_reviews: List of formatted review dicts
            
        Returns:
            str: Detected business type
        """
        # Sample reviews for detection (use first 30 for efficiency)
        sample_reviews = formatted_reviews[:30]
        
        reviews_text = "\n".join([
            f"Review {r['index']}: {r['comment'][:200]}"  # First 200 chars
            for r in sample_reviews
        ])
        
        prompt = f"""Analyze the following information and determine the business type:

        Company Name: {company_name}

        Sample Reviews:
        {reviews_text}

        Based on the company name and review content, identify the PRIMARY business type from the following categories:
        - Tour/Activity (walking tours, guided tours, experiences, attractions)
        - Restaurant/Dining (restaurants, cafes, bars, food establishments)
        - Hotel/Accommodation (hotels, hostels, vacation rentals, lodging)
        - Retail/Shopping (stores, shops, boutiques)
        - Service/Professional (salons, spas, repair services, professional services)
        - Entertainment/Recreation (theaters, museums, entertainment venues)
        - Transportation (car rentals, taxi services, shuttle services)
        - Healthcare (clinics, hospitals, medical services)
        - Other (if none of the above fit well)

        Return a JSON object with this structure:
        {{
            "business_type": "<detected type>",
            "confidence": "<high|medium|low>",
            "reasoning": "<brief explanation>"
        }}

        Choose the MOST SPECIFIC category that fits. Be concise."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at categorizing businesses based on their name and customer reviews. Provide structured JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("business_type", "Tour/Activity")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Business type detection failed: {error_msg}")
            # Log specific errors but continue with fallback
            if "502" in error_msg or "Bad Gateway" in error_msg:
                print("OpenAI returned 502 Bad Gateway - using fallback business type")
            elif "timeout" in error_msg.lower():
                print("OpenAI request timed out - using fallback business type")
            return "Tour/Activity"  # Default fallback
    
    def _generate_topics_for_business_type(self, business_type):
        """
        Generate relevant topics based on the detected business type
        
        Args:
            business_type: The detected business type
            
        Returns:
            list: List of topic names and their descriptions
        """
        prompt = f"""Generate 5 specific review analysis topics for a "{business_type}" business.

        Requirements:
        - Topics should be highly relevant to "{business_type}" businesses
        - Topics should be distinct and non-overlapping
        - Topics should cover the most important aspects customers care about
        - Always include "Value for Money" as one of the 5 topics
        - Topics should be specific enough to categorize reviews effectively

        Return a JSON object with this structure:
        {{
            "topics": [
                {{
                    "name": "<topic name>",
                    "description": "<what this topic covers>",
                    "keywords": ["<example keyword 1>", "<example keyword 2>", "<example keyword 3>"]
                }},
                ... (5 topics total)
            ]
        }}

        Be specific to the business type. For example:
        - For restaurants: Food Quality, Service, Ambiance, Menu Variety, Value for Money
        - For hotels: Room Quality, Staff Service, Cleanliness, Amenities, Value for Money
        - For tours: Guide Performance, Experience Content, Organization, Atmosphere, Value for Money"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at defining relevant review analysis categories for different business types. Provide structured JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            topics_data = result.get("topics", [])
            
            # Extract topic names and descriptions
            topics = []
            for topic in topics_data:
                topics.append({
                    "name": topic.get("name", ""),
                    "description": topic.get("description", ""),
                    "keywords": topic.get("keywords", [])
                })
            
            # Ensure we have exactly 5 topics
            if len(topics) < 5:
                topics.extend(self._get_default_topics_structure()[len(topics):5])
            
            return topics[:5]
            
        except Exception as e:
            error_msg = str(e)
            print(f"Topic generation failed: {error_msg}")
            # Log specific errors but continue with fallback
            if "502" in error_msg or "Bad Gateway" in error_msg:
                print("OpenAI returned 502 Bad Gateway - using fallback topics")
            elif "timeout" in error_msg.lower():
                print("OpenAI request timed out - using fallback topics")
            return self._get_default_topics_structure()
    
    def _get_default_topics_structure(self):
        """Get default topics with structure"""
        return [
            {
                "name": "Tour Guide/Host Performance",
                "description": "Comments about guides, hosts, staff friendliness, knowledge, professionalism",
                "keywords": ["guide", "host", "staff", "friendly", "knowledgeable"]
            },
            {
                "name": "Tour Content and Experience",
                "description": "Comments about what they saw, did, learned, activities, attractions",
                "keywords": ["experience", "content", "activities", "attractions", "learned"]
            },
            {
                "name": "Organization & Management",
                "description": "Comments about booking, timing, scheduling, logistics, planning",
                "keywords": ["booking", "timing", "organization", "logistics", "planning"]
            },
            {
                "name": "Atmosphere and Special Effects",
                "description": "Comments about ambiance, mood, setting, special features",
                "keywords": ["atmosphere", "ambiance", "setting", "mood", "special"]
            },
            {
                "name": "Value for Money",
                "description": "Comments about pricing, worth, value, cost-effectiveness",
                "keywords": ["price", "value", "worth", "cost", "money"]
            }
        ]
    
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
            error_msg = str(e)
            # Provide more specific error messages
            if "502" in error_msg or "Bad Gateway" in error_msg:
                raise Exception(f"OpenAI API is temporarily unavailable (502 Bad Gateway). Please try again in a few moments.")
            elif "timeout" in error_msg.lower():
                raise Exception(f"OpenAI API request timed out. Try again or reduce the number of reviews.")
            elif "503" in error_msg or "Service Unavailable" in error_msg:
                raise Exception(f"OpenAI API is temporarily unavailable (503). Please try again later.")
            elif "429" in error_msg or "rate_limit" in error_msg.lower():
                raise Exception(f"OpenAI API rate limit exceeded. Please wait and try again.")
            else:
                raise Exception(f"OpenAI analysis failed: {error_msg}")
    
    def _create_analysis_prompt(self, company_name, formatted_reviews):
        """Create a detailed prompt for OpenAI analysis using dynamic topics"""
        
        reviews_text = "\n".join([
            f"Review {r['index']} (ID: {r['id']}):\n"
            f"  Name: {r['name']}\n"
            f"  Rating: {r['rating']} stars\n"
            f"  Date: {r['date']}\n"
            f"  Comment: {r['comment']}\n"
            for r in formatted_reviews
        ])
        
        # Build topics list and guidelines from dynamic topics
        topics_list = "\n".join([
            f"                {i+1}. {topic['name']}"
            for i, topic in enumerate(self.dynamic_topics)
        ])
        
        topics_guidelines = "\n".join([
            f"                - \"{topic['name']}\": {topic['description']}"
            for topic in self.dynamic_topics
        ])
        
        # Build example structure with actual topic names
        topics_json_example = ",\n".join([
            f"""                    {{
                    "name": "{topic['name']}",
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
                    }}"""
            for topic in self.dynamic_topics
        ])
        
        prompt = f"""Analyze the following customer reviews for {company_name} (a {self.detected_business_type} business) and categorize them into these EXACT topics:

                {topics_list}

                For each review, determine:
                1. Which topic(s) it relates to (a review can relate to multiple topics)
                2. The sentiment for each topic: positive, neutral, or negative

                Guidelines for topics:
                {topics_guidelines}

                Sentiment Classification:
                - Positive: 4-5 stars OR clearly positive language
                - Negative: 1-2 stars OR clearly negative language
                - Neutral: 3 stars OR mixed/neutral language

                Reviews:
                {reviews_text}

                Return a JSON object with this EXACT structure:
                {{
                "topics": [
                    {topics_json_example}
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
        for topic in self.dynamic_topics:
            if topic["name"] not in existing_topics:
                structured["topics"].append({
                    "name": topic["name"],
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
        # Use default topics if dynamic topics haven't been generated
        topics_to_use = self.dynamic_topics if self.dynamic_topics else self._get_default_topics_structure()
        
        return {
            "total_reviews": 0,
            "total_mentions": 0,
            "business_type": self.detected_business_type or "Unknown",
            "topics": [
                {
                    "name": topic["name"] if isinstance(topic, dict) else topic,
                    "review_count": 0,
                    "mention_count": 0,
                    "positive_count": 0,
                    "neutral_count": 0,
                    "negative_count": 0,
                    "sentiment_score": 0,
                    "keywords": [],
                    "reviews": []
                }
                for topic in topics_to_use
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

