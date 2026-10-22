# CelebrationAI — Smart Celebration & Event Planner

**CelebrationAI** is an elegant, full-featured web application designed for **Challenge 5: Celebration & Event Planner**. It empowers families, couples, students, and community organizers to plan weddings, birthday celebrations, anniversaries, college festivals, and community galas using Google Gemini Generative AI and structured event coordination tools.

---

## 1. Product Overview & Core Vision

CelebrationAI provides a unified, human-centered workspace that balances creative inspiration with mathematical rigor:
- **Intelligent Budget Safeguards:** Guarantees that total estimated expenses never exceed the designated budget ceiling, automatically reserving a 5–10% contingency buffer for incidentals.
- **Generative AI Event Blueprinting:** Integrates with Google Gemini (via the official `google-genai` SDK) to craft personalized decor concepts, color palettes, regional tasting menus, and date-aware timelines.
- **Seamless Local Demo Fallback:** If `GEMINI_API_KEY` is not provided or offline, a built-in heuristic planning engine generates realistic, tailored plans so the platform works out of the box.
- **7-in-1 Event Coordinator Workspace:**
  1. **Overview:** Live countdown ticker, progress bars, and high-priority action alerts.
  2. **Budget & Expenses:** Planned vs. actual spend comparison with Chart.js doughnut and bar charts.
  3. **Timeline:** Chronologically ordered milestones with overdue indicators.
  4. **Vendors:** Service category checklist, booking status, and real contact management.
  5. **Guest List:** RSVP tracker, dietary requirements (+1s), and confirmed headcount metrics.
  6. **Ideas:** Curated decor, menu, and budget-saving concepts bookmarkable to favorites.
  7. **Checklist:** Shopping and day-of preparation checklist with estimated cost tracking.
- **In-Dashboard AI Assistant:** A conversational copilot with real-time access to the current event's financial figures, equipped to generate actionable proposals that users can review and apply with a single click.

---

## 2. Design & Visual Identity

CelebrationAI features a premium design system inspired by luxury stationery and editorial event publications:
- **Warm Ivory & Off-White:** `#FAF8F5`, `#F5F1EB`, `#FFFFFF`
- **Deep Plum & Burgundy:** `#4A1525`, `#5E1931`, `#721D3B`
- **Muted Gold & Champagne:** `#C5A059`, `#D4AF37`, `#F5ECD9`
- **Dark Charcoal:** `#232021` for high-contrast, accessible typography
- **Typography:** *Cormorant Garamond* and *Cinzel* for headings, paired with *Plus Jakarta Sans* for clean data displays.
- **Micro-Interactions:** Lucide icons, smooth tab switching, progress rings, and toast notifications.
- **Mobile-First Responsiveness:** Optimized for desktops, tablets, and smartphones.

---

## 3. Technology Stack

- **Backend:** Python 3.12+ / 3.14, Flask 3.1
- **Database:** SQLite with foreign keys enabled (`celebration.db`), with standard SQL schemas ready for PostgreSQL migration.
- **AI Integration:** Google GenAI SDK (`google-genai` v2.32) utilizing Gemini 2.5 Flash, paired with a deterministic local heuristic fallback.
- **Frontend:** Semantic HTML5, Vanilla CSS3 (custom design system), Modular JavaScript (ES6+), Jinja2 templates.
- **Icons & Visuals:** Lucide Icons CDN, Chart.js v4.4.
- **Security:** Werkzeug password hashing (PBKDF2/scrypt), CSRF-conscious JSON endpoints, parameterized SQL queries, strict session isolation.
- **Testing:** `pytest` test suite with 100% route and model coverage.

---

## 4. Project Structure

