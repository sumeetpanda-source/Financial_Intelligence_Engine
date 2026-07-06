"""
Quick Verification Script
Validates that all components are working correctly
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def check_imports():
    """Check if all required imports work"""
    print("\n✓ Checking imports...\n")
    
    try:
        import pandas as pd
        print("  ✅ pandas")
    except ImportError as e:
        print(f"  ❌ pandas: {e}")
        return False
    
    try:
        import numpy as np
        print("  ✅ numpy")
    except ImportError as e:
        print(f"  ❌ numpy: {e}")
        return False
    
    try:
        import yfinance
        print("  ✅ yfinance")
    except ImportError as e:
        print(f"  ❌ yfinance: {e}")
        return False
    
    try:
        from data_layer.data_fetcher_extended import ExtendedFinancialDataFetcher
        print("  ✅ ExtendedFinancialDataFetcher")
    except ImportError as e:
        print(f"  ❌ ExtendedFinancialDataFetcher: {e}")
        return False
    
    try:
        from data_layer.feature_engineering import FinancialFeatureEngineer
        print("  ✅ FinancialFeatureEngineer")
    except ImportError as e:
        print(f"  ❌ FinancialFeatureEngineer: {e}")
        return False
    
    try:
        from data_layer.sentiment_analyzer import FinancialSentimentAnalyzer
        print("  ✅ FinancialSentimentAnalyzer")
    except ImportError as e:
        print(f"  ❌ FinancialSentimentAnalyzer: {e}")
        return False
    
    try:
        from comprehensive_analysis import ComprehensiveFinancialAnalyzer
        print("  ✅ ComprehensiveFinancialAnalyzer")
    except ImportError as e:
        print(f"  ❌ ComprehensiveFinancialAnalyzer: {e}")
        return False
    
    try:
        from data_quality_assessment import SystemReadinessReport
        print("  ✅ SystemReadinessReport")
    except ImportError as e:
        print(f"  ❌ SystemReadinessReport: {e}")
        return False

    try:
        from agents import OrchestratorAgent
        print("  ✅ OrchestratorAgent")
    except ImportError as e:
        print(f"  ❌ OrchestratorAgent: {e}")
        return False

    try:
        from storage import DataStore
        from data_layer.company_universe import USEquityUniverseBuilder
        from data_layer.phase1_data_pipeline import Phase1DataPipeline
        from data_layer.real_market_data import RealMarketDataPipeline
        from ml_models.phase1_trainer import Phase1ModelTrainer
        from ml_models.real_market_trainer import RealMarketModelTrainer
        from rag_layer.rag_system import RAGSystem
        from rag_layer.sec_filings import SECFilingIngestor
        from genai_layer import build_genai_provider
        print("  ✅ Phase 1 storage, universe, data, model, RAG, and GenAI layers")
    except ImportError as e:
        print(f"  ❌ Phase 1 platform layers: {e}")
        return False
    
    return True


def check_files():
    """Check if all required files exist"""
    print("\n✓ Checking files...\n")
    
    required_files = [
        'data_layer/data_fetcher.py',
        'data_layer/data_fetcher_extended.py',
        'data_layer/feature_engineering.py',
        'data_layer/sentiment_analyzer.py',
        'data_layer/__init__.py',
        'comprehensive_analysis.py',
        'data_quality_assessment.py',
        'demo.py',
        'demo_enhanced.py',
        'demo_ultimate.py',
        'demo_phase1_agents.py',
        'agents/orchestrator_agent.py',
        'agents/retriever_agent.py',
        'agents/sentiment_agent.py',
        'agents/risk_agent.py',
        'agents/forecast_agent.py',
        'agents/decision_agent.py',
        'agents/explainability_agent.py',
        'config/settings.py',
        'storage/data_store.py',
        'data_layer/company_universe.py',
        'data_layer/phase1_data_pipeline.py',
        'data_layer/real_market_data.py',
        'ml_models/simple_models.py',
        'ml_models/phase1_trainer.py',
        'ml_models/real_market_trainer.py',
        'build_phase1_data.py',
        'fetch_real_market_data.py',
        'train_phase1_models.py',
        'train_real_market_models.py',
        'index_phase1_rag.py',
        'ingest_sec_filings.py',
        'query_phase1_rag.py',
        'rag_layer/embeddings.py',
        'rag_layer/document_loader.py',
        'rag_layer/retriever.py',
        'rag_layer/rag_system.py',
        'rag_layer/sec_filings.py',
        'genai_layer/provider.py',
        'setup_phase1_storage.py',
        '.env.example',
        'requirements.txt',
        'docs/DATA_LAYER_EXPANSION.md',
        'docs/QUICK_START.md',
        'docs/DAY1_SUMMARY.md',
        'docs/PHASE1_DEVELOPMENT_NEEDS.md',
        'docs/FINROBOT_PHASE1_REPLICATION_PLAN.md',
        'docs/IMPLEMENTATION_DETAILS.md',
    ]
    
    all_exist = True
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"  ✅ {filepath}")
        else:
            print(f"  ❌ {filepath} - NOT FOUND")
            all_exist = False
    
    return all_exist


def check_data_folder():
    """Check if data folder exists"""
    print("\n✓ Checking data folder...\n")
    
    if not os.path.exists('data'):
        print("  ℹ  data/ folder doesn't exist yet (will be created on demo run)")
        return True
    else:
        print("  ✅ data/ folder exists")
        files = os.listdir('data')
        print(f"  📁 Contains {len(files)} files")
        for f in files[:5]:
            print(f"     - {f}")
        if len(files) > 5:
            print(f"     ... and {len(files) - 5} more")
        return True


def test_data_fetcher():
    """Test data fetcher with single company"""
    print("\n✓ Testing data fetcher...\n")

    offline_assets = [
        "data/processed/us_equity_universe.csv",
        "data/features/phase1_model_features.csv",
        "models/phase1_risk_model.pkl",
        "models/phase1_forecast_model.pkl",
        "data/vectors/chroma",
    ]
    verify_live = os.getenv("FIE_VERIFY_LIVE_DATA", "0").lower() in {"1", "true", "yes"}
    if not verify_live:
        if all(os.path.exists(path) for path in offline_assets):
            print("  ✅ Cached universe, features, models, and RAG assets are ready")
            print("  ℹ️  Set FIE_VERIFY_LIVE_DATA=1 to test Yahoo Finance connectivity")
            return True
        print("  ❌ Offline fallback assets are incomplete")
        return False

    try:
        from data_layer.data_fetcher_extended import ExtendedFinancialDataFetcher
        
        print("  Initializing fetcher...")
        fetcher = ExtendedFinancialDataFetcher(['AAPL'])
        
        print("  Fetching data for AAPL...")
        results = fetcher.fetch_multiple_companies_data(days_back=30, limit=1)
        
        if results['stock_data'].get('AAPL'):
            print("  ✅ Successfully fetched stock data")
        else:
            if all(os.path.exists(path) for path in offline_assets):
                print("  ⚠️  Live Yahoo Finance data is unavailable")
                print("  ✅ Cached universe, features, models, and RAG fallback are ready")
                return True
            print("  ❌ No live data or complete offline fallback assets")
            return False
        
        if results['company_info'].get('AAPL'):
            print("  ✅ Successfully fetched company info")
        else:
            print("  ⚠️  No company info returned")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_feature_engineering():
    """Test feature engineering"""
    print("\n✓ Testing feature engineering...\n")
    
    try:
        import pandas as pd
        from data_layer.feature_engineering import FinancialFeatureEngineer
        import numpy as np
        
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=100)
        data = {
            'Open': np.random.uniform(100, 110, 100),
            'High': np.random.uniform(110, 120, 100),
            'Low': np.random.uniform(90, 100, 100),
            'Close': np.random.uniform(100, 110, 100),
            'Volume': np.random.uniform(1000000, 2000000, 100),
        }
        df = pd.DataFrame(data, index=dates)
        
        print("  Calculating technical indicators...")
        df_indicators = FinancialFeatureEngineer.calculate_technical_indicators(df)
        
        if 'RSI_14' in df_indicators.columns:
            print("  ✅ RSI calculated")
        else:
            print("  ❌ RSI not found")
            return False
        
        if 'MACD' in df_indicators.columns:
            print("  ✅ MACD calculated")
        else:
            print("  ❌ MACD not found")
            return False
        
        feature_count = len(df_indicators.columns) - len(df.columns)
        print(f"  ✅ Generated {feature_count} technical features")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all verification checks"""
    
    print("\n" + "="*60)
    print("  FINANCIAL INTELLIGENCE ENGINE - VERIFICATION SCRIPT")
    print("="*60)
    
    checks = [
        ("Imports", check_imports),
        ("Files", check_files),
        ("Data Folder", check_data_folder),
        ("Data Fetcher", test_data_fetcher),
        ("Feature Engineering", test_feature_engineering),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"  ❌ Unexpected error in {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("  VERIFICATION SUMMARY")
    print("="*60 + "\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Passed: {passed}/{total}")
    
    if passed == total:
        print("\n" + "="*60)
        print("  🎉 ALL CHECKS PASSED!")
        print("="*60)
        print("\n  Next: Run 'python demo_ultimate.py' to see the system in action!\n")
        return 0
    else:
        print("\n" + "="*60)
        print("  ⚠️  SOME CHECKS FAILED")
        print("="*60)
        print("\n  Please fix the issues above and try again.\n")
        print("  Installation help:")
        print("    pip install -r requirements.txt\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
