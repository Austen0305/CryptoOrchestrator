"""
Sentiment AI Service - News and social media sentiment analysis
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import asyncio
import httpx
import numpy as np

logger = logging.getLogger(__name__)

# Try importing sentiment analysis libraries
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER sentiment not available; sentiment analysis will be limited.")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available; sentiment analysis will be limited.")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available; advanced sentiment analysis will be limited.")


class SentimentScore(BaseModel):
    """Sentiment score"""
    compound: float  # Overall sentiment (-1 to 1)
    positive: float  # Positive sentiment (0 to 1)
    neutral: float  # Neutral sentiment (0 to 1)
    negative: float  # Negative sentiment (0 to 1)
    confidence: float  # Confidence score (0 to 1)


class NewsArticle(BaseModel):
    """News article"""
    title: str
    content: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    sentiment: Optional[SentimentScore] = None


class SocialMediaPost(BaseModel):
    """Social media post"""
    text: str
    platform: str  # 'twitter', 'reddit', etc.
    author: Optional[str] = None
    created_at: datetime
    likes: int = 0
    shares: int = 0
    sentiment: Optional[SentimentScore] = None


class AggregatedSentiment(BaseModel):
    """Aggregated sentiment across multiple sources"""
    symbol: str
    overall_score: float  # -1 to 1
    news_score: float
    social_score: float
    confidence: float
    sample_size: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SentimentAIService:
    """Service for sentiment analysis of news and social media"""
    
    def __init__(self):
        # Initialize sentiment analyzers
        self.vader_analyzer = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
        self.transformer_pipeline = None
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.transformer_pipeline = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    return_all_scores=True
                )
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
        
        logger.info("Sentiment AI Service initialized")
    
    def analyze_text(self, text: str, method: str = "vader") -> SentimentScore:
        """Analyze sentiment of text"""
        try:
            if method == "vader" and self.vader_analyzer:
                scores = self.vader_analyzer.polarity_scores(text)
                return SentimentScore(
                    compound=scores['compound'],
                    positive=scores['pos'],
                    neutral=scores['neu'],
                    negative=scores['neg'],
                    confidence=abs(scores['compound'])
                )
            
            elif method == "textblob" and TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                subjectivity = blob.sentiment.subjectivity
                
                # Convert polarity (-1 to 1) to positive/negative scores
                if polarity > 0:
                    positive = polarity
                    negative = 0.0
                else:
                    positive = 0.0
                    negative = -polarity
                
                neutral = 1.0 - abs(polarity)
                
                return SentimentScore(
                    compound=polarity,
                    positive=positive,
                    neutral=neutral,
                    negative=negative,
                    confidence=1.0 - subjectivity
                )
            
            elif method == "transformer" and self.transformer_pipeline:
                results = self.transformer_pipeline(text)
                
                # Parse transformer results
                positive_score = 0.0
                negative_score = 0.0
                
                for result in results:
                    label = result['label'].lower()
                    score = result['score']
                    
                    if 'positive' in label:
                        positive_score = score
                    elif 'negative' in label:
                        negative_score = score
                
                compound = positive_score - negative_score
                neutral = 1.0 - positive_score - negative_score
                
                return SentimentScore(
                    compound=compound,
                    positive=positive_score,
                    neutral=max(neutral, 0.0),
                    negative=negative_score,
                    confidence=max(positive_score, negative_score)
                )
            
            else:
                # Fallback: simple keyword-based sentiment
                return self._simple_sentiment(text)
        
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return SentimentScore(
                compound=0.0,
                positive=0.33,
                neutral=0.34,
                negative=0.33,
                confidence=0.0
            )
    
    def _simple_sentiment(self, text: str) -> SentimentScore:
        """Simple keyword-based sentiment analysis fallback"""
        positive_keywords = ['bullish', 'moon', 'pump', 'rally', 'surge', 'gain', 'profit', 'up', 'buy']
        negative_keywords = ['bearish', 'crash', 'dump', 'drop', 'fall', 'loss', 'down', 'sell', 'panic']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        total_count = positive_count + negative_count
        
        if total_count == 0:
            return SentimentScore(
                compound=0.0,
                positive=0.33,
                neutral=0.34,
                negative=0.33,
                confidence=0.0
            )
        
        compound = (positive_count - negative_count) / total_count
        
        positive = positive_count / total_count if positive_count > 0 else 0.0
        negative = negative_count / total_count if negative_count > 0 else 0.0
        neutral = 1.0 - positive - negative
        
        return SentimentScore(
            compound=compound,
            positive=positive,
            neutral=max(neutral, 0.0),
            negative=negative,
            confidence=abs(compound)
        )
    
    def analyze_news_article(self, article: NewsArticle, method: str = "vader") -> NewsArticle:
        """Analyze sentiment of news article"""
        try:
            # Combine title and content for analysis
            text = f"{article.title}. {article.content}"
            sentiment = self.analyze_text(text, method)
            
            article.sentiment = sentiment
            return article
        
        except Exception as e:
            logger.error(f"Failed to analyze news article: {e}")
            return article
    
    def analyze_social_post(self, post: SocialMediaPost, method: str = "vader") -> SocialMediaPost:
        """Analyze sentiment of social media post"""
        try:
            sentiment = self.analyze_text(post.text, method)
            post.sentiment = sentiment
            return post
        
        except Exception as e:
            logger.error(f"Failed to analyze social post: {e}")
            return post
    
    def aggregate_sentiment(
        self,
        symbol: str,
        news_articles: List[NewsArticle],
        social_posts: List[SocialMediaPost],
        method: str = "vader"
    ) -> AggregatedSentiment:
        """Aggregate sentiment from multiple sources"""
        try:
            # Analyze news articles
            news_scores = []
            for article in news_articles:
                analyzed = self.analyze_news_article(article, method)
                if analyzed.sentiment:
                    news_scores.append(analyzed.sentiment.compound)
            
            # Analyze social posts (weighted by engagement)
            social_scores = []
            total_engagement = 0
            
            for post in social_posts:
                analyzed = self.analyze_social_post(post, method)
                if analyzed.sentiment:
                    engagement = post.likes + post.shares + 1  # +1 to avoid zero
                    weighted_score = analyzed.sentiment.compound * engagement
                    social_scores.append(weighted_score)
                    total_engagement += engagement
            
            # Calculate aggregated scores
            news_score = np.mean(news_scores) if news_scores else 0.0
            social_score = (sum(social_scores) / total_engagement) if total_engagement > 0 else 0.0
            
            # Weighted combination (70% news, 30% social)
            overall_score = 0.7 * news_score + 0.3 * social_score
            
            # Calculate confidence
            sample_size = len(news_articles) + len(social_posts)
            confidence = min(sample_size / 100.0, 1.0)  # Max confidence at 100+ samples
            
            return AggregatedSentiment(
                symbol=symbol,
                overall_score=overall_score,
                news_score=news_score,
                social_score=social_score,
                confidence=confidence,
                sample_size=sample_size
            )
        
        except Exception as e:
            logger.error(f"Failed to aggregate sentiment: {e}")
            return AggregatedSentiment(
                symbol=symbol,
                overall_score=0.0,
                news_score=0.0,
                social_score=0.0,
                confidence=0.0,
                sample_size=0
            )
    
    async def fetch_news_articles(
        self,
        symbol: str,
        api_key: Optional[str] = None,
        limit: int = 10
    ) -> List[NewsArticle]:
        """Fetch news articles for a symbol (placeholder - integrate with news API)"""
        # This would integrate with NewsAPI, Alpha Vantage, etc.
        # For now, return empty list
        logger.warning("News API integration not yet implemented")
        return []
    
    async def fetch_social_posts(
        self,
        symbol: str,
        platform: str = "twitter",
        limit: int = 50
    ) -> List[SocialMediaPost]:
        """Fetch social media posts for a symbol (placeholder - integrate with social APIs)"""
        # This would integrate with Twitter API, Reddit API, etc.
        # For now, return empty list
        logger.warning(f"Social media API integration not yet implemented for {platform}")
        return []


# Global service instance
sentiment_ai_service = SentimentAIService()
