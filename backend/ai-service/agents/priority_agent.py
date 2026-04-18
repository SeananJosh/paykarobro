from decimal import Decimal
from datetime import date
from typing import List, Dict
import random

class PriorityAgent:
    """
    Ranks financial obligations based on multiple factors:
    1. Due Date Urgency (40%)
    2. Penalty Risk (30%)
    3. Vendor Importance (20%)
    4. Cash Availability (10%)
    """
    
    def __init__(self, model_name="gpt-4o"):
        self.model_name = model_name
        # In a real scenario, we would initialize LangChain here
        
    def rank(self, obligations: List, current_balance: Decimal) -> List[Dict]:
        ranked_results = []
        today = date.today()
        
        for ob in obligations:
            # Calculate days remaining
            days_left = (ob.due_date - today).days
            
            # 1. Urgency Score (0-100)
            # 0 days or overdue = 100, 30+ days = 0
            urgency_score = max(0, min(100, (30 - days_left) * 3.33)) if days_left > 0 else 100
            
            # 2. Simulated Penalty Risk (0-100)
            # High risk for rent and utilities
            penalty_risk = 80 if ob.category in ["Rent", "Utilities", "Tax"] else 40
            
            # 3. Simulated Vendor Importance (Fixed for demo)
            importance_map = {
                "CloudKitchen Supplies": 90,
                "Zomato Ads": 60,
                "Office Rent": 95
            }
            vendor_importance = importance_map.get(ob.vendor_name, 50)
            
            # 4. Cash Impact (Simulated)
            # If the amount is a large % of balance, score it lower to preserve liquidity
            _bal = float(current_balance)
            _amt = float(ob.amount)
            cash_impact = 100 - min(100, (_amt / _bal) * 100) if _bal > 0 else 0
            
            # Weighted Final Score
            final_score = (
                (urgency_score * 0.4) + 
                (penalty_risk * 0.3) + 
                (vendor_importance * 0.2) + 
                (cash_impact * 0.1)
            )
            
            # Determine Priority Label
            if final_score > 80: priority = "High"
            elif final_score > 50: priority = "Medium"
            else: priority = "Low"
            
            # Reasoning Generation (Simulated LLM response)
            reasoning = self._generate_reasoning(ob, days_left, priority, penalty_risk)
            
            ranked_results.append({
                "id": ob.id,
                "vendor_name": ob.vendor_name,
                "amount": float(ob.amount),
                "due_date": str(ob.due_date),
                "priority": priority,
                "priority_score": float(final_score),
                "ai_reasoning": reasoning,
                "status": ob.status
            })
            
        return sorted(ranked_results, key=lambda x: x["priority_score"], reverse=True)

    def _generate_reasoning(self, ob, days_left, priority, penalty_risk):
        if days_left <= 0:
            return f"CRITICAL: Payment is overdue. Immediate execution recommended to avoid legal/penalty risk."
        
        if ob.category == "Rent":
            return f"{priority} Priority: Essential operational expense. Landlord relations are vital for business continuity."
            
        if days_left < 3:
            return f"{priority} Priority: Payment due in {days_left} days. Penalty risk of {penalty_risk}% detected if delayed."
            
        if ob.amount > 50000:
            return f"{priority} Priority: Large amount. Recommended to pay in installments or verify liquidity buffer first."
            
        return f"Routine {ob.category} expense. Normal priority based on current cash flow."
