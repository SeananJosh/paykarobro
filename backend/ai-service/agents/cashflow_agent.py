from decimal import Decimal
from datetime import date, timedelta
from typing import List, Dict
import random
import math

class CashFlowAgent:
    """
    Predicts cash flow for the next 30/60/90 days.
    In production: Uses historical bank transactions + seasonal trends + LLM commentary.
    Hackathon MVP: Rule-based simulation with trend analysis.
    """
    
    def __init__(self, model_name="gpt-4o"):
        self.model_name = model_name
        
    def generate_forecast(self, business_id: str, current_balance: float, days: int = 30) -> List[Dict]:
        forecast_data = []
        today = date.today()
        
        # Simulated variables
        daily_growth_trend = 0.002 # 0.2% daily growth
        volatility = 0.15 # 15% volatility
        
        running_balance = float(current_balance)
        
        for i in range(1, days + 1):
            target_date = today + timedelta(days=i)
            
            # Trend calculation
            trend_impact = running_balance * daily_growth_trend
            
            # Seasonality (Weekend dip, Month-end spike)
            seasonality = 1.0
            if target_date.weekday() >= 5: # Weekend
                seasonality = 0.8
            if target_date.day >= 25: # Month end spike for SME
                seasonality = 1.3
                
            # Random noise
            noise = random.uniform(-volatility, volatility) * running_balance
            
            # Daily change
            daily_change = (trend_impact * seasonality) + noise
            running_balance += daily_change
            
            forecast_data.append({
                "date": target_date.strftime("%Y-%m-%d"),
                "predicted_balance": running_balance,
                "confidence_lower": running_balance * 0.85,
                "confidence_upper": running_balance * 1.15,
                "is_weekend": target_date.weekday() >= 5
            })
            
        return forecast_data

    def get_commentary(self, forecast: List[Dict]) -> str:
        """
        Simulated LLM commentary on the forecast.
        """
        final_bal = forecast[-1]["predicted_balance"]
        start_bal = forecast[0]["predicted_balance"]
        
        if final_bal > start_bal:
            return "Positive trend detected. Liquidity expected to improve by 15% over the next 30 days due to month-end receivables."
        else:
            return "Warning: Slight downward trend in liquidity. Recommended to defer non-essential payables in week 3."
