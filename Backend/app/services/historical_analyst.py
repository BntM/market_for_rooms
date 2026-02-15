import pandas as pd
import numpy as np

class HistoricalAnalyst:
    def __init__(self, data_path=None):
        self.data_path = data_path
        
    def analyze_demand(self, df: pd.DataFrame) -> dict:
        """
        Analyzes historical (or scraped) data to indentify density.
        Calculates suggested multipliers for the Enterprise.
        """
        if df.empty:
            return {}
            
        # 1. Location Popularity (Inversely proportional to availability if current data, 
        # or proportional to occupancy if historical)
        if 'location' in df.columns:
            loc_counts = df['location'].value_counts()
            mean_supply = loc_counts.mean()
            # Suggested weight = Mean / Local_Supply (Scarce locations get higher weights)
            # Avoid division by zero
            loc_weights = (mean_supply / (loc_counts + 1)).to_dict()
        else:
            loc_weights = {}
        
        # 2. Time of Day (Peak hours)
        time_weights = {}
        if 'time_slot' in df.columns:
            # Assuming format 'HH:MM' or datetime
            try:
                # Handle varying formats if possible, but strictly expect HH:MM for now as per legacy
                df['hour'] = df['time_slot'].apply(lambda x: int(str(x).split(':')[0]) if ':' in str(x) else 12)
                hour_counts = df['hour'].value_counts()
                mean_hour = hour_counts.mean()
                time_weights = (mean_hour / (hour_counts + 1)).to_dict()
            except Exception:
                pass # Fail gracefully if format is bad

        return {
            "suggested_location_weights": {k: float(f"{float(v):.2f}") for k, v in loc_weights.items()},
            "suggested_time_weights": {f"{k:02d}:00": float(f"{float(v):.2f}") for k, v in time_weights.items()}
        }

    def detect_seasonality(self, df: pd.DataFrame) -> list[dict]:
        """
        Detects spikes in booking volume per day to suggest 'Events'.
        Assuming 'date' or 'day' column exists.
        """
        if 'date' not in df.columns and 'day' not in df.columns:
            return []
            
        col = 'date' if 'date' in df.columns else 'day'
        daily_counts = df[col].value_counts()
        mean_vol = daily_counts.mean()
        std_vol = daily_counts.std()
        
        # Threshold: Mean + 1.5 * StdDev
        threshold = mean_vol + (1.5 * std_vol)
        spikes = daily_counts[daily_counts > threshold]
        
        events = []
        for date, count in spikes.items():
            events.append({
                "day": str(date),
                "volume": int(count),
                "multiplier_suggestion": round(count / mean_vol, 1)
            })
        return events
