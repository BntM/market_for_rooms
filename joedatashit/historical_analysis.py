import pandas as pd
import numpy as np
import json
import os

class HistoricalAnalyst:
    def __init__(self, data_path=None):
        self.data_path = data_path
        
    def analyze_demand(self, df):
        """
        Analyzes historical (or scraped) data to indentify density.
        Calculates suggested multipliers for the Enterprise.
        """
        if df.empty:
            return {}
            
        # 1. Location Popularity (Inversely proportional to availability if current data, 
        # or proportional to occupancy if historical)
        # For now, let's assume higher count in available data means lower relative demand
        loc_counts = df['location'].value_counts()
        mean_supply = loc_counts.mean()
        
        # Suggested weight = Mean / Local_Supply (Scarce locations get higher weights)
        loc_weights = (mean_supply / loc_counts).to_dict()
        
        # 2. Time of Day (Peak hours)
        # Let's extract hour from a 'time_slot' column if it exists
        if 'time_slot' in df.columns:
            # Assuming format 'HH:MM'
            df['hour'] = df['time_slot'].apply(lambda x: int(x.split(':')[0]) if ':' in str(x) else 12)
            hour_counts = df['hour'].value_counts()
            mean_hour = hour_counts.mean()
            time_weights = (mean_hour / hour_counts).to_dict()
        else:
            time_weights = {}

        return {
            "suggested_location_weights": {k: float(f"{float(v):.2f}") for k, v in loc_weights.items()},
            "suggested_time_weights": {f"{k:02d}:00": float(f"{float(v):.2f}") for k, v in time_weights.items()}
        }

    def generate_initial_config(self, analysis):
        config = {
            "base_price": 10,
            "weights": {
                "location": analysis.get("suggested_location_weights", {}),
                "time": analysis.get("suggested_time_weights", {}),
                "capacity": {"2": 1.0, "4": 1.5, "10": 3.0} # Heuristic
            }
        }
        return config

if __name__ == "__main__":
    # Example usage with mock data
    data = [
        {"location": "Library", "time_slot": "10:00"},
        {"location": "Library", "time_slot": "11:00"},
        {"location": "Student Center", "time_slot": "10:00"},
        {"location": "North Campus", "time_slot": "10:00"},
        {"location": "North Campus", "time_slot": "11:00"},
        {"location": "North Campus", "time_slot": "12:00"},
    ]
    df = pd.DataFrame(data)
    analyst = HistoricalAnalyst()
    results = analyst.analyze_demand(df)
    print(json.dumps(results, indent=2))
