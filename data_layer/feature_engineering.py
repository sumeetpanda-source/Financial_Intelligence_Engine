"""
Comprehensive Financial Feature Engineering Module
Calculates 50+ technical, volatility, and momentum indicators for ML models
"""

import pandas as pd
import numpy as np
from typing import Tuple


class FinancialFeatureEngineer:
    """Creates comprehensive financial features from raw OHLCV data"""
    
    @staticmethod
    def calculate_ratios(df):
        """
        Calculate key financial ratios and metrics
        
        Args:
            df (pd.DataFrame): Input stock data with OHLCV columns
        
        Returns:
            pd.DataFrame: Dataframe with new feature columns
        """
        df = df.copy()
        
        # Price changes
        df['Price_Change'] = df['Close'].pct_change()
        df['Price_Change_Pct'] = df['Price_Change'] * 100
        
        # Moving averages
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['MA_50'] = df['Close'].rolling(window=50).mean()
        df['MA_200'] = df['Close'].rolling(window=200).mean()
        
        # Volatility
        df['Volatility'] = df['Close'].rolling(window=20).std()
        df['Volatility_Pct'] = (df['Volatility'] / df['Close']) * 100
        
        # Volume changes
        df['Volume_Change'] = df['Volume'].pct_change()
        df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
        
        return df
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            prices (pd.Series): Price series
            period (int): Period for RSI calculation (default: 14)
        
        Returns:
            pd.Series: RSI values
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """
        Calculate Moving Average Convergence Divergence (MACD)
        
        Args:
            prices (pd.Series): Price series
            fast (int): Fast EMA period (default: 12)
            slow (int): Slow EMA period (default: 26)
            signal (int): Signal line period (default: 9)
        
        Returns:
            tuple: (MACD line, Signal line, Histogram)
        """
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, num_std=2):
        """
        Calculate Bollinger Bands
        
        Args:
            prices (pd.Series): Price series
            period (int): Period (default: 20)
            num_std (int): Number of standard deviations (default: 2)
        
        Returns:
            tuple: (Upper band, Middle band, Lower band)
        """
        middle_band = prices.rolling(window=period).mean()
        std_dev = prices.rolling(window=period).std()
        
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """
        Calculate Average True Range (ATR)
        
        Args:
            high (pd.Series): High prices
            low (pd.Series): Low prices
            close (pd.Series): Close prices
            period (int): Period (default: 14)
        
        Returns:
            pd.Series: ATR values
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_stochastic(high, low, close, period=14, smooth_k=3, smooth_d=3):
        """
        Calculate Stochastic Oscillator
        
        Args:
            high, low, close: OHLC series
            period, smooth_k, smooth_d: Parameters
        
        Returns:
            tuple: (%K line, %D line)
        """
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        k_line = k_percent.rolling(window=smooth_k).mean()
        d_line = k_line.rolling(window=smooth_d).mean()
        
        return k_line, d_line
    
    @staticmethod
    def calculate_obv(close, volume):
        """
        Calculate On-Balance Volume (OBV)
        
        Args:
            close (pd.Series): Close prices
            volume (pd.Series): Volumes
        
        Returns:
            pd.Series: OBV values
        """
        close_vals = np.asarray(close).flatten()
        vol_vals = np.asarray(volume).flatten()
        
        obv = np.where(close_vals > np.roll(close_vals, 1), vol_vals, 
                      np.where(close_vals < np.roll(close_vals, 1), -vol_vals, 0))
        obv = obv.flatten()
        obv = pd.Series(obv).cumsum()
        
        return obv
    
    @staticmethod
    def calculate_roc(prices, period=12):
        """
        Calculate Rate of Change (ROC)
        
        Args:
            prices (pd.Series): Price series
            period (int): Period (default: 12)
        
        Returns:
            pd.Series: ROC values
        """
        roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
        return roc
    
    @staticmethod
    def calculate_technical_indicators(df):
        """
        Calculate comprehensive technical indicators
        
        Args:
            df (pd.DataFrame): Input stock data with OHLCV
        
        Returns:
            pd.DataFrame: Dataframe with 50+ technical indicators
        """
        df = df.copy()

        if isinstance(df.columns, pd.MultiIndex):
            if {'Open', 'High', 'Low', 'Close', 'Volume'}.issubset(set(df.columns.get_level_values(0))):
                df.columns = df.columns.get_level_values(0)
            else:
                df.columns = df.columns.get_level_values(-1)
        
        # Ensure all OHLCV columns are 1D Series
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                if hasattr(df[col], 'values'):
                    vals = df[col].values
                    if len(vals.shape) > 1:
                        vals = vals.flatten()
                    df[col] = vals
        
        # =================
        # MOMENTUM INDICATORS
        # =================
        
        # RSI (14-period)
        df['RSI_14'] = FinancialFeatureEngineer.calculate_rsi(df['Close'], period=14)
        df['RSI_7'] = FinancialFeatureEngineer.calculate_rsi(df['Close'], period=7)
        
        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = FinancialFeatureEngineer.calculate_macd(
            df['Close']
        )
        
        # Stochastic
        df['Stochastic_K'], df['Stochastic_D'] = FinancialFeatureEngineer.calculate_stochastic(
            df['High'], df['Low'], df['Close']
        )
        
        # Rate of Change
        df['ROC_12'] = FinancialFeatureEngineer.calculate_roc(df['Close'], period=12)
        
        # =================
        # VOLATILITY INDICATORS
        # =================
        
        # Bollinger Bands
        close_values = df['Close'].values.flatten()
        close_series = pd.Series(close_values)
        bb_upper, bb_middle, bb_lower = FinancialFeatureEngineer.calculate_bollinger_bands(
            close_series, period=20
        )
        df['BB_Upper'] = bb_upper.values
        df['BB_Middle'] = bb_middle.values
        df['BB_Lower'] = bb_lower.values
        bb_upper_arr = np.asarray(df['BB_Upper']).flatten()
        bb_lower_arr = np.asarray(df['BB_Lower']).flatten()
        df['BB_Width'] = bb_upper_arr - bb_lower_arr
        # Handle division by zero in BB_Position
        df['BB_Position'] = np.divide(close_values - df['BB_Lower'].values, 
                                       df['BB_Width'].values, 
                                       where=df['BB_Width'].values!=0, 
                                       out=np.full(len(df), 0.5, dtype=float))
        
        # ATR (Average True Range)
        df['ATR'] = FinancialFeatureEngineer.calculate_atr(
            df['High'], df['Low'], df['Close'], period=14
        )
        atr_vals = df['ATR'].values.flatten() if hasattr(df['ATR'].values, 'flatten') else df['ATR'].values
        close_vals_2 = df['Close'].values.flatten() if hasattr(df['Close'].values, 'flatten') else df['Close'].values
        df['ATR_Pct'] = (atr_vals / close_vals_2) * 100
        
        # Volatility
        df['Volatility_20'] = df['Close'].pct_change().rolling(window=20).std() * 100
        df['Volatility_50'] = df['Close'].pct_change().rolling(window=50).std() * 100
        
        # =================
        # TREND INDICATORS
        # =================
        
        # Moving Averages
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_10'] = df['Close'].rolling(window=10).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['MA_50'] = df['Close'].rolling(window=50).mean()
        df['MA_100'] = df['Close'].rolling(window=100).mean()
        df['MA_200'] = df['Close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # Price position relative to MAs
        close_arr = np.asarray(df['Close']).flatten()
        ma20_arr = np.asarray(df['MA_20']).flatten()
        ma50_arr = np.asarray(df['MA_50']).flatten()
        
        df['Price_vs_MA20'] = np.divide(close_arr - ma20_arr, ma20_arr, where=ma20_arr!=0, out=np.full_like(close_arr, 0.0)) * 100
        df['Price_vs_MA50'] = np.divide(close_arr - ma50_arr, ma50_arr, where=ma50_arr!=0, out=np.full_like(close_arr, 0.0)) * 100
        df['MA20_vs_MA50'] = np.divide(ma20_arr - ma50_arr, ma50_arr, where=ma50_arr!=0, out=np.full_like(ma20_arr, 0.0)) * 100
        
        # =================
        # VOLUME INDICATORS
        # =================
        
        # On-Balance Volume
        df['OBV'] = FinancialFeatureEngineer.calculate_obv(df['Close'], df['Volume'])
        df['OBV_EMA'] = df['OBV'].ewm(span=20, adjust=False).mean()
        
        # Volume Moving Average
        df['Volume_MA_10'] = df['Volume'].rolling(window=10).mean()
        df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
        vol_vals = np.asarray(df['Volume']).flatten()
        volma_vals = np.asarray(df['Volume_MA_20']).flatten()
        df['Volume_Ratio'] = np.divide(
            vol_vals,
            volma_vals,
            where=volma_vals != 0,
            out=np.full(vol_vals.shape, 1.0, dtype=float)
        )
        
        # Price-Volume Trend
        df['PVT'] = (df['Close'].pct_change() * df['Volume']).cumsum()
        
        # =================
        # PRICE ACTION
        # =================
        
        # Daily Returns
        df['Daily_Return'] = df['Close'].pct_change() * 100
        df['Daily_Return_Squared'] = df['Daily_Return'] ** 2
        
        # High-Low Range
        high_arr = np.asarray(df['High']).flatten()
        low_arr = np.asarray(df['Low']).flatten()
        df['HL_Range'] = np.divide(high_arr - low_arr, low_arr, where=low_arr!=0, out=np.full_like(high_arr, 0.0)) * 100
        df['Close_Position'] = (df['Close'] - df['Low']) / (df['High'] - df['Low'])
        
        # Gap
        df['Gap'] = (df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1) * 100
        
        # =================
        # COMPOSITE FEATURES
        # =================
        
        # Trend Strength (combination of indicators)
        df['Trend_Strength'] = (
            (df['Price_vs_MA20'] > 0).astype(int) * 0.3 +
            (df['MA20_vs_MA50'] > 0).astype(int) * 0.3 +
            ((df['MACD'] > df['MACD_Signal']).astype(int)) * 0.2 +
            ((df['RSI_14'] > 50).astype(int)) * 0.2
        )
        
        # Momentum Score
        df['Momentum_Score'] = (
            ((df['RSI_14'] - 50) / 50) * 0.3 +
            (df['MACD_Histogram'] / df['MACD_Histogram'].std()) * 0.3 +
            ((df['ROC_12'] / df['ROC_12'].std()) * 0.4)
        )
        
        return df
        
        # MACD
        df['MACD'], df['Signal_Line'], df['MACD_Histogram'] = \
            FinancialFeatureEngineer.calculate_macd(df['Close'])
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        return df
