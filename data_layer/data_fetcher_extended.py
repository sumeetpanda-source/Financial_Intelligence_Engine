"""
Extended Financial Data Fetcher
Fetches diverse data: structured (financials), unstructured (news), and visual (charts)
Supports multiple companies and data sources for comprehensive analysis
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import json
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import numpy as np
from storage import DataStore
from data_layer.yfinance_support import configure_yfinance_cache

warnings.filterwarnings('ignore')


class ExtendedFinancialDataFetcher:
    """
    Comprehensive financial data fetcher for multiple sources:
    - Structured: Stock prices, fundamentals, financial statements
    - Unstructured: News articles, analyst reports
    - Visual: Chart data, technical patterns
    """
    
    # Top 50 companies across sectors for diverse portfolio
    DEFAULT_COMPANIES = {
        'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'ADBE', 'CRM'],
        'Finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'PYPL', 'SQ'],
        'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'LLY', 'MRK', 'AMGN', 'GILD', 'BIIB', 'CVS'],
        'Consumer': ['AMZN', 'WMT', 'TM', 'COST', 'MCD', 'NKE', 'SBUX', 'HD', 'LOW', 'DIS'],
        'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'MPC', 'PSX', 'VLO', 'HES', 'OKE', 'MUR'],
    }
    
    def __init__(self, companies: Optional[List[str]] = None):
        """
        Initialize fetcher with list of companies
        
        Args:
            companies: List of ticker symbols. If None, uses DEFAULT_COMPANIES
        """
        self.cache_dir = configure_yfinance_cache()

        if companies is None:
            self.companies = self._load_cached_universe() or sum(self.DEFAULT_COMPANIES.values(), [])
        else:
            self.companies = companies
        
        self.stock_data = {}
        self.company_info = {}
        self.news_data = {}
        self.fundamentals = {}

    def _load_cached_universe(self) -> List[str]:
        """Load the cached US equity universe when available."""
        try:
            store = DataStore()
            universe = store.load_dataframe("processed", "us_equity_universe.csv")
        except Exception:
            return []

        if "ticker" not in universe.columns:
            return []

        return (
            universe["ticker"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.upper()
            .drop_duplicates()
            .tolist()
        )
        
    def fetch_multiple_companies_data(self, days_back: int = 365, limit: Optional[int] = None) -> Dict:
        """
        Fetch data for multiple companies
        
        Args:
            days_back: Number of historical days to fetch
            limit: Limit number of companies (for testing)
        
        Returns:
            Dictionary with all fetched data
        """
        companies_to_fetch = self.companies[:limit] if limit else self.companies
        
        print(f"\n{'='*80}")
        print(f"📊 EXTENDED DATA FETCHER - Fetching data for {len(companies_to_fetch)} companies")
        print(f"{'='*80}\n")
        
        results = {
            'stock_data': {},
            'company_info': {},
            'fundamentals': {},
            'news_sentiment': {},
            'technical_indicators': {},
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'companies_count': len(companies_to_fetch),
                'days_historical': days_back
            }
        }
        
        for idx, ticker in enumerate(companies_to_fetch, 1):
            print(f"[{idx}/{len(companies_to_fetch)}] Processing {ticker}...", end=" ")
            
            try:
                # Fetch stock data
                stock_df = self.fetch_stock_data(ticker, days_back)
                if stock_df is not None:
                    results['stock_data'][ticker] = stock_df.to_dict()
                    print("✅ Stock", end=" ")
                
                # Fetch company info
                info = self.fetch_company_info(ticker)
                if info:
                    results['company_info'][ticker] = info
                    print("Info", end=" ")
                
                # Fetch fundamentals
                fundamentals = self.fetch_fundamentals(ticker)
                if fundamentals:
                    results['fundamentals'][ticker] = fundamentals
                    print("Fundamentals", end=" ")
                
                # Fetch technical indicators
                technical = self.calculate_technical_indicators(stock_df)
                if technical is not None:
                    results['technical_indicators'][ticker] = technical
                    print("Indicators", end=" ")
                
                print("✅")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        self.stock_data = results['stock_data']
        self.company_info = results['company_info']
        self.fundamentals = results['fundamentals']
        
        return results
    
    def fetch_stock_data(self, ticker: str, days_back: int = 365) -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data
        
        Args:
            ticker: Stock ticker symbol
            days_back: Number of historical days
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,
                interval='1d',
                threads=False,
                timeout=15,
                auto_adjust=False,
            )
            
            if data.empty:
                return None

            if isinstance(data.columns, pd.MultiIndex):
                if {'Open', 'High', 'Low', 'Close', 'Volume'}.issubset(set(data.columns.get_level_values(0))):
                    data.columns = data.columns.get_level_values(0)
                else:
                    data.columns = data.columns.get_level_values(-1)
            
            return data
            
        except Exception as e:
            return None
    
    def fetch_company_info(self, ticker: str) -> Optional[Dict]:
        """
        Fetch comprehensive company information
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with company details
        """
        try:
            company = yf.Ticker(ticker)
            info = company.info
            
            company_data = {
                'ticker': ticker,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'N/A'),
                'employees': info.get('fullTimeEmployees', 'N/A'),
                'website': info.get('website', 'N/A'),
                'description': info.get('longBusinessSummary', 'N/A')[:200],  # First 200 chars
            }
            
            return company_data
            
        except Exception as e:
            return None
    
    def fetch_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Fetch financial fundamentals and ratios
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with financial metrics
        """
        try:
            company = yf.Ticker(ticker)
            info = company.info
            
            fundamentals = {
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else 'N/A',
                'peg_ratio': round(info.get('pegRatio', 0), 2) if info.get('pegRatio') else 'N/A',
                'price_to_book': round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else 'N/A',
                'debt_to_equity': round(info.get('debtToEquity', 0), 2) if info.get('debtToEquity') else 'N/A',
                'current_ratio': round(info.get('currentRatio', 0), 2) if info.get('currentRatio') else 'N/A',
                'roe': round((info.get('returnOnEquity', 0) or 0) * 100, 2) if info.get('returnOnEquity') else 'N/A',
                'roa': round((info.get('returnOnAssets', 0) or 0) * 100, 2) if info.get('returnOnAssets') else 'N/A',
                'profit_margin': round((info.get('profitMargins', 0) or 0) * 100, 2) if info.get('profitMargins') else 'N/A',
                'dividend_yield': round((info.get('dividendYield', 0) or 0) * 100, 2) if info.get('dividendYield') else 'N/A',
                'earnings_growth': info.get('earningsGrowth', 'N/A'),
                'revenue_growth': info.get('revenueGrowth', 'N/A'),
            }
            
            return fundamentals
            
        except Exception as e:
            return None
    
    def calculate_technical_indicators(self, stock_df: Optional[pd.DataFrame]) -> Optional[Dict]:
        """
        Calculate technical indicators from stock data
        
        Args:
            stock_df: DataFrame with OHLCV data
        
        Returns:
            Dictionary with technical indicators
        """
        if stock_df is None or stock_df.empty:
            return None
        
        try:
            df = stock_df.copy()
            latest = df.iloc[-1]
            
            # Moving Averages
            ma_20 = df['Close'].tail(20).mean()
            ma_50 = df['Close'].tail(50).mean()
            ma_200 = df['Close'].tail(200).mean() if len(df) >= 200 else None
            
            # RSI
            rsi = self._calculate_rsi(df['Close'], period=14)
            
            # MACD
            macd = self._calculate_macd(df['Close'])
            
            # Bollinger Bands
            bb = self._calculate_bollinger_bands(df['Close'], period=20)
            
            # Volatility
            volatility = df['Close'].pct_change().std() * 100
            
            # Volume indicators
            avg_volume = df['Volume'].tail(20).mean()
            volume_ratio = latest['Volume'] / avg_volume if avg_volume > 0 else 1
            
            indicators = {
                'price_current': round(float(latest['Close']), 2),
                'price_change_pct': round(float((latest['Close'] / df['Close'].iloc[-2] - 1) * 100), 2),
                'ma_20': round(float(ma_20), 2),
                'ma_50': round(float(ma_50), 2),
                'ma_200': round(float(ma_200), 2) if ma_200 else 'N/A',
                'rsi': round(rsi, 2),
                'macd': round(macd, 4) if macd else 'N/A',
                'bb_upper': round(float(bb['upper']), 2) if bb else 'N/A',
                'bb_lower': round(float(bb['lower']), 2) if bb else 'N/A',
                'volatility': round(volatility, 2),
                'volume_ratio': round(volume_ratio, 2),
                '52_week_high': round(float(df['High'].max()), 2),
                '52_week_low': round(float(df['Low'].min()), 2),
            }
            
            return indicators
            
        except Exception as e:
            return None
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        avg_gain = gains.tail(period).mean()
        avg_loss = losses.tail(period).mean()
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_macd(prices: pd.Series) -> Optional[float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < 26:
            return None
        
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        macd = ema_12.iloc[-1] - ema_26.iloc[-1]
        return macd
    
    @staticmethod
    def _calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Optional[Dict]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None
        
        ma = prices.tail(period).mean()
        std = prices.tail(period).std()
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        
        return {'upper': upper, 'lower': lower, 'middle': ma}
    
    def generate_comprehensive_report(self) -> pd.DataFrame:
        """
        Generate comprehensive report of all fetched data
        
        Returns:
            DataFrame with summary metrics for all companies
        """
        report_data = []
        
        for ticker, info in self.company_info.items():
            fundamentals = self.fundamentals.get(ticker, {})
            technical = self.stock_data.get(ticker, {})
            
            row = {
                'Ticker': ticker,
                'Company': info.get('name', 'N/A'),
                'Sector': info.get('sector', 'N/A'),
                'Industry': info.get('industry', 'N/A'),
                'Market Cap': fundamentals.get('market_cap', 'N/A'),
                'P/E Ratio': fundamentals.get('pe_ratio', 'N/A'),
                'Dividend Yield': fundamentals.get('dividend_yield', 'N/A'),
                'ROE': fundamentals.get('roe', 'N/A'),
                'Profit Margin': fundamentals.get('profit_margin', 'N/A'),
            }
            report_data.append(row)
        
        return pd.DataFrame(report_data)


if __name__ == "__main__":
    # Demo: Use extended fetcher
    print("\n" + "="*80)
    print("EXTENDED DATA FETCHER - DEMO")
    print("="*80)
    
    # Initialize with first 5 companies from each sector
    fetcher = ExtendedFinancialDataFetcher()
    
    # Fetch data for 10 companies (for demo)
    results = fetcher.fetch_multiple_companies_data(days_back=365, limit=10)
    
    # Generate report
    print("\n" + "="*80)
    print("COMPREHENSIVE REPORT")
    print("="*80 + "\n")
    
    report = fetcher.generate_comprehensive_report()
    print(report.to_string(index=False))
    
    # Save results
    report.to_csv('data/extended_companies_analysis.csv', index=False)
    print("\n✅ Report saved to: data/extended_companies_analysis.csv")
    
    # Show metadata
    print(f"\n📊 Data fetched: {results['metadata']['companies_count']} companies")
    print(f"📅 Historical data: {results['metadata']['days_historical']} days")
    print(f"⏰ Timestamp: {results['metadata']['timestamp']}")
