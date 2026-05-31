import urllib.parse
from typing import Dict, Any, Tuple

# Elite Lead Scoring System for Omer Paz Nir (OPN Design)
# Designed to identify high-ticket residential renovations & early-stage contractor changes (Maximum Value)

BUDGET_WEIGHTS = {
    "low": 0,          # Under 100k NIS - Typically styling only
    "mid": 15,         # 100k - 300k NIS - Focused renovation / carpentry
    "high": 35,        # 300k - 600k NIS - Full apartment renovation / contractor changes
    "ultra": 50        # 600k+ NIS - Luxury residential planning / private house
}

STAGE_WEIGHTS = {
    "pre_construction": 35,   # Early contractor apartment changes (Maximum value for design work!)
    "under_construction": 20, # In-progress building
    "ready_to_move": 10       # Ready or key handover
}

PROPERTY_WEIGHTS = {
    "private_house": 25,      # House - High complexity, larger scope
    "contractor_apartment": 20,# Contractor changes / Tenants' modifications (highly profitable)
    "renovation": 15          # Standard residential renovation
}

HIGH_VALUE_LOCATIONS = {
    "tel aviv", "herzliya", "ra'anana", "ramat hasharon", "hod hasharon", 
    "kfarsaba", "kfar saba", "givatayim", "ramat gan", "savyon", "arshuf",
    "caesarea", "netanya", "rishon lezion", "rishon", "savyon", "zahala", 
    "neve tzedek", "ramat aviv", "הרצליה", "תל אביב", "רעננה", "רמת השרון", 
    "הוד השרון", "כפר סבא", "גבעתיים", "רמת גן", "סביון", "קיסריה", "נתניה", 
    "ראשון לציון", "צהלה", "נווה צדק", "רמת אביב", "ארשוף", "סביון"
}

DESIGNER_WHATSAPP_NUMBER = "972545555555"  # Replace with Omer's actual phone number in international format

def score_lead(lead_data: Dict[str, Any]) -> Tuple[int, bool]:
    """
    Evaluates lead quality based on business-aligned scoring system.
    Returns:
        (score, is_vip)
    """
    if lead_data.get("lead_type") == "lead_magnet":
        # Baseline score for guide download
        return 20, False
        
    score = 0
    
    # 1. Budget Score
    budget = lead_data.get("budget_range")
    if budget:
        budget = budget.lower()
    else:
        budget = "low"
    score += BUDGET_WEIGHTS.get(budget, 0)
    
    # 2. Project Stage Score
    stage = lead_data.get("project_stage")
    if stage:
        stage = stage.lower()
    else:
        stage = "ready_to_move"
    score += STAGE_WEIGHTS.get(stage, 10)
    
    # 3. Property Type Score
    prop_type = lead_data.get("property_type")
    if prop_type:
        prop_type = prop_type.lower()
    else:
        prop_type = "renovation"
    score += PROPERTY_WEIGHTS.get(prop_type, 15)
    
    # 4. Location Bonus (Location check)
    location = lead_data.get("location")
    if location:
        location = location.lower().strip()
        is_high_value_loc = any(loc in location for loc in HIGH_VALUE_LOCATIONS)
        if is_high_value_loc:
            score += 10
        
    # Lead is marked as VIP Hot if:
    # - Score >= 75 (Highly qualified lead on all fronts)
    # - OR Budget is Ultra
    # - OR Budget is High AND Stage is Pre-Construction (The Designer Sweet Spot)
    is_vip = (
        score >= 75 or 
        budget == "ultra" or 
        (budget == "high" and stage == "pre_construction")
    )
    
    return min(score, 100), is_vip

def generate_whatsapp_url(lead_data: Dict[str, Any], phone_number: str = DESIGNER_WHATSAPP_NUMBER) -> str:
    """
    Generates a pre-filled, highly professional WhatsApp message link using lead data.
    Provides standard and localized templates based on locale detection.
    """
    name = lead_data.get("name", "אורח/ת")
    lead_type = lead_data.get("lead_type", "consultation")
    
    if lead_type == "lead_magnet":
        message = (
            f"שלום עומר! הורדתי את המדריך שלך '5 טעויות בשינויי קבלן' באתר.\n\n"
            f"👤 שם: {name}\n"
            f"📞 טלפון: {lead_data.get('phone', '')}\n\n"
            f"המדריך נראה מעולה! אשמח אם נוכל לתאם שיחה קצרה לבחון איך אפשר לעשות תכנון מקדים נכון לנכס שלי. תודה!"
        )
    else:
        location = lead_data.get("location", "לא צוין")
        
        # Mapping keys to beautiful Hebrew descriptions
        prop_map = {
            "private_house": "בית פרטי 🏡",
            "contractor_apartment": "דירת קבלן (שינויי דיירים) 🏗️",
            "renovation": "שיפוץ דירה יסודי 🛠️"
        }
        stage_map = {
            "pre_construction": "לפני בנייה / שינויי דיירים מוקדמים (תכנון)",
            "under_construction": "בבנייה פעילה",
            "ready_to_move": "לקראת מסירה / מוכן לעיצוב"
        }
        budget_map = {
            "low": "עד 100,000 ₪",
            "mid": "100,000 ₪ - 300,000 ₪",
            "high": "300,000 ₪ - 600,000 ₪",
            "ultra": "מעל 600,000 ₪ 💎"
        }
        
        prop_desc = prop_map.get(lead_data.get("property_type"), lead_data.get("property_type", ""))
        stage_desc = stage_map.get(lead_data.get("project_stage"), lead_data.get("project_stage", ""))
        budget_desc = budget_map.get(lead_data.get("budget_range"), lead_data.get("budget_range", ""))
        
        message = (
            f"שלום עומר! מילאתי את מתכנן הפרויקטים באתר שלך. הנה פרטי הנכס שלי:\n\n"
            f"👤 שם: {name}\n"
            f"📍 מיקום: {location}\n"
            f"🏗️ סוג הפרויקט: {prop_desc}\n"
            f"⏱️ שלב הפרויקט: {stage_desc}\n"
            f"💰 תקציב מוערך: {budget_desc}\n\n"
            f"אשמח לקבוע איתך פגישת ייעוץ ראשונית כדי שנוכל לדבר על הפרויקט ולבחון התאמה. תודה!"
        )
    
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{phone_number}?text={encoded_message}"
