from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr, Field
import uvicorn
import logging
import os
from typing import Dict, Any, List

from scoring import score_lead, generate_whatsapp_url
from database import init_db, save_lead, get_all_leads, update_lead_status, get_analytics_summary

# Initialize logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Omer Paz Nir (OPN Design) Lead Engine",
    description="Automated premium CRO Lead Qualifier & Multi-channel Routing System",
    version="1.1.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to ['https://opndesign.com']
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup guide path
GUIDE_PATH = os.path.join(os.path.dirname(__file__), "contractor_apartment_guide.pdf")

# Startup event
@app.on_event("startup")
def startup_event():
    init_db()
    logger.info("OPN Lead Database initialized successfully.")

# Pydantic Schemas
class LeadCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, example="מיכל כהן")
    email: EmailStr = Field(..., example="michal@example.com")
    phone: str = Field(..., min_length=9, example="0545555555")
    property_type: str = Field(None, example="contractor_apartment") # 'contractor_apartment', 'renovation', 'private_house', or null for magnet
    location: str = Field(None, example="הרצליה פיתוח")
    project_stage: str = Field(None, example="pre_construction") # 'pre_construction', 'under_construction', 'ready_to_move', or null
    budget_range: str = Field(None, example="high") # 'low', 'mid', 'high', 'ultra', or null
    lead_type: str = Field("consultation", example="consultation") # 'consultation' or 'lead_magnet'

class LeadStatusUpdateSchema(BaseModel):
    status: str
    notes: str = None

@app.post("/api/leads")
async def register_lead(lead: LeadCreateSchema):
    """
    Registers a new lead, runs the elite CRO scoring model,
    saves to SQLite, triggers notifications, and returns routing details.
    """
    try:
        lead_dict = lead.dict()
        
        # 1. Score the lead
        score, is_vip = score_lead(lead_dict)
        
        # 2. Generate custom WhatsApp tracking link
        whatsapp_url = generate_whatsapp_url(lead_dict)
        
        # 3. Save to Lead Repository
        lead_id = save_lead(lead_dict, score, is_vip, whatsapp_url)
        
        # 4. VIP Hot Lead - Priority Trigger Workflow
        if is_vip:
            trigger_vip_notifications(lead_id, lead_dict, score)
            
        return {
            "success": True,
            "lead_id": lead_id,
            "score": score,
            "is_vip": is_vip,
            "whatsapp_url": whatsapp_url,
            "message": "Lead captured successfully!"
        }
        
    except Exception as e:
        logger.error(f"Error registering lead: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal lead processing failure: {str(e)}")

@app.get("/api/leads")
async def fetch_leads():
    """
    Admin endpoint to view ranked and classified leads.
    """
    try:
        return get_all_leads()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/leads/{lead_id}")
