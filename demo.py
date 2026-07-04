"""
Demo Script: Financial Intelligence Engine
Shows the system working end-to-end
"""

from data_layer.data_fetcher import FinancialDataFetcher
import pandas as pd


def main():
    print("\n" + "="*70)
    print(" FINANCIAL INTELLIGENCE ENGINE - DEMO")
    print("="*70)
    
    fetcher = FinancialDataFetcher()
    
    # Companies to analyze
    companies = ['AAPL', 'MSFT', 'GOOGL']
    
    print("\n📊 Fetching financial data for major tech companies...")
    print("\n" + "-"*70)
    
    all_results = []
    
    for ticker in companies:
        print(f"\n🔍 Processing: {ticker}")
        print("-"*70)
        
        # Fetch company info
        info = fetcher.fetch_company_info(ticker)
        if not info:
            continue
        
        # Fetch stock data
        stock_data = fetcher.fetch_stock_data(ticker, days_back=30)
        if stock_data is None:
            continue
        
        # Calculate metrics
        latest_price = float(stock_data['Close'].iloc[-1])
        high_30d = float(stock_data['High'].max())
        low_30d = float(stock_data['Low'].min())
        avg_volume = float(stock_data['Volume'].mean())
        
        # Store results
        result = {
            'Ticker': ticker,
            'Company': info['name'],
            'Sector': info['sector'],
            'Latest Price': f"${latest_price:.2f}",
            '30-Day High': f"${high_30d:.2f}",
            '30-Day Low': f"${low_30d:.2f}",
            'Avg Volume': f"{avg_volume:,.0f}",
            'P/E Ratio': info['pe_ratio'],
        }
        
        all_results.append(result)
        
        print(f"  ✅ {info['name']}")
        print(f"     Sector: {info['sector']}")
        print(f"     Latest Price: ${latest_price:.2f}")
        print(f"     52-Week High: ${info['fifty_two_week_high']}")
        print(f"     P/E Ratio: {info['pe_ratio']}")
    
    # Create summary DataFrame
    print("\n" + "="*70)
    print(" SUMMARY")
    print("="*70 + "\n")
    
    if all_results:
        df = pd.DataFrame(all_results)
        print(df.to_string(index=False))
        
        # Save to CSV
        csv_path = 'data/companies_summary.csv'
        df.to_csv(csv_path, index=False)
        print(f"\n✅ Summary saved to: {csv_path}")
    
    print("\n" + "="*70)
    print(" ✅ DEMO COMPLETE - System is working!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
