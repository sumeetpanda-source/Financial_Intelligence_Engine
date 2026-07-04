"""
Financial Data Fetcher
Fetches stock data from yFinance and company information
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings

from data_layer.yfinance_support import configure_yfinance_cache

warnings.filterwarnings('ignore')


class FinancialDataFetcher:
    """Fetches financial data for companies"""
    
    def __init__(self):
        self.cache_dir = configure_yfinance_cache()
        self.data = None
        self.info = None
    
    def fetch_stock_data(self, ticker, days_back=365):
        """
        Fetch historical stock data from Yahoo Finance
        
        Args:
            ticker (str): Stock ticker symbol (e.g., 'AAPL')
            days_back (int): Number of days of history to fetch
        
        Returns:
            pd.DataFrame: OHLCV (Open, High, Low, Close, Volume) data
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            print(f"📊 Fetching {ticker} data from {start_date.date()} to {end_date.date()}...")
            
            data = yf.download(
                ticker, 
                start=start_date, 
                end=end_date, 
                progress=False,
                threads=False,
                timeout=15,
                auto_adjust=False,
            )
            
            print(f"✅ Successfully fetched {len(data)} days of data")
            self.data = data
            return data
            
        except Exception as e:
            print(f"❌ Error fetching stock data: {str(e)}")
            return None
    
    def fetch_company_info(self, ticker):
        """
        Fetch company information from Yahoo Finance
        
        Args:
            ticker (str): Stock ticker symbol
        
        Returns:
            dict: Company information
        """
        try:
            print(f"📋 Fetching company info for {ticker}...")
            
            company = yf.Ticker(ticker)
            info = company.info
            
            company_data = {
                'ticker': ticker,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            }
            
            print(f"✅ Company info retrieved")
            self.info = company_data
            return company_data
            
        except Exception as e:
            print(f"❌ Error fetching company info: {str(e)}")
            return None
    
    def get_data_summary(self):
        """Get summary statistics of fetched data"""
        if self.data is None:
            print("❌ No data fetched yet")
            return None
        
        summary = {
            'rows': len(self.data),
            'columns': list(self.data.columns),
            'price_high': self.data['High'].max(),
            'price_low': self.data['Low'].min(),
            'avg_volume': self.data['Volume'].mean(),
            'last_close': self.data['Close'].iloc[-1]
        }
        
        return summary


if __name__ == "__main__":
    # Demo: Fetch data
    fetcher = FinancialDataFetcher()
    
    # Example: Apple Inc.
    print("\n" + "="*60)
    print("DEMO: Fetching Financial Data")
    print("="*60)
    
    # Fetch stock price data for 30 days
    stock_data = fetcher.fetch_stock_data('AAPL', days_back=30)
    
    if stock_data is not None:
        print("\n📈 Stock Data Summary:")
        print(f"  Latest Close: ${stock_data['Close'].iloc[-1]:.2f}")
        print(f"  30-Day High: ${stock_data['High'].max():.2f}")
        print(f"  30-Day Low: ${stock_data['Low'].min():.2f}")
    
    # Fetch company information
    company_info = fetcher.fetch_company_info('AAPL')
    
    if company_info:
        print("\n📋 Company Information:")
        for key, value in company_info.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
