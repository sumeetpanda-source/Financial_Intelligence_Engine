"""
Comprehensive Financial Analysis Engine
Integrates structured data, technical analysis, and sentiment analysis
Produces unified investment insights and scoring
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from data_layer.data_fetcher_extended import ExtendedFinancialDataFetcher
from data_layer.feature_engineering import FinancialFeatureEngineer
from data_layer.sentiment_analyzer import FinancialSentimentAnalyzer


class ComprehensiveFinancialAnalyzer:
    """
    Unified analysis engine combining multiple data sources
    Structured: Prices, Fundamentals, Technicals
    Unstructured: News, Sentiment
    Output: Investment scores and recommendations
    """
    
    def __init__(self):
        self.fetcher = ExtendedFinancialDataFetcher()
        self.sentiment_analyzer = FinancialSentimentAnalyzer()
        self.analysis_results = {}
        self.investment_scores = {}
    
    def run_comprehensive_analysis(self, companies: List[str], days_back: int = 365) -> Dict:
        """
        Run complete analysis combining all data sources
        
        Args:
            companies: List of company tickers
            days_back: Historical days to fetch
        
        Returns:
            Comprehensive analysis results
        """
        print("\n" + "="*90)
        print("  COMPREHENSIVE FINANCIAL ANALYSIS ENGINE")
        print("="*90)
        
        # Phase 1: Fetch Structured Data
        print("\n📊 PHASE 1: Fetching Structured Data...")
        structured_results = self._fetch_structured_data(companies, days_back)
        
        # Phase 2: Calculate Technical Indicators
        print("\n📈 PHASE 2: Calculating Technical Analysis...")
        technical_results = self._calculate_technical_analysis(structured_results)
        
        # Phase 3: Generate Unstructured Data (News/Sentiment)
        print("\n📰 PHASE 3: Generating Sentiment Analysis...")
        sentiment_results = self._analyze_sentiment(companies)
        
        # Phase 4: Integrate All Data
        print("\n🔗 PHASE 4: Integrating Multi-Source Data...")
        integrated_data = self._integrate_all_data(
            structured_results, 
            technical_results, 
            sentiment_results
        )
        
        # Phase 5: Calculate Investment Scores
        print("\n⭐ PHASE 5: Computing Investment Scores...")
        investment_scores = self._calculate_investment_scores(integrated_data)
        
        # Phase 6: Generate Recommendations
        print("\n💡 PHASE 6: Generating Recommendations...")
        recommendations = self._generate_recommendations(investment_scores, integrated_data)
        
        final_results = {
            'structured_data': structured_results,
            'technical_analysis': technical_results,
            'sentiment_analysis': sentiment_results,
            'integrated_data': integrated_data,
            'investment_scores': investment_scores,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat(),
        }
        
        self.analysis_results = final_results
        
        return final_results
    
    def _fetch_structured_data(self, companies: List[str], days_back: int) -> Dict:
        """Fetch structured data from financial sources"""
        self.fetcher.companies = companies
        results = self.fetcher.fetch_multiple_companies_data(days_back=days_back, limit=len(companies))
        return results
    
    def _calculate_technical_analysis(self, structured_results: Dict) -> Dict:
        """Calculate comprehensive technical analysis"""
        technical_data = {}
        
        for ticker, stock_data_dict in structured_results['stock_data'].items():
            df = pd.DataFrame(stock_data_dict)
            df.index = pd.to_datetime(df.index)
            
            # Calculate technical indicators
            df_indicators = FinancialFeatureEngineer.calculate_technical_indicators(df)
            latest = df_indicators.iloc[-1]
            
            technical_data[ticker] = {
                'momentum': {
                    'rsi_14': float(latest.get('RSI_14', 50)),
                    'macd': float(latest.get('MACD', 0)),
                    'roc_12': float(latest.get('ROC_12', 0)),
                },
                'volatility': {
                    'atr': float(latest.get('ATR', 0)),
                    'bollinger_position': float(latest.get('BB_Position', 0.5)),
                    'volatility_20': float(latest.get('Volatility_20', 0)),
                },
                'trend': {
                    'price_vs_ma20': float(latest.get('Price_vs_MA20', 0)),
                    'price_vs_ma50': float(latest.get('Price_vs_MA50', 0)),
                    'trend_strength': float(latest.get('Trend_Strength', 0)),
                },
                'volume': {
                    'volume_ratio': float(latest.get('Volume_Ratio', 1)),
                    'obv': float(latest.get('OBV', 0)) if 'OBV' in latest.index else 0,
                },
            }
        
        return technical_data
    
    def _analyze_sentiment(self, companies: List[str]) -> Dict:
        """Generate sentiment analysis data"""
        # Generate sample news
        news_articles = self.sentiment_analyzer.generate_sample_news_dataset(companies, days=30)
        
        sentiment_data = {}
        for ticker in companies:
            indicators = self.sentiment_analyzer.get_sentiment_indicators(news_articles, ticker)
            if indicators:
                sentiment_data[ticker] = indicators
        
        return sentiment_data
    
    def _integrate_all_data(self, structured: Dict, technical: Dict, 
                           sentiment: Dict) -> Dict:
        """Integrate structured, technical, and sentiment data"""
        integrated = {}
        
        for ticker in structured['company_info'].keys():
            company_info = structured['company_info'].get(ticker, {})
            fundamentals = structured['fundamentals'].get(ticker, {})
            technical_info = technical.get(ticker, {})
            sentiment_info = sentiment.get(ticker, {})
            
            integrated[ticker] = {
                'company': company_info.get('name', ticker),
                'sector': company_info.get('sector', 'N/A'),
                'fundamentals': {
                    'pe_ratio': fundamentals.get('pe_ratio', 'N/A'),
                    'roe': fundamentals.get('roe', 'N/A'),
                    'profit_margin': fundamentals.get('profit_margin', 'N/A'),
                },
                'technical': technical_info,
                'sentiment': sentiment_info,
            }
        
        return integrated
    
    def _calculate_investment_scores(self, integrated_data: Dict) -> Dict:
        """Calculate composite investment scores"""
        scores = {}
        
        for ticker, data in integrated_data.items():
            # Technical score (0-100)
            technical = data.get('technical', {})
            rsi = technical.get('momentum', {}).get('rsi_14', 50)
            trend_strength = technical.get('trend', {}).get('trend_strength', 0)
            technical_score = (rsi / 100 * 40 + trend_strength * 100 * 0.6) / 2
            
            # Sentiment score (0-100)
            sentiment = data.get('sentiment', {})
            sentiment_score_raw = sentiment.get('avg_sentiment_score', 0.5)
            sentiment_score = sentiment_score_raw * 100
            
            # Fundamental score (0-100)
            fundamentals = data.get('fundamentals', {})
            pe_ratio = fundamentals.get('pe_ratio', 'N/A')
            roe = fundamentals.get('roe', 'N/A')
            
            fundamental_score = 50  # Base score
            if isinstance(pe_ratio, (int, float)) and 10 < pe_ratio < 30:
                fundamental_score += 20
            if isinstance(roe, (int, float)) and roe > 15:
                fundamental_score += 20
            
            # Composite score (weighted average)
            composite_score = (technical_score * 0.4 + sentiment_score * 0.3 + 
                             fundamental_score * 0.3)
            
            scores[ticker] = {
                'technical_score': round(technical_score, 2),
                'sentiment_score': round(sentiment_score, 2),
                'fundamental_score': round(fundamental_score, 2),
                'composite_score': round(composite_score, 2),
                'risk_level': 'Low' if composite_score > 70 else 
                             'Medium' if composite_score > 50 else 'High',
                'confidence': round(technical_score * sentiment_score / 10000 * 100, 1),
            }
        
        return scores
    
    def _generate_recommendations(self, scores: Dict, integrated_data: Dict) -> Dict:
        """Generate investment recommendations"""
        recommendations = {}
        
        for ticker, score_data in scores.items():
            composite = score_data['composite_score']
            
            if composite > 70:
                recommendation = 'STRONG BUY'
                rationale = f"Strong fundamentals ({score_data['fundamental_score']:.0f}/100), "
                rationale += f"positive sentiment ({score_data['sentiment_score']:.0f}/100), "
                rationale += f"and good technical setup ({score_data['technical_score']:.0f}/100)"
            elif composite > 60:
                recommendation = 'BUY'
                rationale = "Positive momentum with mixed signals"
            elif composite > 40:
                recommendation = 'HOLD'
                rationale = "Mixed signals - monitor before taking action"
            else:
                recommendation = 'SELL'
                rationale = f"Weak fundamentals or negative sentiment"
            
            recommendations[ticker] = {
                'recommendation': recommendation,
                'composite_score': composite,
                'rationale': rationale,
                'confidence_level': score_data['confidence'],
                'review_date': (datetime.now() + pd.Timedelta(days=7)).isoformat(),
            }
        
        return recommendations
    
    def generate_executive_report(self) -> pd.DataFrame:
        """Generate executive summary report"""
        if not self.analysis_results:
            return None
        
        report_data = []
        scores = self.analysis_results['investment_scores']
        recommendations = self.analysis_results['recommendations']
        integrated = self.analysis_results['integrated_data']
        
        for ticker, score in scores.items():
            rec = recommendations.get(ticker, {})
            data = integrated.get(ticker, {})
            
            row = {
                'Ticker': ticker,
                'Company': data.get('company', 'N/A'),
                'Sector': data.get('sector', 'N/A'),
                'Technical Score': score['technical_score'],
                'Sentiment Score': score['sentiment_score'],
                'Fundamental Score': score['fundamental_score'],
                'Overall Score': score['composite_score'],
                'Confidence %': score['confidence'],
                'Risk Level': score['risk_level'],
                'Recommendation': rec.get('recommendation', 'HOLD'),
            }
            report_data.append(row)
        
        return pd.DataFrame(report_data)
    
    def generate_detailed_company_analysis(self, ticker: str) -> Dict:
        """Generate detailed analysis for a specific company"""
        if ticker not in self.analysis_results['integrated_data']:
            return None
        
        data = self.analysis_results['integrated_data'][ticker]
        score = self.analysis_results['investment_scores'][ticker]
        recommendation = self.analysis_results['recommendations'][ticker]
        
        analysis = {
            'ticker': ticker,
            'company_name': data['company'],
            'sector': data['sector'],
            
            'scoring': {
                'technical': score['technical_score'],
                'sentiment': score['sentiment_score'],
                'fundamental': score['fundamental_score'],
                'overall': score['composite_score'],
                'confidence': score['confidence'],
            },
            
            'technical_indicators': data['technical'],
            'sentiment_metrics': data['sentiment'],
            'fundamental_metrics': data['fundamentals'],
            
            'recommendation': recommendation['recommendation'],
            'rationale': recommendation['rationale'],
            'risk_level': score['risk_level'],
        }
        
        return analysis


def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*90)
    print(f"  {title}")
    print("="*90)


if __name__ == "__main__":
    # Run comprehensive analysis
    print_section("COMPREHENSIVE FINANCIAL ANALYSIS DEMO")
    
    analyzer = ComprehensiveFinancialAnalyzer()
    
    # Companies to analyze
    companies = ['AAPL', 'MSFT', 'JPM', 'JNJ', 'XOM', 'AMZN', 'NVDA', 'PFE', 'WMT', 'META']
    
    # Run analysis
    results = analyzer.run_comprehensive_analysis(companies, days_back=365)
    
    # Generate reports
    print_section("EXECUTIVE SUMMARY REPORT")
    
    exec_report = analyzer.generate_executive_report()
    print("\n" + exec_report.to_string(index=False))
    
    # Save report
    exec_report.to_csv('data/comprehensive_investment_report.csv', index=False)
    print(f"\n✅ Executive report saved to: data/comprehensive_investment_report.csv")
    
    # Show detailed analysis for top company
    print_section(f"DETAILED ANALYSIS: {companies[0]}")
    
    detailed = analyzer.generate_detailed_company_analysis(companies[0])
    
    if detailed:
        print(f"\nCompany: {detailed['company_name']}")
        print(f"Sector: {detailed['sector']}")
        print(f"\nScoring:")
        for metric, score in detailed['scoring'].items():
            print(f"  {metric.capitalize()}: {score:.2f}")
        print(f"\nRecommendation: {detailed['recommendation']}")
        print(f"Rationale: {detailed['rationale']}")
        print(f"Risk Level: {detailed['risk_level']}")
    
    print_section("ANALYSIS COMPLETE")
    print(f"✅ Analyzed {len(companies)} companies")
    print(f"✅ Integrated structured + unstructured data")
    print(f"✅ Generated investment recommendations")
    print("✅ Ready for decision-making\n")
