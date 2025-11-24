import logging
import random
import time
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fraud Detection Service")

# Auto-instrumentation
LoggingInstrumentor().instrument(set_logging_format=True)
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)

class FraudCheckRequest(BaseModel):
    user_id: int
    total_amount: float

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/fraud/check")
async def check_fraud(request: FraudCheckRequest, x_chaos_scenario: str | None = Header(default=None)):
    logger.info(f"Checking fraud for user {request.user_id} with amount {request.total_amount}")
    
    with tracer.start_as_current_span("fraud_analysis") as span:
        span.set_attribute("user.id", request.user_id)
        span.set_attribute("amount", request.total_amount)

        # Chaos: High Latency (Complex ML Model Simulation)
        if x_chaos_scenario == "high-load" or x_chaos_scenario == "fraud-latency":
            latency = random.uniform(1.0, 3.0)
            logger.error(f"[Chaos Error] Simulating complex ML model latency: {latency:.2f}s")
            time.sleep(latency)

        # Chaos: False Positives
        # Reject orders from users with ID starting with '4' (e.g., 4, 42, 404)
        if str(request.user_id).startswith("4"):
            logger.error(f"[Chaos Error] Fraud detected for user {request.user_id} (Simulated False Positive)")
            span.set_attribute("fraud.detected", True)
            return {"is_fraud": True, "reason": "Suspicious user activity pattern detected"}

        # Chaos: Random Rejection for high amounts (> 10000)
        if request.total_amount > 10000 and random.random() < 0.3:
             logger.error(f"[Chaos Error] Fraud detected for high amount {request.total_amount}")
             span.set_attribute("fraud.detected", True)
             return {"is_fraud": True, "reason": "High value transaction risk"}

        logger.info("No fraud detected")
        span.set_attribute("fraud.detected", False)
        return {"is_fraud": False, "reason": "Clean"}
