## Inspiration

As students at George Mason University, we've all experienced the frustration of finding a study room during midterms and finals. The current system is first-come, first-served — which means rooms sit empty at 8 AM while students fight over the same 2 PM slots. We asked ourselves: **what if study room allocation was efficient, fair, and intelligent?**

Inspired by real-world financial markets, we built **Market Rooms** — a dynamic pricing marketplace where study rooms are allocated through Dutch auctions. Instead of a race to click "reserve," students place bids and limit orders, and our pricing engine finds the optimal clearing price using multi-agent reinforcement learning. The result? Better utilization, fairer access, and real-time price signals that tell students *exactly* when demand is high or low.

## What it does

**Market Rooms** is a full-stack marketplace platform that transforms university study room booking into a dynamic, AI-driven market:

- **🏛️ Dutch Auction System**: Rooms are sold via descending-price auctions. Prices start high and tick down over time — the first bidder to accept wins the slot. This incentivizes students to reveal their true willingness to pay.
  
- **📊 Dynamic Pricing Engine**: Prices adjust based on demand signals including time-of-day, day-of-week, room capacity, location popularity, and lead time. The pricing formula is:

\\( P = P_{base} \times (w_c \cdot f_{cap} + w_l \cdot f_{loc} + w_t \cdot f_{time} + w_d \cdot f_{day}) \times \delta_{lead} \times G \\)

- **🤖 Patriot AI Assistant (ONEchat Integration)**: Students upload their syllabus PDF, and our Gemini-powered AI extracts exam dates, then automatically places limit orders for study rooms 3 days before each exam — hands-free exam prep scheduling.

- **📈 Multi-Agent Simulation**: An admin dashboard with a PettingZoo-based multi-agent reinforcement learning simulation that models student behavior, tests pricing strategies, and finds optimal market parameters through grid search.

- **💡 AI Market Analysis**: Administrators get Gemini 1.5 Flash-powered strategic reports analyzing demand patterns, revenue trends, and pricing anomalies — all from real marketplace data.

- **🔄 Limit Orders**: Students set a max price and walk away. When the auction price drops to their limit, the order executes automatically — just like a stock market.

## How we built it

**Architecture:**
- **Backend**: FastAPI (Python) with async SQLAlchemy + SQLite, serving a REST API with 50+ endpoints across auctions, agents, resources, simulation, and admin modules.
- **Frontend**: React 18 + Vite, with Chart.js for real-time price visualization and a custom component library styled with inline CSS to match the official GMU Patriot AI (ONEchat) interface.
- **AI Layer**: Google Gemini 1.5 Flash for syllabus parsing, market chat, and admin report generation. PDF text extraction via PyPDF2.
- **Simulation**: PettingZoo multi-agent environment where autonomous agents bid on rooms using configurable strategies (budget-conscious, time-sensitive, aggressive). Grid search over strategy hyperparameters finds Nash equilibrium pricing.
- **Pricing Engine**: Weighted multi-factor model calibrated from scraped LibCal booking data from GMU's Johnson Center and Student Centers.

**Data Pipeline:**
1. Scraped real availability data from `gmu.libcal.com` and `studentcenters-gmu.libcal.com`
2. Fed into a historical analysis module that computes time-of-day and day-of-week demand curves
3. Used these curves to seed the dynamic pricing weights
4. Validated with Monte Carlo simulations across 1,000+ market scenarios

## Challenges we ran into

- **Database Schema Evolution**: As we added features (group bids, split bookings, limit orders), the SQLite schema needed migrations. SQLAlchemy models and the actual DB got out of sync multiple times, causing `OperationalError` crashes that we had to debug live.

- **Styling Without Tailwind**: The Patriot AI chat interface needed to exactly match GMU's official ONEchat design. Without Tailwind CSS in the project, we had to hand-craft every style inline — hundreds of lines of CSS-in-JS for pixel-perfect fidelity.

- **Auction Engine Concurrency**: Dutch auctions tick down in real-time while multiple agents bid simultaneously. Ensuring atomicity (no double-booking, correct price at bid time) with async SQLAlchemy required careful transaction management.

- **Gemini API Integration**: Parsing unstructured syllabus PDFs into structured exam dates required careful prompt engineering. Early prompts returned inconsistent date formats, so we added strict JSON schema instructions and fallback mock data for demo reliability.

- **Multi-Agent RL Convergence**: Getting PettingZoo agents to converge on reasonable bidding strategies required extensive hyperparameter tuning. Agents would either all bid immediately (wasting tokens) or all wait (missing slots).

## Accomplishments that we're proud of

- **End-to-end marketplace**: From PDF upload → AI exam extraction → automatic limit order placement → auction execution → booking confirmation — the entire student workflow is seamless.
- **Real pricing math**: Our dynamic pricing formula uses 6 weighted factors calibrated from real GMU booking data, not arbitrary numbers.
- **Production-quality UI**: The Patriot AI interface is indistinguishable from the real ONEchat — complete with GMU branding, dark green sidebar, gold accents, and responsive layout.
- **50+ API endpoints**: A comprehensive REST API that could power a real university deployment.
- **Multi-agent simulation**: A research-grade PettingZoo environment that generates publishable insights about optimal room pricing strategies.

## What we learned

- **Market design is hard**: Even simple Dutch auctions have edge cases (what happens when nobody bids? when everyone bids at once? when the price floor is too high?). We gained deep appreciation for mechanism design theory.
- **AI as a UX layer**: Using Gemini to parse syllabi transforms a 5-minute manual process into a 10-second upload. LLMs are most powerful when they remove friction, not add complexity.
- **Data-driven pricing works**: Our scraped LibCal data showed clear demand patterns (2-4 PM peak, Monday/Wednesday spike) that our pricing engine learned to exploit. Dynamic pricing isn't just theory — it measurably improves utilization.
- **Full-stack integration complexity**: Connecting React ↔ FastAPI ↔ SQLAlchemy ↔ Gemini ↔ PettingZoo taught us that the hardest bugs live at integration boundaries, not within individual components.

## What's next for Market Rooms

- **🔐 CAS Authentication**: Integrate with GMU's Central Authentication Service so students log in with their Mason NetID.
- **📱 Mobile App**: React Native client for on-the-go bidding with push notifications when limit orders execute.
- **🧠 Predictive Pricing**: Train a transformer model on historical booking data to forecast demand 7 days out and pre-set optimal starting prices.
- **🤝 Group Booking Marketplace**: Let students form study groups and split room costs, with the auction system handling multi-party coordination.
- **🏫 Multi-University Expansion**: Package as a white-label SaaS for any university with shared spaces — libraries, labs, maker spaces.
- **📊 Real LibCal Integration**: Direct API connection to LibCal for live availability sync, replacing the scraping pipeline.