async def update_lead(lead_id: int, payload: LeadStatusUpdateSchema):
    """
    Admin endpoint to update lead pipeline stage and notes.
    """
    updated = update_lead_status(lead_id, payload.status, payload.notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return {"success": True, "message": "Lead updated successfully."}

@app.get("/api/analytics")
async def fetch_analytics():
    """
    Admin endpoint to fetch lead metrics and summary metrics.
    """
    try:
        return get_analytics_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-guide")
async def download_guide():
    """
    Serves the Contractor Apartment mistakes PDF Guide directly.
    """
    if not os.path.exists(GUIDE_PATH):
        raise HTTPException(status_code=404, detail="Guide PDF not found on server.")
    return FileResponse(GUIDE_PATH, media_type="application/pdf", filename="contractor_apartment_guide.pdf")

def trigger_vip_notifications(lead_id: int, lead_data: Dict[str, Any], score: int):
    """
    Priority notification handler. Triggers SMS, Email, and webhook alerts
    for top-tier prospects (e.g. Early Contractor Changes with high budgets).
    """
    logger.critical(
        f"\n🔥 [VIP HOT LEAD ALERT] 🔥\n"
        f"A top-tier client is ready to start! (Lead ID: {lead_id}, Score: {score}/100)\n"
        f"👤 Name: {lead_data['name']}\n"
        f"📞 Phone: {lead_data['phone']}\n"
        f"📧 Email: {lead_data['email']}\n"
        f"📍 Location: {lead_data.get('location', 'N/A')}\n"
        f"🏗️ Project: {lead_data.get('property_type', 'N/A')} | Stage: {lead_data.get('project_stage', 'N/A')}\n"
        f"💰 Budget: {str(lead_data.get('budget_range', 'N/A')).upper()}\n"
        f"Action Recommended: Reach out within 15 minutes! Send WhatsApp template.\n"
    )

# High-converting local interactive form and dashboard SPA
@app.get("/", response_class=HTMLResponse)
async def serve_demo_form():
    return """
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>עומר פז ניר - אדריכלות ועיצוב פנים</title>
        <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #1C1C1C;
                --primary-light: #2A2A2A;
                --accent: #C5A880; /* Elegant gold tone matches OPN brand */
                --accent-dark: #A58B65;
                --text-dark: #2C2C2C;
                --text-muted: #666666;
                --text-light: #FBFBFB;
                --bg-light: #F6F5F2; /* Luxury light warm linen */
                --bg-card: rgba(255, 255, 255, 0.85);
                --shadow-luxury: 0 20px 50px rgba(0, 0, 0, 0.05);
                --shadow-glass: 0 8px 32px 0 rgba(197, 168, 128, 0.08);
                --transition-premium: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                background-color: var(--bg-light);
                color: var(--text-dark);
                font-family: 'Assistant', sans-serif;
                min-height: 100vh;
                overflow-x: hidden;
                display: flex;
                flex-direction: column;
                transition: background-color 0.4s ease;
            }
            
            /* Luxury Navbar */
            header {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(197, 168, 128, 0.15);
                padding: 20px 40px;
                position: sticky;
                top: 0;
                z-index: 100;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                gap: 15px;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.01);
            }
            
            .brand-logo {
                font-family: 'Assistant', sans-serif;
                font-size: 24px;
                letter-spacing: 1px;
                font-weight: 600;
                color: var(--primary);
                cursor: pointer;
                white-space: nowrap;
                text-align: center;
            }
            
            .brand-logo span {
                font-weight: 600;
                color: var(--accent);
            }
            
            .nav-tabs {
                display: flex;
                gap: 24px;
            }
            
            .nav-tab {
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: var(--text-muted);
                cursor: pointer;
                padding: 8px 16px;
                border-radius: 30px;
                transition: var(--transition-premium);
                border: 1px solid transparent;
            }
            
            .nav-tab:hover {
                color: var(--primary);
                background: rgba(197, 168, 128, 0.05);
            }
            
            .nav-tab.active {
                color: var(--primary);
                background: white;
                border-color: rgba(197, 168, 128, 0.3);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
            }
            
            /* Main Content Container */
            .main-content {
                flex: 1;
                max-width: 1200px;
                width: 100%;
                margin: 40px auto;
                padding: 0 24px;
            }
            
            /* Client SPA Section */
            .client-section {
                display: block;
            }
            
            .hero-section {
                text-align: center;
                margin-bottom: 40px;
                animation: fadeIn 0.8s ease;
            }
            
            .hero-title {
                font-size: 38px;
                font-weight: 300;
                letter-spacing: -0.5px;
                color: var(--primary);
                margin-bottom: 12px;
            }
            
            .hero-title span {
                font-weight: 700;
                color: var(--accent);
            }
            
            .hero-subtitle {
                font-size: 16px;
                font-weight: 300;
                color: var(--text-muted);
                max-width: 600px;
                margin: 0 auto;
                line-height: 1.6;
            }
            
            /* Elegant Form Card */
            .glass-card {
                background: var(--bg-card);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.6);
                border-radius: 16px;
                box-shadow: var(--shadow-luxury), var(--shadow-glass);
                max-width: 600px;
                width: 100%;
                margin: 0 auto 50px auto;
                padding: 45px;
                position: relative;
                transition: var(--transition-premium);
            }
            
            .glass-card::before {
                content: '';
                position: absolute;
                top: 0; right: 0; bottom: 0; left: 0;
                border-radius: 16px;
                border: 1px solid rgba(197, 168, 128, 0.15);
                pointer-events: none;
            }
            
            /* Form Steps */
            .form-step {
                display: none;
            }
            
            .form-step.active {
                display: block;
                animation: slideInUp 0.5s cubic-bezier(0.165, 0.84, 0.44, 1);
            }
            
            /* Form Fields styling */
            .step-title {
                font-size: 20px;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 24px;
                text-align: right;
            }
            
            .input-group {
                margin-bottom: 24px;
                text-align: right;
            }
            
            label {
                display: block;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 10px;
                color: var(--primary);
                letter-spacing: 0.5px;
            }
            
            input[type="text"], input[type="email"], select {
                width: 100%;
                padding: 14px 18px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                font-size: 16px;
                background: white;
                outline: none;
                transition: var(--transition-premium);
                color: var(--text-dark);
            }
            
            input[type="text"]:focus, input[type="email"]:focus, select:focus {
                border-color: var(--accent);
                box-shadow: 0 0 0 4px rgba(197, 168, 128, 0.1);
            }
            
            /* Options Selector Grid */
            .options-grid {
                display: grid;
                grid-template-columns: repeat(1, 1fr);
                gap: 12px;
                margin-bottom: 24px;
            }
            
            @media (min-width: 480px) {
                .options-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            .option-card {
                border: 1px solid rgba(0, 0, 0, 0.08);
                background: white;
                padding: 18px;
                border-radius: 10px;
                cursor: pointer;
                transition: var(--transition-premium);
                text-align: center;
                font-weight: 600;
                font-size: 15px;
                position: relative;
            }
            
            .option-card:hover {
                border-color: var(--accent);
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(197, 168, 128, 0.05);
            }
            
            .option-card.selected {
                border-color: var(--accent);
                background: var(--accent);
                color: white;
                transform: translateY(0);
                box-shadow: 0 4px 12px rgba(197, 168, 128, 0.2);
            }
            
            /* Buttons */
            .btn {
                background: var(--primary);
                color: white;
                border: none;
                padding: 14px 28px;
                font-size: 16px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                width: 100%;
                transition: var(--transition-premium);
                letter-spacing: 1px;
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 8px;
            }
            
            .btn:hover {
                background: var(--primary-light);
                transform: translateY(-1px);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            }
            
            .btn-outline {
                background: transparent;
                border: 1px solid var(--primary);
                color: var(--primary);
                margin-top: 10px;
            }
            
            .btn-outline:hover {
                background: rgba(0, 0, 0, 0.02);
            }
            
            /* Progress indicators */
            .progress-container {
                height: 3px;
                background: #EAEAE8;
                border-radius: 10px;
                margin-bottom: 35px;
                overflow: hidden;
            }
            
            .progress-bar {
                height: 100%;
                width: 33%;
                background: var(--accent);
                transition: width 0.4s ease;
            }
            
            /* Success Panel VIP styling */
            .success-card {
                display: none;
                text-align: center;
            }
            
            .success-badge {
                display: inline-block;
                background: #FAF5EE;
                border: 1px solid var(--accent);
                color: #8C6D3F;
                padding: 6px 16px;
                border-radius: 30px;
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 20px;
                letter-spacing: 1px;
                animation: pulse 2s infinite;
            }
            
            .success-title {
                font-size: 26px;
                color: var(--primary);
                margin-bottom: 15px;
                font-weight: 600;
            }
            
            .success-desc {
                font-size: 15px;
                line-height: 1.7;
                margin-bottom: 30px;
                color: var(--text-muted);
            }
            
            .whatsapp-btn {
                background: #25D366;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                text-decoration: none;
                padding: 16px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                transition: var(--transition-premium);
                box-shadow: 0 8px 25px rgba(37, 211, 102, 0.15);
            }
            
            .whatsapp-btn:hover {
                background: #20BA5A;
                transform: translateY(-2px);
                box-shadow: 0 12px 30px rgba(37, 211, 102, 0.25);
            }
            
            /* Sticky Lead Magnet floating button */
            .sticky-magnet-trigger {
                position: fixed;
                bottom: 24px;
                left: 24px;
                background: rgba(28, 28, 28, 0.95);
                color: var(--accent);
                border: 1px solid rgba(197, 168, 128, 0.3);
                padding: 14px 24px;
                border-radius: 50px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                z-index: 99;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
                backdrop-filter: blur(10px);
                transition: var(--transition-premium);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .sticky-magnet-trigger:hover {
                color: white;
                background: var(--accent);
                border-color: var(--accent);
                transform: translateY(-3px);
            }
            
            /* Lead Magnet Overlay Modal */
            .modal-overlay {
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(8px);
                z-index: 1000;
                display: none;
                justify-content: center;
                align-items: center;
                animation: fadeIn 0.3s ease;
            }
            
            .modal-card {
                background: white;
                border-radius: 16px;
                max-width: 500px;
                width: 100%;
                padding: 40px;
                box-shadow: 0 25px 60px rgba(0,0,0,0.15);
                position: relative;
                text-align: center;
                animation: scaleUp 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            }
            
            .modal-close {
                position: absolute;
                top: 20px;
                right: 20px;
                font-size: 24px;
                color: var(--text-muted);
                cursor: pointer;
                background: none;
                border: none;
                outline: none;
                transition: var(--transition-premium);
            }
            
            .modal-close:hover {
                color: var(--primary);
            }
            
            .modal-badge {
                display: inline-block;
                background: rgba(197, 168, 128, 0.1);
                color: var(--accent-dark);
                font-size: 11px;
                font-weight: 700;
                padding: 4px 12px;
                border-radius: 20px;
                margin-bottom: 12px;
                text-transform: uppercase;
            }
            
            .modal-title {
                font-size: 22px;
                font-weight: 600;
                margin-bottom: 10px;
            }
            
            .modal-desc {
                font-size: 14px;
                color: var(--text-muted);
                margin-bottom: 24px;
                line-height: 1.6;
            }
            
            /* Admin Section styles */
            .admin-section {
                display: none;
                animation: fadeIn 0.5s ease;
            }
            
            /* Analytics Grid */
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(1, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }
            
            @media (min-width: 768px) {
                .metrics-grid {
                    grid-template-columns: repeat(4, 1fr);
                }
            }
            
            .metric-card {
                background: white;
                border-radius: 12px;
                padding: 24px;
                box-shadow: var(--shadow-luxury);
                border: 1px solid rgba(197, 168, 128, 0.1);
                position: relative;
            }
            
            .metric-title {
                font-size: 13px;
                font-weight: 600;
                color: var(--text-muted);
                text-transform: uppercase;
                margin-bottom: 8px;
            }
            
            .metric-value {
                font-size: 28px;
                font-weight: 700;
                color: var(--primary);
                font-family: 'Outfit', sans-serif;
            }
            
            .metric-card.vip-highlight {
                border: 2px solid var(--accent);
                background: linear-gradient(135deg, #FFFDF9 0%, #FAF6EE 100%);
            }
            
            .metric-card.vip-highlight .metric-value {
                color: var(--accent-dark);
            }
            
            /* Analytics Charts */
            .charts-grid {
                display: grid;
                grid-template-columns: repeat(1, 1fr);
                gap: 20px;
                margin-bottom: 35px;
            }
            
            @media (min-width: 768px) {
                .charts-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            .chart-card {
                background: white;
                border-radius: 12px;
                padding: 24px;
                box-shadow: var(--shadow-luxury);
                border: 1px solid rgba(197, 168, 128, 0.1);
            }
            
            .chart-title {
                font-size: 15px;
                font-weight: 600;
                margin-bottom: 18px;
                color: var(--primary);
                text-align: right;
            }
            
            .chart-bar-container {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .chart-bar-row {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .chart-bar-label {
                width: 140px;
                font-size: 13px;
                text-align: right;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .chart-bar-bg {
                flex: 1;
                height: 12px;
                background: #EEE;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .chart-bar-fill {
                height: 100%;
                background: var(--accent);
                border-radius: 6px;
                width: 0%;
                transition: width 1s ease;
            }
            
            .chart-bar-fill.vip {
                background: var(--primary);
            }
            
            .chart-bar-val {
                width: 40px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Outfit', sans-serif;
            }
            
            /* CRM Table and Filter bar */
            .filter-bar {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: var(--shadow-luxury);
                margin-bottom: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                align-items: center;
                border: 1px solid rgba(197, 168, 128, 0.1);
            }
            
            .filter-input {
                flex: 1;
                min-width: 200px;
                padding: 10px 14px;
                font-size: 14px;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 6px;
                outline: none;
            }
            
            .filter-select {
                padding: 10px 14px;
                font-size: 14px;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 6px;
                background: white;
                outline: none;
                width: auto;
            }
            
            .crm-table-container {
                background: white;
                border-radius: 12px;
                box-shadow: var(--shadow-luxury);
                border: 1px solid rgba(197, 168, 128, 0.1);
                overflow-x: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: right;
            }
            
            th {
                background: #FAF8F5;
                color: var(--text-muted);
                padding: 16px 20px;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                border-bottom: 1px solid rgba(197, 168, 128, 0.1);
            }
            
            td {
                padding: 16px 20px;
                font-size: 14px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
                color: var(--text-dark);
            }
            
            tr:hover td {
                background: #FCFAF7;
            }
            
            tr.vip-row td {
                background: rgba(197, 168, 128, 0.03);
            }
            
            tr.vip-row:hover td {
                background: rgba(197, 168, 128, 0.06);
            }
            
            /* Badges & Status markers */
            .badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
            }
            
            .badge-vip {
                background: #FFF0D4;
                color: #B27C1E;
                border: 1px solid rgba(197, 168, 128, 0.3);
                box-shadow: 0 2px 8px rgba(197, 168, 128, 0.15);
            }
            
            .badge-magnet {
                background: #E8F5E9;
                color: #2E7D32;
            }
            
            .badge-consult {
                background: #E3F2FD;
                color: #1565C0;
            }
            
            .status-pill {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }
            
            .status-new { background: #ECEFF1; color: #455A64; }
            .status-contacted { background: #FFF9C4; color: #F57F17; }
            .status-scheduled { background: #E1BEE7; color: #7B1FA2; }
            .status-won { background: #C8E6C9; color: #2E7D32; }
            .status-lost { background: #FFCDD2; color: #C62828; }
            
            /* Quick action utility buttons */
            .action-btn {
                background: none;
                border: none;
                color: var(--accent-dark);
                cursor: pointer;
                font-weight: 600;
                font-size: 13px;
                padding: 4px 8px;
                border-radius: 4px;
                transition: var(--transition-premium);
            }
            
            .action-btn:hover {
                background: rgba(197, 168, 128, 0.15);
                color: var(--primary);
            }
            
            .action-btn.wa-link {
                color: #25D366;
            }
            
            .action-btn.wa-link:hover {
                background: rgba(37, 211, 102, 0.1);
                color: #20BA5A;
            }
            
            /* Edit Modal elements */
            .crm-modal-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 15px;
                text-align: right;
                margin-top: 15px;
            }
            
            .lead-detail-label {
                font-size: 12px;
                color: var(--text-muted);
                margin-bottom: 2px;
            }
            
            .lead-detail-val {
                font-size: 15px;
                font-weight: bold;
                color: var(--primary);
                margin-bottom: 12px;
            }
            
            /* Custom animations */
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideInUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes scaleUp {
                from { opacity: 0; transform: scale(0.95); }
                to { opacity: 1; transform: scale(1); }
            }
            
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(197, 168, 128, 0.4); }
                70% { box-shadow: 0 0 0 10px rgba(197, 168, 128, 0); }
                100% { box-shadow: 0 0 0 0 rgba(197, 168, 128, 0); }
            }
            
            footer {
                text-align: center;
                padding: 30px;
                font-size: 13px;
                color: var(--text-muted);
                border-top: 1px solid rgba(197, 168, 128, 0.1);
                background: white;
                margin-top: auto;
            }
            
            footer a {
                color: var(--accent-dark);
                text-decoration: none;
                font-weight: 600;
            }
        </style>
    </head>
    <body>
        
        <!-- HEADER -->
        <header>
            <div class="brand-logo" onclick="switchTab('client')">עומר פז ניר | תכנון ועיצוב פנים</div>
            <div class="nav-tabs">
                <div class="nav-tab active" id="tab-client" onclick="switchTab('client')">אפיון פרויקט</div>
                <div class="nav-tab" id="tab-admin" onclick="switchTab('admin')">מערכת CRM</div>
            </div>
        </header>

        <!-- MAIN SPA CONTENT -->
        <div class="main-content">
            
            <!-- CLIENT SECTION -->
            <div class="client-section" id="client-section">
                
                <div class="hero-section">
                    <h2 class="hero-title">תכננו את <span>קונספט הפרויקט</span> שלכם</h2>
                    <p class="hero-subtitle">התחילו את האפיון הראשוני של דירתכם או ביתכם. כלי האפיון החכם שלנו יסייע לכם להגדיר מטרות ויאפשר לנו לבחון התאמה לתכנון מוקדם.</p>
                </div>
                
                <div class="glass-card" id="form-card">
                    
                    <div class="progress-container" id="progress-container">
                        <div class="progress-bar" id="progress-bar"></div>
                    </div>
                    
                    <!-- STEP 1: Property Type & Location -->
                    <div class="form-step active" id="step-1">
                        <h3 class="step-title">1. סוג הפרויקט ומיקום</h3>
                        <label>באיזה נכס מדובר?</label>
                        <div class="options-grid">
                            <div class="option-card" onclick="selectProperty(this, 'contractor_apartment')">דירת קבלן (שינויי דיירים) 🏗️</div>
                            <div class="option-card" onclick="selectProperty(this, 'renovation')">שיפוץ דירה יסודי 🛠️</div>
                            <div class="option-card" onclick="selectProperty(this, 'private_house')">בית פרטי / דו-משפחתי 🏡</div>
                        </div>
                        <div class="input-group">
                            <label for="location">מיקום הפרויקט (עיר/יישוב)</label>
                            <input type="text" id="location" placeholder="למשל: תל אביב, הרצליה פיתוח, רעננה...">
                        </div>
                        <button class="btn" onclick="nextStep(2)">המשך לאפיון תקציב ולוח זמנים</button>
                    </div>
                    
                    <!-- STEP 2: Project Stage & Budget -->
                    <div class="form-step" id="step-2">
                        <h3 class="step-title">2. שלב הפרויקט ומסגרת תקציב</h3>
                        <label>מהו שלב הפרויקט הנוכחי?</label>
                        <div class="options-grid">
                            <div class="option-card" onclick="selectStage(this, 'pre_construction')">לפני בנייה (שלב תכנוני מוקדם) ⏱️</div>
                            <div class="option-card" onclick="selectStage(this, 'under_construction')">במהלך בנייה פעילה 🧱</div>
                            <div class="option-card" onclick="selectStage(this, 'ready_to_move')">לקראת מסירה / מפתח ביד 🔑</div>
                        </div>
                        <label style="margin-top: 15px;">תקציב מוערך לעיצוב ושיפוץ</label>
                        <div class="options-grid">
                            <div class="option-card" onclick="selectBudget(this, 'low')">עד 100,000 ₪</div>
                            <div class="option-card" onclick="selectBudget(this, 'mid')">100k - 300k ₪</div>
                            <div class="option-card" onclick="selectBudget(this, 'high')">300k - 600k ₪</div>
                            <div class="option-card" onclick="selectBudget(this, 'ultra')">מעל 600,000 ₪ 💎</div>
                        </div>
                        <button class="btn" onclick="nextStep(3)">המשך להזנת פרטי קשר</button>
                        <button class="btn btn-outline" onclick="prevStep(1)">חזרה לשלב הקודם</button>
                    </div>
                    
                    <!-- STEP 3: Contact Info -->
                    <div class="form-step" id="step-3">
                        <h3 class="step-title">3. פרטים ליצירת קשר</h3>
                        <div class="input-group">
                            <label for="fullname">שם מלא</label>
                            <input type="text" id="fullname" placeholder="שם ושם משפחה">
                        </div>
                        <div class="input-group">
                            <label for="email">אימייל</label>
                            <input type="email" id="email" placeholder="name@domain.com" style="direction: ltr; text-align: right;">
                        </div>
                        <div class="input-group">
                            <label for="phone">טלפון נייד (מומלץ WhatsApp)</label>
                            <input type="text" id="phone" placeholder="054XXXXXXX">
                        </div>
                        <button class="btn" onclick="submitLead()">שלח ואפיין קונספט פרויקט</button>
                        <button class="btn btn-outline" onclick="prevStep(2)">חזרה לשלב הקודם</button>
                    </div>
                    
                    <!-- SUCCESS CARD -->
                    <div class="success-card" id="success-card">
                        <div class="success-badge" id="vip-badge">פנייה בעדיפות גבוהה ✨ VIP</div>
                        <h3 class="success-title" id="success-title">הקונספט אופיין בהצלחה!</h3>
                        <p class="success-desc" id="success-desc">
                            פרטי האפיון הראשוניים נשמרו בהצלחה במערכת. על מנת שנוכל לקדם את הפגישה ולהעניק לך מענה מהיר, מומלץ לשלוח את סיכום האפיון ישירות לעומר בווטסאפ:
                        </p>
                        <a href="#" id="whatsapp-link" class="whatsapp-btn" target="_blank">
                            <svg style="width: 24px; height: 24px; fill: white;" viewBox="0 0 24 24"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946C.06 5.348 5.397 0 11.977 0c3.187.001 6.185 1.24 8.435 3.493 2.25 2.253 3.488 5.251 3.487 8.44-.003 6.625-5.34 11.97-11.92 11.97-1.995-.001-3.956-.502-5.706-1.458L0 24zm6.59-11.585c.166.277.276.578.433.882.222.428.1.802-.05.11-.148-.693-.979-1.705-1.344-2.193-.364-.488-.737-.396-.997-.41-.21-.011-.45-.013-.69-.013-.24 0-.63.09-.96.45-.33.36-1.26 1.23-1.26 3.01s1.3 3.48 1.48 3.72c.18.24 2.55 3.93 6.19 5.51.86.38 1.54.6 2.06.77.87.28 1.66.24 2.28.15.7-.1 2.14-.88 2.44-1.73.3-.85.3-1.58.21-1.73-.09-.15-.33-.24-.7-.43-.36-.18-2.14-1.06-2.47-1.18-.33-.12-.57-.18-.81.18-.24.36-.93 1.18-1.14 1.42-.21.24-.42.27-.78.09-.36-.18-1.53-.56-2.91-1.79-1.07-.96-1.8-2.15-2.01-2.51-.21-.36-.02-.56.16-.74.16-.16.36-.42.54-.63.18-.21.24-.36.36-.6.12-.24.06-.45-.03-.63z"/></svg>
                            שליחת סיכום האפיון לעומר ב-WhatsApp
                        </a>
                    </div>
                </div>
            </div>
            
            <!-- ADMIN SECTION -->
            <div class="admin-section" id="admin-section">
                <div class="hero-section">
                    <h2 class="hero-title">לוח בקרה <span>CRM & CRO Analytics</span></h2>
                    <p class="hero-subtitle">ניהול, דירוג ומעקב אחר פניות ממוקדות תקציב ותכנון מוקדם.</p>
                </div>
                
                <!-- Metrics -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">סה"כ פניות</div>
                        <div class="metric-value" id="metric-total">0</div>
                    </div>
                    <div class="metric-card vip-highlight">
                        <div class="metric-title">🔥 פניות VIP חמות</div>
                        <div class="metric-value" id="metric-vip">0</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">דירוג איכות ממוצע</div>
                        <div class="metric-value" id="metric-score">0.0</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">הורדות מדריכים</div>
                        <div class="metric-value" id="metric-magnet">0</div>
                    </div>
                </div>
                
                <!-- Charts Grid -->
                <div class="charts-grid">
                    <div class="chart-card">
                        <div class="chart-title">פילוח לפי תקציבי לקוח (פגישות)</div>
                        <div class="chart-bar-container" id="chart-budgets">
                            <!-- Populated by JS -->
                        </div>
                    </div>
                    <div class="chart-card">
                        <div class="chart-title">פילוח לפי שלבי פרויקט</div>
                        <div class="chart-bar-container" id="chart-stages">
                            <!-- Populated by JS -->
                        </div>
                    </div>
                </div>
                
                <!-- Filter Bar -->
                <div class="filter-bar">
                    <input type="text" class="filter-input" id="search-filter" placeholder="חיפוש לפי שם, מיקום או טלפון..." oninput="applyTableFilters()">
                    <select class="filter-select" id="type-filter" onchange="applyTableFilters()">
                        <option value="">כל סוגי הפניות</option>
                        <option value="consultation">אפיון קונספט (פגישות)</option>
                        <option value="lead_magnet">הורדת מדריך קבלן</option>
                    </select>
                    <select class="filter-select" id="vip-filter" onchange="applyTableFilters()">
                        <option value="">כל הדירוגים</option>
                        <option value="1">רק לקוחות VIP 🔥</option>
                        <option value="0">ללא VIP</option>
                    </select>
                    <select class="filter-select" id="status-filter" onchange="applyTableFilters()">
                        <option value="">כל הסטטוסים</option>
                        <option value="new">פנייה חדשה (New)</option>
                        <option value="contacted">נוצר קשר (Contacted)</option>
                        <option value="scheduled">נקבעה פגישה (Scheduled)</option>
                        <option value="won">פרויקט נסגר (Won)</option>
                        <option value="lost">לא רלוונטי (Lost)</option>
                    </select>
                </div>
                
                <!-- Leads Table -->
                <div class="crm-table-container">
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 50px;">ID</th>
                                <th>לקוח</th>
                                <th>סוג פנייה</th>
                                <th>נכס ומיקום</th>
                                <th>שלב</th>
                                <th>תקציב</th>
                                <th>איכות</th>
                                <th>סטטוס</th>
                                <th>תאריך</th>
                                <th style="text-align: center;">פעולות</th>
                            </tr>
                        </thead>
                        <tbody id="leads-table-body">
                            <!-- Populated dynamically -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- STICKY LEAD MAGNET TRIGGER -->
        <button class="sticky-magnet-trigger" onclick="openMagnetModal()">
            <svg style="width: 18px; height: 18px; fill: currentColor;" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 16h-2v-2h2v2zm0-4h-2V7h2v7z"/></svg>
            הורדת מדריך שינויי קבלן חינם 📄
        </button>

        <!-- LEAD MAGNET MODAL -->
        <div class="modal-overlay" id="magnet-modal">
            <div class="modal-card">
                <button class="modal-close" onclick="closeMagnetModal()">×</button>
                <div class="modal-badge">מתנה לרוכשי דירות קבלן</div>
                <h3 class="modal-title">מדריך קבלן: 5 טעויות תכנון שיעלו לכם עשרות אלפי שקלים</h3>
                <p class="modal-desc">
                    רכשתם דירה מקבלן? אל תעשו את הטעויות היקרות של שינויי דיירים ללא תכנון מוקדם. הזינו את פרטיכם וקבלו את המדריך המלא ישירות למחשב או לנייד!
                </p>
                <div class="input-group">
                    <label for="magnet-name">שם מלא</label>
                    <input type="text" id="magnet-name" placeholder="שם מלא שלכם">
                </div>
                <div class="input-group">
                    <label for="magnet-email">אימייל לקבלת המדריך</label>
                    <input type="email" id="magnet-email" placeholder="name@domain.com" style="direction: ltr; text-align: right;">
                </div>
                <div class="input-group">
                    <label for="magnet-phone">טלפון לקבלת עדכונים בווטסאפ</label>
                    <input type="text" id="magnet-phone" placeholder="05XXXXXXXX">
                </div>
                <button class="btn" onclick="submitMagnetLead()">הורדת המדריך עכשיו 📥</button>
            </div>
        </div>

        <!-- LEAD EDIT CRM MODAL -->
        <div class="modal-overlay" id="edit-modal">
            <div class="modal-card" style="text-align: right; max-width: 550px;">
                <button class="modal-close" onclick="closeEditModal()">×</button>
                <div class="modal-badge" id="edit-modal-lead-type">פרטי פנייה</div>
                <h3 class="modal-title" style="margin-bottom: 20px;" id="edit-modal-name">עריכת פניית לקוח</h3>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <div class="lead-detail-label">טלפון</div>
                        <div class="lead-detail-val" id="detail-phone">-</div>
                    </div>
                    <div>
                        <div class="lead-detail-label">אימייל</div>
                        <div class="lead-detail-val" id="detail-email">-</div>
                    </div>
                    <div>
                        <div class="lead-detail-label">מיקום</div>
                        <div class="lead-detail-val" id="detail-location">-</div>
                    </div>
                    <div>
                        <div class="lead-detail-label">סוג נכס</div>
                        <div class="lead-detail-val" id="detail-property">-</div>
                    </div>
                    <div>
                        <div class="lead-detail-label">שלב בפרויקט</div>
                        <div class="lead-detail-val" id="detail-stage">-</div>
                    </div>
                    <div>
                        <div class="lead-detail-label">תקציב משוער</div>
                        <div class="lead-detail-val" id="detail-budget">-</div>
                    </div>
                </div>

                <hr style="border: 0; border-top: 1px solid #EEE; margin: 15px 0;">

                <div class="input-group">
                    <label for="edit-status">סטטוס פנייה במערכת</label>
                    <select id="edit-status">
                        <option value="new">פנייה חדשה (New)</option>
                        <option value="contacted">נוצר קשר ראשוני (Contacted)</option>
                        <option value="scheduled">נקבעה פגישת אפיון (Scheduled)</option>
                        <option value="won">לקוח סגור - פרויקט החל (Won)</option>
                        <option value="lost">לא רלוונטי / אבוד (Lost)</option>
                    </select>
                </div>

                <div class="input-group">
                    <label for="edit-notes">הערות ליווי ומעקב (Admin Notes)</label>
                    <textarea id="edit-notes" rows="4" style="width: 100%; border: 1px solid rgba(0,0,0,0.1); border-radius: 8px; padding: 12px; font-family: inherit; font-size: 15px; outline: none;" placeholder="כתוב הערות מעקב, תקציר פגישה, או סיבות לאי-רלוונטיות..."></textarea>
                </div>

                <input type="hidden" id="edit-lead-id">
                <button class="btn" onclick="saveLeadStatus()">שמירת עדכונים ומעקב</button>
            </div>
        </div>

        <!-- FOOTER -->
        <footer>
            כל הזכויות שמורות © 2026 עומר פז ניר - סטודיו לתכנון ועיצוב פנים למגורי יוקרה. מופעל על ידי Antigravity lead CRM.
        </footer>

        <!-- INTERACTION JAVASCRIPT -->
        <script>
            let leadData = {
                property_type: '',
                location: '',
                project_stage: '',
                budget_range: '',
                name: '',
                email: '',
                phone: '',
                lead_type: 'consultation'
            };
            
            let allLeads = []; // Cached array for filtering
            let currentEditLead = null;

            // Form selection utilities
            function selectProperty(element, type) {
                document.querySelectorAll('#step-1 .option-card').forEach(el => el.classList.remove('selected'));
                element.classList.add('selected');
                leadData.property_type = type;
            }

            function selectStage(element, stage) {
                document.querySelectorAll('#step-2 .option-card:nth-of-type(-n+3)').forEach(el => el.classList.remove('selected'));
                element.classList.add('selected');
                leadData.project_stage = stage;
            }

            function selectBudget(element, budget) {
                document.querySelectorAll('#step-2 .option-card:nth-of-type(n+4)').forEach(el => el.classList.remove('selected'));
                element.classList.add('selected');
                leadData.budget_range = budget;
            }

            function nextStep(step) {
                if (step === 2) {
                    leadData.location = document.getElementById('location').value;
                    if (!leadData.property_type) {
                        alert('אנא בחרו את סוג הנכס');
                        return;
                    }
                    if (!leadData.location.trim()) {
                        alert('אנא הזינו את מיקום הנכס');
                        return;
                    }
                    document.getElementById('step-1').classList.remove('active');
                    document.getElementById('step-2').classList.add('active');
                    document.getElementById('progress-bar').style.width = '66%';
                } else if (step === 3) {
                    if (!leadData.project_stage) {
                        alert('אנא בחרו את שלב הפרויקט');
                        return;
                    }
                    if (!leadData.budget_range) {
                        alert('אנא בחרו מסגרת תקציב משוערת');
                        return;
                    }
                    document.getElementById('step-2').classList.remove('active');
                    document.getElementById('step-3').classList.add('active');
                    document.getElementById('progress-bar').style.width = '100%';
                }
            }

            function prevStep(step) {
                if (step === 1) {
                    document.getElementById('step-2').classList.remove('active');
                    document.getElementById('step-1').classList.add('active');
                    document.getElementById('progress-bar').style.width = '33%';
                } else if (step === 2) {
                    document.getElementById('step-3').classList.remove('active');
                    document.getElementById('step-2').classList.add('active');
                    document.getElementById('progress-bar').style.width = '66%';
                }
            }

            // SPA Tabs navigation
            function switchTab(tab) {
                document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
                
                if (tab === 'client') {
                    document.getElementById('tab-client').classList.add('active');
                    document.getElementById('client-section').style.display = 'block';
                    document.getElementById('admin-section').style.display = 'none';
                    document.body.style.backgroundColor = 'var(--bg-light)';
                } else if (tab === 'admin') {
                    document.getElementById('tab-admin').classList.add('active');
                    document.getElementById('client-section').style.display = 'none';
                    document.getElementById('admin-section').style.display = 'block';
                    document.body.style.backgroundColor = '#FAF9F6';
                    
                    // Fetch real-time DB data
                    fetchCRMAnalytics();
                    fetchCRMLeads();
                }
            }

            // Client Consultation Lead Submission
            async function submitLead() {
                leadData.name = document.getElementById('fullname').value;
                leadData.email = document.getElementById('email').value;
                leadData.phone = document.getElementById('phone').value;
                leadData.lead_type = 'consultation';

                if (!leadData.name.trim() || !leadData.email.trim() || !leadData.phone.trim()) {
                    alert('אנא מלאו את כל פרטי הקשר כדי לקבל אפיון');
                    return;
                }

                try {
                    const response = await fetch('/api/leads', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(leadData)
                    });

                    const result = await response.json();
                    if (result.success) {
                        document.getElementById('step-3').classList.remove('active');
                        document.getElementById('progress-container').style.display = 'none';
                        
                        const successCard = document.getElementById('success-card');
                        successCard.style.display = 'block';
                        
                        const waLink = document.getElementById('whatsapp-link');
                        waLink.href = result.whatsapp_url;
                        
                        const vipBadge = document.getElementById('vip-badge');
                        const successTitle = document.getElementById('success-title');
                        const successDesc = document.getElementById('success-desc');
                        
                        if (result.is_vip) {
                            vipBadge.style.display = 'inline-block';
                            vipBadge.innerText = 'פנייה בעדיפות עליונה ✨ VIP חם';
                            successTitle.innerText = 'מדהים! פנייתך סומנה בעדיפות עליונה.';
                            successDesc.innerText = 'הפרטים שלך מלמדים על פרויקט בעל פוטנציאל גבוה בשלב קריטי. מומלץ לתאם פגישה ללא דיחוי. לחצו למטה כדי להעביר את סיכום האפיון ישירות לווטסאפ האישי של עומר:';
                        } else {
                            vipBadge.style.display = 'none';
                            successTitle.innerText = 'האפיון נשמר בהצלחה!';
                            successDesc.innerText = 'תודה רבה על יצירת הקשר. פרטי האפיון נשמרו. לקבלת מענה מהיר במיוחד ותיאום שיחה קצרה, נשמח אם תשלחו לעומר את המפרט בווטסאפ:';
                        }
                    } else {
                        alert('חלה שגיאה בעיבוד האפיון. אנא נסו שנית.');
                    }
                } catch (error) {
                    console.error('Submission error:', error);
                    alert('שגיאת תקשורת עם שרת האפיון.');
                }
            }

            // Lead Magnet Modal Actions
            function openMagnetModal() {
                document.getElementById('magnet-modal').style.display = 'flex';
            }

            function closeMagnetModal() {
                document.getElementById('magnet-modal').style.display = 'none';
            }

            async function submitMagnetLead() {
                const name = document.getElementById('magnet-name').value;
                const email = document.getElementById('magnet-email').value;
                const phone = document.getElementById('magnet-phone').value;

                if (!name.trim() || !email.trim() || !phone.trim()) {
                    alert('אנא מלאו את כל השדות להורדת המדריך');
                    return;
                }

                const payload = {
                    name: name,
                    email: email,
                    phone: phone,
                    lead_type: 'lead_magnet'
                };

                try {
                    const response = await fetch('/api/leads', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    const result = await response.json();
                    if (result.success) {
                        closeMagnetModal();
                        
                        // Open mock PDF guide download in a new tab
                        window.open('/api/download-guide', '_blank');
                        
                        // Custom VIP pop-up prompt for guide downloads
                        alert('המדריך ירד בהצלחה! שלחנו לך גם עותק למייל. בעמוד הבא תוכל/י לתאם שיחת אפיון קצרה עם עומר במידה ותרצה/י.');
                    } else {
                        alert('שגיאה ברישום להורדת המדריך.');
                    }
                } catch (error) {
                    console.error('Magnet error:', error);
                    alert('שגיאת חיבור לשרת.');
                }
            }

            // CRM Dashboard API Fetchers
            async function fetchCRMAnalytics() {
                try {
                    const response = await fetch('/api/analytics');
                    const data = await response.json();
                    
                    document.getElementById('metric-total').innerText = data.total_leads;
                    document.getElementById('metric-vip').innerText = data.vip_leads;
                    document.getElementById('metric-score').innerText = data.avg_score;
                    document.getElementById('metric-magnet').innerText = data.magnet_leads;
                    
                    // Render Budget Chart
                    const budgetsContainer = document.getElementById('chart-budgets');
                    budgetsContainer.innerHTML = '';
                    
                    const budgetLabels = {
                        'low': 'עד 100k ₪',
                        'mid': '100k - 300k ₪',
                        'high': '300k - 600k ₪',
                        'ultra': 'מעל 600k ₪ 💎'
                    };
                    
                    let maxBudgetVal = 1;
                    Object.values(data.budgets).forEach(v => { if(v > maxBudgetVal) maxBudgetVal = v; });
                    
                    Object.entries(budgetLabels).forEach(([k, label]) => {
                        const val = data.budgets[k] || 0;
                        const pct = (val / maxBudgetVal) * 100;
                        
                        budgetsContainer.innerHTML += `
                            <div class="chart-bar-row">
                                <span class="chart-bar-label">${label}</span>
                                <div class="chart-bar-bg">
                                    <div class="chart-bar-fill" style="width: ${pct}%"></div>
                                </div>
                                <span class="chart-bar-val">${val}</span>
                            </div>
                        `;
                    });

                    // Render Stage Chart
                    const stagesContainer = document.getElementById('chart-stages');
                    stagesContainer.innerHTML = '';
                    
                    const stageLabels = {
                        'pre_construction': 'לפני בנייה (שינויים)',
                        'under_construction': 'במהלך בנייה',
                        'ready_to_move': 'לקראת מסירה'
                    };
                    
                    let maxStageVal = 1;
                    Object.values(data.stages).forEach(v => { if(v > maxStageVal) maxStageVal = v; });
                    
                    Object.entries(stageLabels).forEach(([k, label]) => {
                        const val = data.stages[k] || 0;
                        const pct = (val / maxStageVal) * 100;
                        
                        stagesContainer.innerHTML += `
                            <div class="chart-bar-row">
                                <span class="chart-bar-label">${label}</span>
                                <div class="chart-bar-bg">
                                    <div class="chart-bar-fill vip" style="width: ${pct}%"></div>
                                </div>
                                <span class="chart-bar-val">${val}</span>
                            </div>
                        `;
                    });
                    
                } catch (e) {
                    console.error("Error fetching analytics:", e);
                }
            }

            async function fetchCRMLeads() {
                try {
                    const response = await fetch('/api/leads');
                    allLeads = await response.json();
                    renderLeadsTable(allLeads);
                } catch (e) {
                    console.error("Error fetching leads:", e);
                }
            }

            function renderLeadsTable(leads) {
                const tbody = document.getElementById('leads-table-body');
                tbody.innerHTML = '';
                
                if (leads.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 30px;">לא נמצאו פניות במערכת.</td></tr>';
                    return;
                }
                
                const propMap = {
                    'private_house': 'בית פרטי 🏡',
                    'contractor_apartment': 'דירת קבלן 🏗️',
                    'renovation': 'שיפוץ יסודי 🛠️',
                    null: '-', '': '-'
                };
                
                const stageMap = {
                    'pre_construction': 'לפני בנייה',
                    'under_construction': 'בבנייה',
                    'ready_to_move': 'לקראת מסירה',
                    null: '-', '': '-'
                };
                
                const budgetMap = {
                    'low': 'עד 100k ₪',
                    'mid': '100k - 300k',
                    'high': '300k - 600k',
                    'ultra': 'מעל 600k 💎',
                    null: '-', '': '-'
                };
                
                leads.forEach(lead => {
                    const dateStr = new Date(lead.created_at + 'Z').toLocaleDateString('he-IL', {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    });
                    
                    const leadTypeBadge = lead.lead_type === 'lead_magnet' 
                        ? '<span class="badge badge-magnet">מדריך קבלן</span>' 
                        : '<span class="badge badge-consult">פגישת אפיון</span>';
                        
                    const vipBadge = lead.is_vip 
                        ? '<span class="badge badge-vip">🔥 VIP חם</span>' 
                        : `<span style="font-family: Outfit; font-weight: bold; color: ${lead.score >= 50 ? '#C5A880' : '#888'}">${lead.score}/100</span>`;
                    
                    const rowClass = lead.is_vip ? 'class="vip-row"' : '';
                    
                    tbody.innerHTML += `
                        <tr ${rowClass}>
                            <td>${lead.id}</td>
                            <td>
                                <div style="font-weight: bold;">${lead.name}</div>
                                <div style="font-size: 11px; color: var(--text-muted); font-family: Outfit;">${lead.phone}</div>
                            </td>
                            <td>${leadTypeBadge}</td>
                            <td>
                                <div>${propMap[lead.property_type] || lead.property_type || '-'}</div>
                                <div style="font-size: 12px; color: var(--text-muted);">${lead.location || '-'}</div>
                            </td>
                            <td>${stageMap[lead.project_stage] || lead.project_stage || '-'}</td>
                            <td>${budgetMap[lead.budget_range] || lead.budget_range || '-'}</td>
                            <td>${vipBadge}</td>
                            <td><span class="status-pill status-${lead.status}">${lead.status}</span></td>
                            <td style="font-size: 12px; color: var(--text-muted); font-family: Outfit;">${dateStr}</td>
                            <td style="text-align: center; white-space: nowrap;">
                                <button class="action-btn" onclick="openEditModal(${lead.id})">צפייה ועריכה</button>
                                <a href="${lead.whatsapp_url}" class="action-btn wa-link" target="_blank" title="שלח הודעה">WhatsApp</a>
                            </td>
                        </tr>
                    `;
                });
            }

            function applyTableFilters() {
                const searchVal = document.getElementById('search-filter').value.toLowerCase();
                const typeVal = document.getElementById('type-filter').value;
                const vipVal = document.getElementById('vip-filter').value;
                const statusVal = document.getElementById('status-filter').value;
                
                const filtered = allLeads.filter(lead => {
                    const matchesSearch = lead.name.toLowerCase().includes(searchVal) || 
                                          (lead.location && lead.location.toLowerCase().includes(searchVal)) || 
                                          lead.phone.includes(searchVal);
                    const matchesType = !typeVal || lead.lead_type === typeVal;
                    const matchesVip = !vipVal || lead.is_vip == parseInt(vipVal);
                    const matchesStatus = !statusVal || lead.status === statusVal;
                    
                    return matchesSearch && matchesType && matchesVip && matchesStatus;
                });
                
                renderLeadsTable(filtered);
            }

            // Edit Modal Functions
            function openEditModal(leadId) {
                currentEditLead = allLeads.find(l => l.id === leadId);
                if (!currentEditLead) return;
                
                document.getElementById('edit-lead-id').value = currentEditLead.id;
                document.getElementById('edit-modal-name').innerText = `מעקב פנייה: ${currentEditLead.name}`;
                document.getElementById('edit-modal-lead-type').innerText = currentEditLead.lead_type === 'lead_magnet' ? 'הורדת מדריך' : 'אפיון קונספט';
                
                document.getElementById('detail-phone').innerText = currentEditLead.phone;
                document.getElementById('detail-email').innerText = currentEditLead.email;
                document.getElementById('detail-location').innerText = currentEditLead.location || 'לא צוין';
                
                const propMap = { 'private_house': 'בית פרטי 🏡', 'contractor_apartment': 'דירת קבלן 🏗️', 'renovation': 'שיפוץ יסודי 🛠️' };
                const stageMap = { 'pre_construction': 'לפני בנייה', 'under_construction': 'בבנייה', 'ready_to_move': 'לקראת מסירה' };
                const budgetMap = { 'low': 'עד 100,000 ₪', 'mid': '100k - 300k', 'high': '300k - 600k', 'ultra': 'מעל 600k 💎' };
                
                document.getElementById('detail-property').innerText = propMap[currentEditLead.property_type] || currentEditLead.property_type || 'N/A';
                document.getElementById('detail-stage').innerText = stageMap[currentEditLead.project_stage] || currentEditLead.project_stage || 'N/A';
                document.getElementById('detail-budget').innerText = budgetMap[currentEditLead.budget_range] || currentEditLead.budget_range || 'N/A';
                
                document.getElementById('edit-status').value = currentEditLead.status;
                document.getElementById('edit-notes').value = currentEditLead.notes || '';
                
                document.getElementById('edit-modal').style.display = 'flex';
            }

            function closeEditModal() {
                document.getElementById('edit-modal').style.display = 'none';
                currentEditLead = null;
            }

            async function saveLeadStatus() {
                const leadId = document.getElementById('edit-lead-id').value;
                const status = document.getElementById('edit-status').value;
                const notes = document.getElementById('edit-notes').value;
                
                try {
                    const response = await fetch(`/api/leads/${leadId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status, notes })
                    });
                    const res = await response.json();
                    
                    if (res.success) {
                        closeEditModal();
                        fetchCRMLeads();
                        fetchCRMAnalytics();
                    } else {
                        alert('שגיאה בעדכון הסטטוס.');
                    }
                } catch (e) {
                    console.error("Save error:", e);
                    alert('שגיאת שרת בשמירת הסטטוס.');
                }
            }

            // Exit-intent fallback (optional subtle trigger when cursor leaves top window)
            document.addEventListener('mouseleave', (e) => {
                if (e.clientY < 20) {
                    // Trigger modal as exit intent if not downloaded already
                    if (!localStorage.getItem('magnet_downloaded') && document.getElementById('magnet-modal').style.display !== 'flex') {
                        openMagnetModal();
                        localStorage.setItem('magnet_downloaded', 'true'); // Show once per session
                    }
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
