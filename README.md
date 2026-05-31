# Omer Paz Nir (OPN Design) - High-Converting Lead Generation Architecture

This repository contains the complete, production-grade backend engine and high-converting lead funnel designed to integrate seamlessly with the elegant portfolio website of **Omer Paz Nir - Interior Design** (https://opndesign.com/).

The goal is to turn passive portfolio visitors into high-value, scheduled consultations while respecting the clean, high-end minimalist brand identity of the studio.

---

## 🏗️ 1. Technical Architecture & File Structure

This backend is structured as a robust microservice using **FastAPI** (Python 3.8+) and a self-contained SQLite relational database. It is designed to be easily deployed to a cloud server (Vercel, Render, Heroku, AWS, or DigitalOcean) and hooked up to the main website frontend via standard AJAX calls.

### Repository Layout
- `main.py`: The FastAPI application server that registers leads, scores them, triggers VIP notifications, and returns tracking payloads. It also serves a stunning glassmorphic, Hebrew-localized interactive preview at `http://127.0.0.1:8000/`.
- `scoring.py`: Core business logic that handles multi-tier lead grading (assigning priority scores) and constructs custom, tracked WhatsApp message strings.
- `database.py`: Clean, repository-pattern interface for SQLite/PostgreSQL storage, ensuring database safety, indexing, and pipeline management.
- `opn_leads.db`: Self-managed SQLite database file (created automatically on startup).

---

## 🗄️ 2. The Database Schema
The database uses a highly focused CRM schema designed specifically for high-ticket service sales tracking:

```sql
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    property_type TEXT NOT NULL,  -- 'private_house', 'contractor_apartment', 'renovation'
    location TEXT NOT NULL,       -- Custom input (bonus points for premium areas)
    project_stage TEXT NOT NULL,  -- 'pre_construction', 'under_construction', 'ready_to_move'
    budget_range TEXT NOT NULL,   -- 'low', 'mid', 'high', 'ultra'
    score INTEGER NOT NULL,       -- Lead Score (0 - 100)
    is_vip INTEGER DEFAULT 0,     -- Boolean (0 or 1) indicating Top Tier priority
    whatsapp_url TEXT,            -- Presaved dynamic contact URL
    status TEXT DEFAULT 'new',    -- 'new', 'contacted', 'scheduled', 'won', 'lost'
    notes TEXT,                   -- Admin follow-up annotations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Why this schema works for CRO:
- **`score` and `is_vip`**: Immediate indices that bubble the best projects to the top.
- **`status` tracking**: Allows the studio to track conversion progression directly (from registration to booked consultation).
- **Flexibility**: Lightweight enough to run on SQLite locally or scale to Postgres in production by changing standard database drivers.

---

## 🧠 3. Elite Lead Scoring Algorithm
In interior design—especially in Israel—**Early Contractor Modifications (שינויי דיירים בשלב הקבלן)** represent the highest-margin and highest-value opportunity for designers. If a client hires a designer *before* the contractor finishes building, they save massive amounts of money, and the designer has full layout freedom.

Our algorithm ranks leads accordingly:
- **Property Type**: Private House (25 pts), Contractor Apartment (20 pts), Renovation (15 pts).
- **Stage**: Pre-construction / Planning (35 pts - *designer's sweet spot*), Active construction (20 pts), Handover ready (10 pts).
- **Budget**: Ultra 600k+ NIS (50 pts), High 300k-600k NIS (35 pts), Mid 100k-300k NIS (15 pts), Low (0 pts).
- **High-Value Location**: Standard prime regions (Tel Aviv, Sharon Area, Savyon, Herzliya, etc.) receive an automatic +10 bonus points.
- **VIP Designation**: Automatic trigger if `score >= 75`, `budget == "ultra"`, or the lead is `high budget` AND `pre-construction stage`.

---

## 💬 4. Dynamic WhatsApp Link Automation
Standard forms often suffer from "submission drop-off"—leads fill out details but never answer follow-up calls. Our system implements a **Dual-Action conversion funnel**:
1. Lead submits the form (instantly stored in the backend database).
2. The UI instantly transforms, displaying a success panel with a high-priority call-to-action button: **"Send my Project Concept details to Omer via WhatsApp"**.
3. Clicking this button launches a pre-filled, highly professional WhatsApp message containing their formatted answers, looking like this:

> *"שלום עומר! מילאתי את מתכנן הפרויקטים באתר שלך. הנה פרטי הנכס שלי:*
>
> *👤 שם: מיכל כהן*
> *📍 מיקום: הרצליה פיתוח*
> *🏗️ סוג הפרויקט: דירת קבלן (שינויי דיירים) 🏗️*
> *⏱️ שלב הפרויקט: לפני בנייה / שינויי דיירים מוקדמים (תכנון)*
> *💰 תקציב מוערך: 300,000 ₪ - 600,000 ₪*
>
> *אשמח לקבוע איתך פגישת ייעוץ ראשונית כדי שנוכל לדבר על הפרויקט ולבחון התאמה. תודה!"*

This eliminates friction and puts the hot lead directly in Omer's active WhatsApp chat!

---

## 📈 5. Front-End UX/UI Integration Blueprint

To integrate these high-converting mechanisms into the minimalist React/HTML code of https://opndesign.com/, apply these guidelines:

### A. The Persistent & Native "Book a Consultation / תיאום פגישת ייעוץ" CTA
- **Placement**: A persistent, elegant "floating action button" (FAB) or a sticky header element. On mobile, it should stick to the bottom of the viewport with a frosted glass effect (`backdrop-filter: blur()`).
- **Aesthetic**: Minimalist typography. Transparent dark gray or soft gold background (`#C5A880`) matching the current portfolio tones. Do not use bright red or glowing greens which cheapen the high-end residential brand.
- **Micro-interactions**: Subtle hover state shifting background scale, or a soft pulsing shadow effect.
- **Visual implementation**:
  ```css
  .sticky-cta {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: rgba(28, 28, 28, 0.9);
      color: #FAF8F5;
      border: 1px solid rgba(197, 168, 128, 0.4);
      padding: 14px 28px;
      border-radius: 50px;
      font-size: 15px;
      font-weight: 600;
      letter-spacing: 1px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
      z-index: 1000;
      transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
  }
  .sticky-cta:hover {
      background: #C5A880;
      transform: translateY(-2px);
      box-shadow: 0 12px 40px 0 rgba(197, 168, 128, 0.25);
  }
  ```

### B. High-Converting Alternative Lead Magnet: "5 Contractor Apartment Mistakes" Guide
Many high-value visitors are 6-12 months away from construction and are not ready to "book a call" yet. A guide magnet captures their contact info early!
- **Placement**: Under portfolio projects (especially "Contractor Apartments") or in a subtle exit-intent popup.
- **The Concept**: "מדריך קבלן: 5 טעויות תכנון שיעלו לכם עשרות אלפי שקלים (וקראו איך להימנע מהן)."
- **Workflow**:
  - The visitor enters their Name, Email, and Phone to download the free PDF guide.
  - The backend receives the request, stores the contact as a "Guide Lead," and triggers a WhatsApp URL generation or automated email containing the PDF.
  - **VIP Trigger**: A follow-up automated message is sent via WhatsApp to the user 5 minutes later:
    *"היי [Name], שלחתי לך את המדריך למייל. מאחר וציינת שרכשת דירת קבלן, רציתי לעדכן שיש לעומר 2 מקומות פנויים בלבד לליווי פרויקטים ברבעון הקרוב. האם תרצי שנתאם שיחה קצרה לבדוק אם נוכל לעזור בתכנון המוקדם?"*

---

## 🚀 6. Step-by-Step Technical Setup & Running Locally

Follow these instructions to run and test this backend in a local environment:

### Step 1: Install Dependencies
Open your terminal and run:
```bash
pip install fastapi uvicorn pydantic
```

### Step 2: Launch the Backend Service
From this directory, execute:
```bash
python main.py
```
You will see uvicorn start a web server on `http://127.0.0.1:8000`.

### Step 3: Open the Interactive Form
Open your browser and navigate to `http://127.0.0.1:8000/`.
You will be greeted by a gorgeous, Hebrew-localized minimalist project planner designed to mimic the OPN brand guidelines:
1. Select **Property Type** and **Location**.
2. Define the **Stage** and **Budget**.
3. Provide **Contact Details** and click "Submit".
4. Witness the lead score calculation, VIP classification in the terminal logs, and the dynamic transition to the custom **WhatsApp Redirect**.
