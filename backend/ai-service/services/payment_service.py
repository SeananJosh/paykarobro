import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
import models
import random

class PaymentService:
    """
    Handles payment execution logic.
    In production: Connects to Razorpay / NPCI UPI Gateway.
    Hackathon MVP: Simulates successful execution and logs to DB.
    """
    
    @staticmethod
    def execute_payment(db: Session, obligation_id: str, payment_method: str = "UPI") -> models.Payment:
        # Fetch obligation
        ob = db.query(models.Obligation).filter(models.Obligation.id == obligation_id).first()
        if not ob:
            raise Exception("Obligation not found")
            
        # 1. Simulate Gateway Interaction
        gateway_ref = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        success = random.random() > 0.05 # 95% success rate for simulation
        
        status = "success" if success else "failed"
        
        # 2. Record Payment
        payment = models.Payment(
            obligation_id=ob.id,
            business_id=ob.business_id,
            amount=ob.amount,
            payment_method=payment_method,
            gateway_ref=gateway_ref,
            status=status
        )
        db.add(payment)
        
        # 3. Update Obligation Status
        if status == "success":
            ob.status = "paid"
            
        # 4. Create Audit Log for "Action"
        audit = models.AgentAuditLog(
            business_id=ob.business_id,
            agent_name="PaymentExecutionAgent",
            input_summary=f"Executing payment for {ob.vendor_name}",
            output_summary=f"Payment {status}",
            reasoning="User-authorized execution of AI-ranked obligation.",
            user_action="approved"
        )
        db.add(audit)
        
        db.commit()
        db.refresh(payment)
        return payment