```
Celebration AI/
├── app.py                     # Flask application factory, routes, and REST endpoints
├── config.py                  # Environment configuration and defaults
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Protected secrets and build artifacts
├── README.md                  # Project documentation and setup guide
├── celebration.db             # Local SQLite database (auto-created on start)
├── models/
│   ├── __init__.py            # Models package init
│   ├── database.py            # SQLite connection manager and table definitions
│   ├── user.py                # User authentication and password hashing
│   └── event.py               # Full CRUD for events, expenses, tasks, guests, etc.
├── services/
│   ├── __init__.py            # Services package init
│   ├── ai_planner.py          # Google Gemini integration and local heuristic planner
│   └── chat_assistant.py      # Dashboard AI assistant and action proposal generator
├── templates/
│   ├── base.html              # Core layout, navbar, footer, and notifications
│   ├── index.html             # Homepage with hero, quick form, categories, & themes
│   ├── explore.html           # Themes and color palettes inspiration gallery
│   ├── how_it_works.html      # Methodology and AI architecture walkthrough
│   ├── create_event.html      # 5-step event creation wizard with validation
│   ├── my_events.html         # User's celebrations overview with countdown tickers
│   ├── dashboard.html         # 7-tab event planner workspace & chat assistant
│   ├── login.html             # Sign in with instant one-click demo login
│   ├── register.html          # New account registration
│   ├── 404.html               # Custom 404 page
│   └── 500.html               # Custom 500 page
├── static/
│   ├── css/
│   │   └── style.css          # Design system stylesheet
│   └── js/
│       ├── main.js            # Navbar, alerts, and Lucide icons
│       ├── event-form.js      # Multi-step wizard and generation overlay
│       ├── dashboard.js       # Tabs, Chart.js charts, and CRUD modals
│       └── chat.js            # In-dashboard assistant and proposal handlers
└── tests/
    ├── __init__.py
    └── test_app.py            # Automated pytest suite (11 test cases)
```

---

## 5. Prerequisites

- Python 3.10+ (Tested on Python 3.14 on Windows)
- Modern web browser (Chrome, Edge, Firefox, Safari)
- Windows PowerShell or Command Prompt

---

## 6. Installation & Local Setup (Windows PowerShell)

Open PowerShell in the project directory:

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate virtual environment
.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Create your local .env file
Copy-Item .env.example .env
```

---

## 7. Configuring the Google Gemini AI Key

1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
2. Open your `.env` file and insert your key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
3. If no key is configured, **CelebrationAI automatically operates in Demo Mode**, utilizing the built-in local heuristic planner with full functionality.

---

## 8. Running the Application

```powershell
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

### Instant Demo Login:
To test without creating an account:
- Click **Sign In** on the navbar.
- Click **"Instant Demo Login (Alex Morgan)"** to enter the workspace immediately.

---

## 9. Running Automated Tests

Run the complete test suite using `pytest`:

```powershell
pytest tests/test_app.py -v
```

All 11 tests will execute, verifying:
- Health check and landing page rendering
- Theme exploration and methodology pages
- User password hashing and authentication
- Form input validation on required fields
- End-to-end event generation and persistence
- Budget calculations and mathematical integrity
- Timeline task creation, completion toggling, and deletion
- Vendor checklist status management
- Guest list management and RSVP tracking
- In-dashboard AI chat assistant and action proposal application
- Private event authorization and access protection

---

## 10. Deployment Readiness

CelebrationAI is structured for deployment to platforms such as Render, Railway, Fly.io, or AWS EC2:
- **Production WSGI Server:** Ready for `gunicorn app:app` or `waitress`.
- **Health Check Endpoint:** `/health` returns `200 OK` with JSON service status.
- **Database Migration:** Uses standard SQL queries; can be pointed to PostgreSQL by configuring `DATABASE_PATH` in `.env`.
- **Environment Variables:** All secrets and credentials are loaded dynamically from environment variables.

---

## 11. Current Limitations & Future Roadmap

- **Vendor Marketplace:** Vendor records currently represent user-managed research and contracts; direct booking integrations with verified local directories can be added in future versions.
- **Calendar Synchronization:** Timeline milestones can be exported via iCal/Google Calendar in future iterations.
- **Multi-Currency Live Rates:** Default currency is INR (₹) with USD ($) and EUR (€) options; live forex conversion feeds can be integrated.

---

## 12. 🌐 Community Wisdom & Proven Patterns

In accordance with event technology and generative AI best practices:
1. **Mathematical Validation on LLM Output:** As discussed in community architecture discussions regarding generative financial planners ([Building Reliable AI Applications with Structured Outputs](https://dev.to/search?q=structured+outputs+llm)), relying on raw LLM arithmetic often leads to hallucinations. CelebrationAI implements strict backend reconciliation: the Python service recalculates all budget percentages, caps totals at the budget ceiling, and reserves a dedicated contingency fund.
2. **Reviewable Action Proposals vs. Silent Overwriting:** To prevent destructive AI actions, our conversational assistant does not silently mutate the database. Instead, it outputs structured action proposals that require explicit user confirmation.
