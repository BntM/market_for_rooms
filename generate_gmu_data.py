import csv
import random
from datetime import datetime, timedelta

def generate_data():
    start_date = datetime.now().date()
    days = 14
    
    buildings = {
        "Fenwick Library": [f"Fenwick {room}" for room in ["1014", "2020", "3001", "4004", "5005"]],
        "Mason Square Library": [f"Arlington {room}" for room in ["111", "222", "333"]],
        "Mercer Library": [f"Mercer {room}" for room in ["A", "B", "C", "D"]],
        "Innovation Hall": [f"Innovation {room}" for room in ["101", "102", "201", "202"]],
        "Johnson Center": [f"JC Meeting Room {room}" for room in ["A", "B", "C", "D", "E", "F"]],
        "The Hub": [f"Hub Meeting Room {room}" for room in ["1", "2", "3", "4"]]
    }
    
    capacities = {
        "Fenwick Library": 4,
        "Mason Square Library": 6,
        "Mercer Library": 8,
        "Innovation Hall": 10,
        "Johnson Center": 10,
        "The Hub": 12
    }
    
    rows = []
    headers = ["Building", "Room Name", "Capacity", "Date", "Time", "Status"]
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Booking probability (higher on weekdays?)
        is_weekend = current_date.weekday() >= 5
        base_book_prob = 0.2 if is_weekend else 0.4
        
        for building, rooms in buildings.items():
            cap = capacities[building]
            
            for room in rooms:
                # 9 AM to 9 PM
                for hour in range(9, 21):
                    for minute in [0, 30]:
                        time_str = f"{hour:02d}:{minute:02d}"
                        
                        # Randomly determining status based on time of day
                        # Peak hours 11-3
                        peak_multiplier = 1.5 if 11 <= hour <= 15 else 1.0
                        prob = base_book_prob * peak_multiplier
                        
                        status = "Booked" if random.random() < prob else "Available"
                        
                        rows.append([
                            building,
                            room,
                            str(cap),
                            date_str,
                            time_str,
                            status
                        ])
                        
    with open("gmu_room_data_full.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
        
    print(f"Generated {len(rows)} rows of data.")

if __name__ == "__main__":
    generate_data()
