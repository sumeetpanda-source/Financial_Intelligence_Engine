"""
Data Cleaning and Preprocessing Module
"""

import pandas as pd
import numpy as np


class DataCleaner:
    """Cleans and preprocesses financial data"""
    
    @staticmethod
    def handle_missing_values(df, method='forward_fill'):
        """
        Handle missing values in data
        
        Args:
            df (pd.DataFrame): Input dataframe
            method (str): Method to handle missing values ('forward_fill', 'backward_fill', 'drop')
        
        Returns:
            pd.DataFrame: Dataframe with missing values handled
        """
        if method == 'forward_fill':
            return df.fillna(method='ffill').fillna(method='bfill')
        elif method == 'backward_fill':
            return df.fillna(method='bfill').fillna(method='ffill')
        elif method == 'drop':
            return df.dropna()
        return df
    
    @staticmethod
    def remove_outliers(df, column, threshold=3):
        """
        Remove outliers using z-score method
        
        Args:
            df (pd.DataFrame): Input dataframe
            column (str): Column name to check for outliers
            threshold (float): Z-score threshold (default: 3)
        
        Returns:
            pd.DataFrame: Dataframe with outliers removed
        """
        mean = df[column].mean()
        std = df[column].std()
        
        z_scores = np.abs((df[column] - mean) / std)
        return df[z_scores < threshold]
    
    @staticmethod
    def normalize_columns(df, columns):
        """
        Normalize columns to 0-1 range (Min-Max scaling)
        
        Args:
            df (pd.DataFrame): Input dataframe
            columns (list): List of column names to normalize
        
        Returns:
            pd.DataFrame: Dataframe with normalized columns
        """
        df_copy = df.copy()
        for col in columns:
            if col in df_copy.columns:
                min_val = df_copy[col].min()
                max_val = df_copy[col].max()
                df_copy[col] = (df_copy[col] - min_val) / (max_val - min_val)
        return df_copy
