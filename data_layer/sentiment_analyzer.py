"""
Sentiment Analysis & News Module
Analyzes financial news and sentiment for companies
Supports both real news APIs and simulated data for demo purposes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json


class FinancialSentimentAnalyzer:
    """
    Analyzes financial news and sentiment
    Integrates with financial news sources
    """
    
    # Sample financial news templates for demonstration
    SAMPLE_NEWS_TEMPLATES = {
        'positive': [
            "{company} beats Q{quarter} earnings expectations with {growth}% revenue growth",
            "{company} announces major partnership with industry leader",
            "{company} stock reaches new 52-week high amid strong earnings",
            "{company} launches innovative {product} gaining analyst praise",
            "{company} increases dividend by {pct}% signaling confidence in growth",
            "Analysts upgrade {company} rating to Buy on strong fundamentals",
            "{company} expands into {market} market in strategic move",
            "Institutional investors increase position in {company} stock",
        ],
        'negative': [
            "{company} misses earnings expectations, stock falls {pct}%",
            "{company} faces regulatory scrutiny in latest investigation",
            "{company} reports declining margins amid rising costs",
            "Major client drops {company} amid competitive pressures",
            "{company} issues guidance cut for next quarter",
            "Analysts downgrade {company} citing market challenges",
            "{company} faces supply chain disruptions",
            "Legal issues impact {company} stock price",
        ],
        'neutral': [
            "{company} maintains market position in steady trading",
            "{company} announces quarterly earnings release date",
            "{company} updates investor relations information",
            "{company} wins industry recognition award",
            "{company} expands R&D team with new hires",
            "{company} participates in financial conference",
            "{company} releases sustainability report",
            "{company} updates product roadmap for upcoming year",
        ]
    }
    
    def __init__(self):
        self.sentiment_data = {}
        self.news_data = {}
    
    def analyze_sentiment_from_text(self, text: str) -> Dict:
        """
        Analyze sentiment from financial text
        
        Args:
            text: Financial text to analyze
        
        Returns:
            Dictionary with sentiment scores
        """
        # Simple keyword-based sentiment analysis
        positive_keywords = ['beat', 'gain', 'surge', 'soar', 'upgrade', 'rally', 
                           'outperform', 'growth', 'profit', 'strength', 'strong']
        negative_keywords = ['miss', 'decline', 'fall', 'plunge', 'downgrade', 'weak',
                           'loss', 'challenge', 'risk', 'threat', 'downgra']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        total = positive_count + negative_count
        
        if total == 0:
            sentiment_score = 0.5  # Neutral
        else:
            sentiment_score = positive_count / total
        
        return {
            'sentiment_score': sentiment_score,
            'positive_signals': positive_count,
            'negative_signals': negative_count,
            'sentiment_label': 'Positive' if sentiment_score > 0.6 else 
                              'Negative' if sentiment_score < 0.4 else 'Neutral'
        }
    
    def generate_sample_news_dataset(self, companies: List[str], days: int = 30) -> List[Dict]:
        """
        Generate sample financial news for demonstration
        
        Args:
            companies: List of company tickers
            days: Number of days to generate news for
        
        Returns:
            List of news articles with sentiment
        """
        news_articles = []
        
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            
            for company in companies:
                # Randomly select news type
                sentiment_type = np.random.choice(['positive', 'negative', 'neutral'], 
                                                 p=[0.4, 0.3, 0.3])
                
                templates = self.SAMPLE_NEWS_TEMPLATES[sentiment_type]
                template = np.random.choice(templates)
                
                # Fill template with company-specific data
                article_text = template.format(
                    company=company,
                    product='new device' if sentiment_type == 'positive' else 'service',
                    market='emerging' if sentiment_type == 'positive' else 'domestic',
                    growth=np.random.randint(15, 45),
                    pct=np.random.randint(5, 25),
                    quarter=np.random.randint(1, 5),
                )
                
                # Analyze sentiment
                sentiment = self.analyze_sentiment_from_text(article_text)
                
                article = {
                    'ticker': company,
                    'date': date.isoformat(),
                    'headline': article_text,
                    'sentiment_score': sentiment['sentiment_score'],
                    'sentiment_label': sentiment['sentiment_label'],
                    'positive_signals': sentiment['positive_signals'],
                    'negative_signals': sentiment['negative_signals'],
                    'source': np.random.choice(['Bloomberg', 'Reuters', 'Financial Times', 'WSJ', 'MarketWatch']),
                    'relevance_score': round(np.random.uniform(0.6, 1.0), 2),
                }
                
                news_articles.append(article)
        
        return news_articles
    
    def calculate_sentiment_metrics_by_company(self, news_articles: List[Dict]) -> pd.DataFrame:
        """
        Calculate aggregated sentiment metrics by company
        
        Args:
            news_articles: List of news articles
        
        Returns:
            DataFrame with sentiment metrics per company
        """
        df = pd.DataFrame(news_articles)
        
        sentiment_summary = df.groupby('ticker').agg({
            'sentiment_score': ['mean', 'std', 'min', 'max'],
            'positive_signals': 'sum',
            'negative_signals': 'sum',
            'relevance_score': 'mean',
            'headline': 'count'
        }).round(3)
        
        # Flatten column names
        sentiment_summary.columns = [
            'avg_sentiment', 'sentiment_volatility', 'min_sentiment', 'max_sentiment',
            'total_positive_signals', 'total_negative_signals', 
            'avg_relevance', 'news_count'
        ]
        
        return sentiment_summary.reset_index()
    
    def calculate_sentiment_trend(self, news_articles: List[Dict], 
                                 ticker: str, window_days: int = 7) -> pd.DataFrame:
        """
        Calculate sentiment trend over time for a company
        
        Args:
            news_articles: List of news articles
            ticker: Company ticker
            window_days: Window for rolling average
        
        Returns:
            DataFrame with daily sentiment trend
        """
        df = pd.DataFrame(news_articles)
        df = df[df['ticker'] == ticker].copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # Group by date and calculate daily sentiment
        daily_sentiment = df.groupby('date').agg({
            'sentiment_score': 'mean',
            'headline': 'count',
            'positive_signals': 'sum',
            'negative_signals': 'sum',
        }).reset_index()
        
        daily_sentiment.columns = ['date', 'daily_sentiment', 'news_count', 
                                  'positive_signals', 'negative_signals']
        
        # Calculate rolling average
        daily_sentiment['sentiment_trend'] = (
            daily_sentiment['daily_sentiment'].rolling(window=window_days, min_periods=1).mean()
        )
        
        return daily_sentiment.sort_values('date', ascending=False)
    
    def get_sentiment_indicators(self, news_articles: List[Dict], 
                               ticker: str) -> Dict:
        """
        Get comprehensive sentiment indicators for a company
        
        Args:
            news_articles: List of news articles
            ticker: Company ticker
        
        Returns:
            Dictionary with sentiment indicators
        """
        df = pd.DataFrame(news_articles)
        company_news = df[df['ticker'] == ticker]
        
        if company_news.empty:
            return None
        
        positive_count = (company_news['sentiment_label'] == 'Positive').sum()
        negative_count = (company_news['sentiment_label'] == 'Negative').sum()
        neutral_count = (company_news['sentiment_label'] == 'Neutral').sum()
        
        indicators = {
            'avg_sentiment_score': round(company_news['sentiment_score'].mean(), 3),
            'sentiment_trend': 'Improving' if company_news.iloc[-7:]['sentiment_score'].mean() > 
                              company_news.iloc[-14:-7]['sentiment_score'].mean() else 'Declining',
            'positive_news_count': positive_count,
            'negative_news_count': negative_count,
            'neutral_news_count': neutral_count,
            'sentiment_distribution': {
                'positive': f"{positive_count/len(company_news)*100:.1f}%",
                'negative': f"{negative_count/len(company_news)*100:.1f}%",
                'neutral': f"{neutral_count/len(company_news)*100:.1f}%",
            },
            'latest_sentiment': company_news.iloc[-1]['sentiment_label'],
            'avg_relevance': round(company_news['relevance_score'].mean(), 2),
            'total_news_articles': len(company_news),
        }
        
        return indicators


class UnstructuredDataProcessor:
    """
    Processes unstructured financial data
    Handles text documents, PDFs, transcripts
    """
    
    def __init__(self):
        self.documents = []
        self.extracted_data = {}
    
    def extract_text_from_sample_documents(self, companies: List[str]) -> Dict[str, str]:
        """
        Extract sample text from financial documents
        
        Args:
            companies: List of company tickers
        
        Returns:
            Dictionary with extracted text per company
        """
        sample_documents = {
            'annual_report': "Our financial performance in 2024 showed strong growth with a 25% increase in revenue. "
                           "Operating margins improved due to operational efficiency initiatives. "
                           "We remain committed to sustainable growth and shareholder value creation.",
            
            'earnings_call': "Thank you for joining our earnings call. We reported Q4 earnings of $1.25 per share, "
                           "beating estimates. Our guidance for next quarter reflects confidence in market conditions. "
                           "We are investing heavily in R&D to maintain competitive advantage.",
            
            'investor_presentation': "Key takeaways: 1) Market leadership in core segments, 2) Strong cash generation, "
                                    "3) Expansion into high-growth markets, 4) Investment in emerging technologies. "
                                    "Our strategic positioning provides long-term growth potential.",
        }
        
        extracted_text = {}
        for company in companies:
            combined_text = " ".join(sample_documents.values())
            extracted_text[company] = combined_text
        
        return extracted_text
    
    def calculate_document_features(self, text: str) -> Dict:
        """
        Calculate features from unstructured text
        
        Args:
            text: Document text
        
        Returns:
            Dictionary with text features
        """
        words = text.split()
        sentences = text.split('.')
        
        features = {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_sentence_length': len(words) / max(len([s for s in sentences if s.strip()]), 1),
            'has_positive_language': any(word in text.lower() for word in 
                                        ['growth', 'strong', 'increase', 'success', 'opportunity']),
            'has_risk_language': any(word in text.lower() for word in 
                                    ['risk', 'challenge', 'decline', 'uncertain', 'pressure']),
            'mentions_innovation': 'innovation' in text.lower() or 'technology' in text.lower(),
            'mentions_market_expansion': 'market' in text.lower() and 'expansion' in text.lower(),
        }
        
        return features


if __name__ == "__main__":
    # Demo sentiment analysis
    print("\n" + "="*80)
    print("SENTIMENT ANALYSIS & NEWS MODULE - DEMO")
    print("="*80)
    
    analyzer = FinancialSentimentAnalyzer()
    companies = ['AAPL', 'MSFT', 'GOOGL', 'JPM', 'JNJ']
    
    # Generate sample news
    print("\n📰 Generating sample financial news articles...")
    news_articles = analyzer.generate_sample_news_dataset(companies, days=30)
    
    # Calculate sentiment metrics
    print("\n📊 Calculating sentiment metrics by company...\n")
    sentiment_summary = analyzer.calculate_sentiment_metrics_by_company(news_articles)
    print(sentiment_summary.to_string(index=False))
    
    # Save sentiment data
    sentiment_summary.to_csv('data/sentiment_analysis.csv', index=False)
    print("\n✅ Sentiment analysis saved to: data/sentiment_analysis.csv")
    
    # Show detailed indicators for first company
    print("\n" + "="*80)
    print(f"DETAILED SENTIMENT ANALYSIS: {companies[0]}")
    print("="*80)
    
    indicators = analyzer.get_sentiment_indicators(news_articles, companies[0])
    for key, value in indicators.items():
        print(f"  {key}: {value}")
    
    # Save all news articles
    news_df = pd.DataFrame(news_articles)
    news_df.to_csv('data/financial_news_articles.csv', index=False)
    print(f"\n✅ News articles saved to: data/financial_news_articles.csv")
    
    print("\n" + "="*80)
    print(" ✅ Unstructured Data Processing Complete!")
    print("="*80 + "\n")
