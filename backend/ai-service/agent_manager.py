from datetime import timedelta, date
import random
from decimal import Decimal
from agents.priority_agent import PriorityAgent
from agents.cashflow_agent import CashFlowAgent
from agents.insight_agent import InsightAgent
from agents.negotiation_agent import NegotiationAgent

# Initialize agents
priority_agent = PriorityAgent()
cashflow_agent = CashFlowAgent()
insight_agent = InsightAgent()
negotiation_agent = NegotiationAgent()

def rank_obligations(obligations):
    """
    Facade for the Priority Decision Agent.
    """
    # Mock current balance for calculation
    mock_balance = 150000.00
    return priority_agent.rank(obligations, mock_balance)

def generate_cash_flow_forecast(business_id: str, current_date):
    """
    Facade for the Cash Flow Prediction Agent.
    """
    mock_balance = 150000.00
    return cashflow_agent.generate_forecast(business_id, mock_balance)

def generate_daily_digest(business_id: str, obligations=None, forecast=None, lang: str = "en"):
    """
    Facade for the Insight Agent.
    """
    if not obligations: obligations = []
    if not forecast: forecast = []
    
    return insight_agent.generate_digest("Ravi's Cloud Kitchen", obligations, forecast, lang=lang)

def draft_negotiation(vendor_name, amount, due_date):
    """
    Facade for the Negotiation Agent.
    """
    return negotiation_agent.draft_deferral(vendor_name, float(amount), due_date)

def get_negotiation_strategies(vendor_name, amount, due_date):
    return negotiation_agent.generate_strategies(vendor_name, float(amount), due_date)
