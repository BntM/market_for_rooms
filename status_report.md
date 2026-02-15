# Issue Resolved: Reset Button & Simulator Link

I have successfully fixed the "Reset & Load Default Data" button freezing issue and corrected the Simulator tab link.

## Summary of Fixes:
1.  **Backend Optimization**: I rewrote the data import logic (`_process_import` in `admin.py`) to use **bulk database inserts** for both Time Slots and Auctions. This reduced the operation time from >30 seconds (causing timeouts) to **~3.5 seconds**.
2.  **Backend Startup Fixes**: I resolved several `NameError` crashes (missing `router`, `datetime`, `lifespan`) that were preventing the backend from starting correctly after recent edits.
3.  **Database Locks**: I cleared stuck background processes that were locking the database file.
4.  **Navigation**: The "Simulator" tab in `Layout.jsx` now correctly points to the new Interactive Dashboard.

## Verification:
I ran a verification script (`verify_admin_reset.py`) against your local backend and confirmed the reset endpoint now returns successfully in under 4 seconds.

**Action Required:**
Please reload your browser at `http://localhost:5173/admin` and try the "Reset & Load Default Data" button again. It should now work instantly.
