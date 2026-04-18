from typing import List, Dict
import random

class InsightAgent:
    """
    Synthesizes data into a plain-English Daily Digest.
    Supports 'en' and 'hi' (Hindi).
    """
    
    def __init__(self, model_name="claude-3-5-sonnet"):
        self.model_name = model_name
        
    def generate_digest(self, biz_name: str, obligations: List[Dict], forecast: List[Dict], lang: str = "en") -> Dict:
        """
        Input: Ranked obligations and Cash flow forecast.
        Output: Summary and KPIs.
        """
        # Calculate some real KPIs from the data
        pending_total = sum(float(ob['amount']) for ob in obligations if ob['status'] == 'pending')
        high_priority_count = sum(1 for ob in obligations if ob.get('priority') == 'High' and ob['status'] == 'pending')
        
        balances = [float(f['predicted_balance']) for f in forecast]
        min_balance = min(balances) if balances else 0
        avg_burn = 5000 
        runway_days = int(balances[0] / avg_burn) if balances and avg_burn > 0 else 0

        # Build Summary in correct language
        if lang == "hi":
            summary = [
                f"नमस्ते {biz_name}!",
                f"आपके पास {runway_days} दिनों का रनवे है।",
                f"सावधानी: {high_priority_count} भुगतान तत्काल ध्यान देने योग्य हैं।"
            ]
        else:
            summary = [
                f"Hello {biz_name}!",
                f"You have approximately {runway_days} days of runway left.",
                f"Action Required: {high_priority_count} high-priority payables detected."
            ]
            
        return {
            "business_name": biz_name,
            "summary": summary,
            "lang": lang,
            "kpis": {
                "days_cash_on_hand": f"{runway_days} Days",
                "burn_rate_monthly": f"₹{(avg_burn * 30)/1000:.1f}k",
                "pending_payables": f"₹{pending_total/1000:.1f}k",
                "high_priority_count": high_priority_count,
                "risk_level": "Medium" if min_balance < 50000 else "Low"
            }
        }
