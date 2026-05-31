import sqlite3
import os
from typing import Dict, Any, List

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "opn_leads.db")

def init_db():
    """
    Initializes the SQLite database and creates the leads table if it doesn't exist.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if we need to upgrade the table (e.g. if lead_type is missing)
    cursor.execute("PRAGMA table_info(leads)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if columns and "lead_type" not in columns:
        cursor.execute("DROP TABLE leads")
        
    # Elegant, clean schema reflecting high-converting CRO pipeline with support for lead magnets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            property_type TEXT,
            location TEXT,
            project_stage TEXT,
            budget_range TEXT,
            score INTEGER NOT NULL,
            is_vip INTEGER DEFAULT 0, -- Boolean: 0 or 1
            whatsapp_url TEXT,
            status TEXT DEFAULT 'new', -- 'new', 'contacted', 'scheduled', 'won', 'lost'
            lead_type TEXT DEFAULT 'consultation', -- 'consultation', 'lead_magnet'
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_lead(lead_data: Dict[str, Any], score: int, is_vip: bool, whatsapp_url: str) -> int:
    """
    Saves a scored lead into the database.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO leads (
            name, email, phone, property_type, location, project_stage, budget_range, score, is_vip, whatsapp_url, lead_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead_data.get("name"),
        lead_data.get("email"),
        lead_data.get("phone"),
        lead_data.get("property_type"),
        lead_data.get("location"),
        lead_data.get("project_stage"),
        lead_data.get("budget_range"),
        score,
        1 if is_vip else 0,
        whatsapp_url,
        lead_data.get("lead_type", "consultation")
    ))
    
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return lead_id

def get_all_leads() -> List[Dict[str, Any]]:
    """
    Retrieves all leads from the database, sorted by score and date.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM leads ORDER BY is_vip DESC, score DESC, created_at DESC")
    rows = cursor.fetchall()
    
    leads = [dict(row) for row in rows]
    conn.close()
    return leads

def update_lead_status(lead_id: int, status: str, notes: str = None) -> bool:
    """
    Updates the pipeline status or adds notes to a lead.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    if notes:
        cursor.execute("UPDATE leads SET status = ?, notes = ? WHERE id = ?", (status, notes, lead_id))
    else:
        cursor.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
        
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def get_analytics_summary() -> Dict[str, Any]:
    """
    Aggregates lead engine metrics for the CRM dashboard.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM leads")
    total_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE is_vip = 1")
    vip_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE lead_type = 'lead_magnet'")
    magnet_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE lead_type = 'consultation'")
    consultation_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(score) FROM leads")
    avg_score = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT budget_range, COUNT(*) FROM leads WHERE lead_type = 'consultation' GROUP BY budget_range")
    budgets = dict(cursor.fetchall())
    
    cursor.execute("SELECT project_stage, COUNT(*) FROM leads WHERE lead_type = 'consultation' GROUP BY project_stage")
    stages = dict(cursor.fetchall())
    
    cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
    statuses = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        "total_leads": total_leads,
        "vip_leads": vip_leads,
        "magnet_leads": magnet_leads,
        "consultation_leads": consultation_leads,
        "avg_score": round(avg_score, 1),
        "budgets": budgets,
        "stages": stages,
        "statuses": statuses
    }
