from typing import Dict, List
import random

class NegotiationAgent:
    """
    Advanced Negotiation Agent for drafting professional financial interactions.
    Provides multiple templates and 'tones' based on the relationship with the vendor.
    """
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        
    def generate_strategies(self, vendor_name: str, amount: float, due_date: str) -> List[Dict]:
        """
        Returns multiple negotiation strategies and their corresponding drafts.
        """
        strategies = [
            {
                "tone": "Professional Deferral",
                "risk": "Low",
                "draft": self._draft_professional(vendor_name, amount, due_date)
            },
            {
                "tone": "Urgent Liquidity Logic",
                "risk": "Medium",
                "draft": self._draft_urgent(vendor_name, amount, due_date)
            },
            {
                "tone": "Partnership Alignment",
                "risk": "Low",
                "draft": self._draft_partnership(vendor_name, amount, due_date)
            }
        ]
        return strategies

    def _draft_professional(self, vendor: str, amt: float, date: str) -> str:
        return f"""
Subject: Regarding Invoice #{random.randint(1000, 9999)} - Payment Update

Dear {vendor} Accounts Payable,

I am writing regarding our outstanding balance of ₹{amt:,.2f} scheduled for {date}. 

Due to a temporary shift in our internal reconciliation cycles, we would like to request a short-term deferral of this payment to {self._get_future_date(10)}. 

We value our partnership and ensure that all future payments remain on schedule. Thank you for your continued support.

Best,
Ravi
"""

    def _draft_urgent(self, vendor: str, amt: float, date: str) -> str:
        return f"""
Subject: URGENT: Payment Schedule Adjustment - {vendor}

Hi {vendor} Team,

We are currently optimizing our operational cash flow for the current quarter. To maintain our project timelines, we need to adjust the payment date for our current invoice (₹{amt:,.2f}) to {self._get_future_date(14)}.

We appreciate your flexibility as we scale our operations this month. Please let us know if you require any additional documentation.

Best regards,
Ravi
"""

    def _draft_partnership(self, vendor: str, amt: float, date: str) -> str:
        return f"""
Subject: Strengthening our Partnership - Financial Alignment

Dear {vendor},

As one of our key strategic partners, we wanted to reach out regarding our upcoming payment of ₹{amt:,.2f}. 

To better align with our new bi-weekly settlement process, we would like to move this specific payment to {self._get_future_date(7)}. This alignment will allow for smoother transaction processing moving forward.

We look forward to many more months of successful collaboration.

Warmly,
Ravi
"""

    def _get_future_date(self, days: int) -> str:
        from datetime import date, timedelta
        return (date.today() + timedelta(days=days)).strftime("%d %b %Y")
        
    def draft_deferral(self, vendor_name: str, amount: float, due_date: str, reason: str = None) -> str:
        """Standard method for backward compatibility with the facade"""
        return self._draft_professional(vendor_name, amount, due_date)
