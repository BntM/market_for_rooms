import numpy as np
import pandas as pd
import random
from typing import List, Dict, Any, Optional

class RoomMarketSimulator:
    def __init__(self, base_price=10):
        self.base_price = base_price
        self.rooms = []
        self.agents = []
        self.history = []
        
    def setup_rooms(self, num_rooms=20, locations=None, capacities=None, existing_rooms=None):
        if existing_rooms:
            self.rooms = []
            for r in existing_rooms:
                self.rooms.append({
                    "id": str(r.id),
                    "location": r.location,
                    "capacity": r.capacity,
                    "status": "available"
                })
            return

        if not locations:
            locations = ["Library", "Student Center", "Engineering Hall", "North Campus"]
        if not capacities:
            capacities = [2, 4, 6, 10]
        
        self.rooms = []
        for i in range(num_rooms):
            self.rooms.append({
                "id": f"room_{i}",
                "location": random.choice(locations),
                "capacity": random.choice(capacities),
                "status": "available"
            })
            
    def setup_agents_advanced(self, agent_configs: List[Dict[str, Any]]):
        """
        agent_configs: List of dicts like {"name": "Rich Student", "budget_mult": 2.0, "urgency_min": 0.1, "urgency_max": 0.3, "count": 50}
        """
        self.agents = []
        aid = 0
        for config in agent_configs:
            count = config.get("count", 0)
            for _ in range(count):
                self.agents.append({
                    "id": f"agent_{aid}",
                    "type": config.get("name", "Unknown"),
                    "tokens": 50 * config.get("budget_mult", 1.0),
                    "pref_location": config.get("pref_location") or random.choice(["Library", "Student Center", "Engineering Hall"]),
                    "urgency": random.uniform(config.get("urgency_min", 0.1), config.get("urgency_max", 1.0))
                })
                aid += 1

    def calculate_price(self, room, tte_days, weights, scarcity):
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
        return max(round(price, 2), 1.0) # Min price 1

    def run_simulation(self, days=14, weights=None, token_drip=5, events: Dict[int, float] = None) -> List[Dict]:
        """
        events: Dict of {day_index: demand_multiplier}
        """
        if weights is None:
            weights = {
                "location": {"Library": 1.3, "Student Center": 1.2, "Engineering Hall": 1.1},
                "capacity": {"2": 1.0, "4": 1.4, "6": 1.8, "10": 2.5}
            }
        if events is None:
            events = {}
            
        results = []
        
        for day in range(days):
            # Token distribution
            for agent in self.agents:
                agent['tokens'] += token_drip
            
            # Booking attempts
            day_bookings = 0
            scarcity = 0.0
            
            # Event Multiplier (Seasonality)
            demand_mult = events.get(day, 1.0)
            
            # Simulating agent decision cycles
            # Higher demand mult = more cycles or more agents active
            cycles = int(3 * demand_mult)
            
            for _ in range(cycles):
                random.shuffle(self.agents)
                for agent in self.agents:
                    available_rooms = [r for r in self.rooms if r['status'] == "available"]
                    if not available_rooms:
                        available_rooms = [r for r in self.rooms if r['status'] == "available"]
                    
                    if not available_rooms:
                        break
                        
                    room = random.choice(available_rooms)
                    tte = days - day 
                    
                    scarcity = day_bookings / len(self.rooms)
                    price = self.calculate_price(room, tte, weights, scarcity)
                    
                    # Decision Logic
                    pref_mult = 1.5 if room['location'] == agent['pref_location'] else 1.0
                    
                    # Urgency increases effectively if event is today
                    effective_urgency = agent['urgency'] / demand_mult 
                    
                    utility = (50.0 * pref_mult) / float(effective_urgency)
                    
                    if float(agent['tokens']) >= price and utility >= price:
                        agent['tokens'] = float(agent['tokens']) - price
                        room['status'] = "booked"
                        day_bookings += 1
                        
                        results.append({
                            "day": day,
                            "agent_id": agent['id'],
                            "agent_type": agent['type'],
                            "room_id": room['id'],
                            "price_paid": price,
                            "tte": tte,
                            "revenue": price
                        })
            
            # Reset rooms
            for r in self.rooms:
                r['status'] = "available"
                
        return results

    def optimize_price(self, base_price_range: List[int], agent_configs, weights, events, existing_rooms=None) -> Dict:
        """Runs simulations for multiple base prices and returns the best one."""
        best_price = 0
        max_revenue = 0
        results = {}
        
        for price in base_price_range:
            self.base_price = price
            if existing_rooms:
                self.setup_rooms(existing_rooms=existing_rooms)
            else:
                self.setup_rooms(num_rooms=40) # Fixed for optimization
            self.setup_agents_advanced(agent_configs)
            
            sim_results = self.run_simulation(days=14, weights=weights, events=events)
            total_rev = sum(r['price_paid'] for r in sim_results)
            results[price] = total_rev
            
            if total_rev > max_revenue:
                max_revenue = total_rev
                best_price = price
                
        return {"best_base_price": best_price, "max_revenue": max_revenue, "all_results": results}
