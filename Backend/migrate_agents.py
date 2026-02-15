
import sqlite3

def migrate():
    conn = sqlite3.connect('market.db')
    cursor = conn.cursor()
    
    # Check if 'is_simulated' exists
    try:
        cursor.execute("ALTER TABLE agents ADD COLUMN is_simulated BOOLEAN DEFAULT 0")
        print("Added is_simulated")
    except sqlite3.OperationalError:
        print("is_simulated already exists")
        
    try:
        cursor.execute("ALTER TABLE agents ADD COLUMN behavior_risk_tolerance FLOAT DEFAULT 0.5")
        print("Added behavior_risk_tolerance")
    except sqlite3.OperationalError:
        print("behavior_risk_tolerance already exists")

    try:
        cursor.execute("ALTER TABLE agents ADD COLUMN behavior_price_sensitivity FLOAT DEFAULT 0.5")
        print("Added behavior_price_sensitivity")
    except sqlite3.OperationalError:
        print("behavior_price_sensitivity already exists")

    try:
        cursor.execute("ALTER TABLE agents ADD COLUMN behavior_flexibility FLOAT DEFAULT 0.5")
        print("Added behavior_flexibility")
    except sqlite3.OperationalError:
        print("behavior_flexibility already exists")
        
    try:
        cursor.execute("ALTER TABLE agents ADD COLUMN behavior_preferred_days VARCHAR DEFAULT '0,1,2,3,4'")
        print("Added behavior_preferred_days")
    except sqlite3.OperationalError:
        print("behavior_preferred_days already exists")

    try:
        cursor.execute("ALTER TABLE agents ADD COLUMN behavior_preferred_period VARCHAR DEFAULT 'any'")
        print("Added behavior_preferred_period")
    except sqlite3.OperationalError:
        print("behavior_preferred_period already exists")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
