import numpy as np
import pandas as pd
import random
import json
from datetime import datetime, timedelta

class RoomMarketSimulator:
    def __init__(self, base_price=10):
        self.base_price = base_price
        self.rooms = []
        self.agents = []
        self.history = []
        
    def setup_rooms(self, num_rooms=20):
        locations = ["Library", "Student Center", "Engineering Hall", "North Campus"]
        capacities = [2, 4, 6, 10]
        
        for i in range(num_rooms):
            self.rooms.append({
                "id": f"room_{i}",
                "location": random.choice(locations),
                "capacity": random.choice(capacities),
                "status": "available"
            })
            
    def setup_agents(self, num_agents=100, initial_tokens=50):
        agent_types = ["The Procrastinator", "The Early Bird", "The Group Planner", "The Regular"]
        
        for i in range(num_agents):
            a_type = random.choice(agent_types)
            # Higher budget for early birds, lower for procrastinators
            budget_mult = 1.5 if a_type == "The Early Bird" else 0.8 if a_type == "The Procrastinator" else 1.0
            
            self.agents.append({
                "id": f"agent_{i}",
                "type": a_type,
                "tokens": initial_tokens * budget_mult,
                "pref_location": random.choice(["Library", "Student Center", "Engineering Hall"]),
                "pref_capacity": random.choice([2, 4, 6]),
                "urgency": random.uniform(0.5, 2.0) if a_type == "The Procrastinator" else random.uniform(0.1, 0.5)
            })

    def calculate_price(self, room, tte_days, weights, scarcity):
        """
        tte_days: Time To Event (days)
        weights: Dictionary of weight multipliers
        scarcity: Float 0.0 to 1.0 (portion of rooms filled)
        """
        w_loc = weights['location'].get(room['location'], 1.0)
        w_cap = weights['capacity'].get(str(room['capacity']), 1.0)
        
        # Airline U-Curve Logic
        if tte_days > 10:
            w_tte = 2.5 # Anti-hoarding
        elif 3 <= tte_days <= 10:
            w_tte = 0.8 # Clearance
        else:
            w_tte = 1.5 + (1.0 / (tte_days + 0.1)) # Last minute spike
            
        scarcity_mult = 1.0 + (scarcity ** 2) * 2.0
        
        price = self.base_price * w_loc * w_cap * w_tte * scarcity_mult
        return round(price, 2)

    def run_simulation(self, days=14, weights=None, token_drip=5):
        if weights is None:
            weights = {
                "location": {"Library": 1.3, "Student Center": 1.2, "Engineering Hall": 1.1},
                "capacity": {"2": 1.0, "4": 1.4, "6": 1.8, "10": 2.5}
            }
            
        results = []
        
        for day in range(days):
            # Token distribution (Weekly or Daily)
            for agent in self.agents:
                agent['tokens'] += token_drip
            
            # Booking attempts
            day_bookings = 0
            scarcity = day_bookings / len(self.rooms)
            
            # Simulating agent decision cycles
            for _ in range(3): # 3 cycles per day
                random.shuffle(self.agents)
                for agent in self.agents:
                    # Choose a random available room
                    available_rooms = [r for r in self.rooms if r['status'] == "available"]
                    if not available_rooms:
                        break
                        
                    room = random.choice(available_rooms)
                    tte = days - day # How many days until the slot session starts
                    
                    price = self.calculate_price(room, tte, weights, scarcity)
                    
                    # Decision Logic: Buy if utility > price
                    # Utility = (PrefWeight * BaseValue) / urgency
                    pref_mult = 1.5 if room['location'] == agent['pref_location'] else 1.0
                    utility = (50.0 * pref_mult) / float(agent['urgency'])
                    
                    if float(agent['tokens']) >= price and utility >= price:
                        agent['tokens'] = float(agent['tokens']) - price
                        room['status'] = "booked"
                        day_bookings = day_bookings + 1
                        scarcity = day_bookings / len(self.rooms)
                        
                        results.append({
                            "day": day,
                            "agent_id": agent['id'],
                            "agent_type": agent['type'],
                            "room_id": room['id'],
                            "price_paid": price,
                            "tte": tte
                        })
            
            # Reset rooms for next day simulation (simplified)
            for r in self.rooms:
                r['status'] = "available"
                
        return pd.DataFrame(results)

if __name__ == "__main__":
    sim = RoomMarketSimulator()
    sim.setup_rooms()
    sim.setup_agents()
    df = sim.run_simulation()
    print(df.head())
    print(f"Total Bookings: {len(df)}")
