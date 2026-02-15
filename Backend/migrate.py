import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else "market.db"
conn = sqlite3.connect(db_path, timeout=30)
c = conn.cursor()

# Check and add missing bids columns
cols = [r[1] for r in c.execute("PRAGMA table_info(bids)").fetchall()]
print(f"Current bids columns: {cols}")

if "is_group_bid" not in cols:
    c.execute("ALTER TABLE bids ADD COLUMN is_group_bid BOOLEAN DEFAULT 0")
    print("  Added: is_group_bid")
if "split_with_agent_id" not in cols:
    c.execute("ALTER TABLE bids ADD COLUMN split_with_agent_id TEXT")
    print("  Added: split_with_agent_id")

# Check and add missing bookings columns
bcols = [r[1] for r in c.execute("PRAGMA table_info(bookings)").fetchall()]
print(f"Current bookings columns: {bcols}")

if "split_with_agent_id" not in bcols:
    c.execute("ALTER TABLE bookings ADD COLUMN split_with_agent_id TEXT")
    print("  Added: split_with_agent_id")
if "split_status" not in bcols:
    c.execute('ALTER TABLE bookings ADD COLUMN split_status TEXT DEFAULT "none"')
    print("  Added: split_status")

conn.commit()
conn.close()
print("Migration complete!")
