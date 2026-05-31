import os
import unittest
from scoring import score_lead, generate_whatsapp_url
from database import init_db, save_lead, get_all_leads, update_lead_status, get_analytics_summary, DATABASE_PATH

class TestOPNLeadEngine(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize database in current directory
        init_db()
        print("[OK] Database initialized successfully.")

    def test_1_lead_scoring_standard(self):
        """
        Verify that standard leads score correctly without VIP status.
        """
        lead = {
            "name": "יוסי לוי",
            "email": "yossi@example.com",
            "phone": "0521111111",
            "property_type": "renovation",
            "location": "ראשון לציון",
            "project_stage": "ready_to_move",
            "budget_range": "mid"
        }
        score, is_vip = score_lead(lead)
        self.assertFalse(is_vip, "Standard renovation with mid budget should not be VIP.")
        self.assertTrue(score > 0, f"Score should be positive, got {score}")
        print(f"[OK] Standard lead score: {score} (VIP: {is_vip})")

    def test_2_lead_scoring_vip_contractor(self):
        """
        Verify that the 'early contractor change sweet spot' triggers VIP status.
        """
        lead = {
            "name": "שירה כהן",
            "email": "shira@example.com",
            "phone": "0542222222",
            "property_type": "contractor_apartment",
            "location": "הרצליה פיתוח",
            "project_stage": "pre_construction", # Early planning phase
            "budget_range": "high"               # High budget
        }
        score, is_vip = score_lead(lead)
        self.assertTrue(is_vip, "Early contractor change with high budget MUST trigger VIP status.")
        self.assertTrue(score >= 75, f"VIP score should be >= 75, got {score}")
        print(f"[OK] VIP Contractor sweet-spot lead score: {score} (VIP: {is_vip})")

    def test_3_lead_scoring_ultra_budget(self):
        """
        Verify that ultra luxury budgets always trigger VIP.
        """
        lead = {
            "name": "דוד אריאלי",
            "email": "david@luxury.com",
            "phone": "0583333333",
            "property_type": "private_house",
            "location": "סביון",
            "project_stage": "under_construction",
            "budget_range": "ultra"              # Ultra budget
        }
        score, is_vip = score_lead(lead)
        self.assertTrue(is_vip, "Ultra luxury budget MUST trigger VIP status.")
        print(f"[OK] VIP Ultra budget lead score: {score} (VIP: {is_vip})")

    def test_4_lead_scoring_magnet(self):
        """
        Verify that lead magnet downloads score correctly.
        """
        lead = {
            "name": "רוני גרין",
            "email": "roni@green.com",
            "phone": "0534444444",
            "lead_type": "lead_magnet"
        }
        score, is_vip = score_lead(lead)
        self.assertEqual(score, 20, "Lead magnet download should receive standard baseline score of 20.")
        self.assertFalse(is_vip, "Lead magnet download should not be marked as VIP.")
        print(f"[OK] Lead magnet score: {score} (VIP: {is_vip})")

    def test_5_database_operations(self):
        """
        Verify database insert, retrieval, status updates, and analytics aggregation.
        """
        # Test lead definition
        lead = {
            "name": "אלון לוי",
            "email": "alon@example.com",
            "phone": "0505555555",
            "property_type": "private_house",
            "location": "נווה צדק",
            "project_stage": "pre_construction",
            "budget_range": "ultra",
            "lead_type": "consultation"
        }
        score, is_vip = score_lead(lead)
        url = generate_whatsapp_url(lead)
        
        # 1. Save
        lead_id = save_lead(lead, score, is_vip, url)
        self.assertTrue(lead_id > 0, "Saved lead ID should be greater than 0.")
        print(f"[OK] Saved lead successfully. Assigned ID: {lead_id}")
        
        # 2. Get All
        leads = get_all_leads()
        self.assertTrue(len(leads) > 0, "Retrieved leads list should not be empty.")
        saved_lead = next((l for l in leads if l["id"] == lead_id), None)
        self.assertIsNotNone(saved_lead, "Saved lead should exist in the retrieved list.")
        self.assertEqual(saved_lead["name"], "אלון לוי")
        self.assertEqual(saved_lead["is_vip"], 1)
        self.assertEqual(saved_lead["status"], "new")
        print("[OK] Lead successfully verified in database query.")
        
        # 3. Update Status
        updated = update_lead_status(lead_id, "scheduled", "קבענו פגישה ליום שישי בבוקר")
        self.assertTrue(updated, "Update status should return True.")
        
        # Re-fetch and check update
        leads_updated = get_all_leads()
        updated_lead = next((l for l in leads_updated if l["id"] == lead_id), None)
        self.assertEqual(updated_lead["status"], "scheduled")
        self.assertEqual(updated_lead["notes"], "קבענו פגישה ליום שישי בבוקר")
        print("[OK] Lead status and notes update successfully verified.")
        
        # 4. Analytics Summary
        analytics = get_analytics_summary()
        self.assertTrue(analytics["total_leads"] > 0, "Analytics total leads should be positive.")
        self.assertTrue(analytics["vip_leads"] > 0, "Analytics VIP leads count should be positive.")
        self.assertEqual(analytics["statuses"].get("scheduled", 0), 1, "Analytics status counting should reflect 'scheduled' state.")
        print(f"[OK] Analytics Aggregate Summary verified: {analytics}")

if __name__ == "__main__":
    unittest.main()
