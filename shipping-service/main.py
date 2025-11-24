import logging
import random
import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup OpenTelemetry
resource = Resource.create({"service.name": "shipping-service"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

LoggingInstrumentor().instrument(set_logging_format=True)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

class ShippingRequest(BaseModel):
    order_id: int
    address: str

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/ship")
async def ship_order(request: Request, shipping_req: ShippingRequest):
    logger.info(f"Received shipping request for order {shipping_req.order_id}")
    
    # Chaos Injection: Latency
    # If address contains "SLOW", inject latency
    if "SLOW" in shipping_req.address.upper():
        logger.error("[Chaos Error] Injecting latency for SLOW address")
        time.sleep(2)
        
    # Chaos Injection: Error
    # If address contains "ERROR", return 500
    if "ERROR" in shipping_req.address.upper():
        logger.error("[Chaos Error] Injecting error for ERROR address")
        raise HTTPException(status_code=500, detail="Shipping failed due to invalid address (simulated)")

    shipping_cost = 5.00
    if "INTERNATIONAL" in shipping_req.address.upper():
        shipping_cost = 25.00

    tracking_id = f"TRK-{random.randint(1000, 9999)}-{shipping_req.order_id}"
    
    logger.info(f"Order {shipping_req.order_id} shipped. Tracking: {tracking_id}")
    
    return {
        "order_id": shipping_req.order_id,
        "status": "shipped",
        "tracking_id": tracking_id,
        "cost": shipping_cost
    }
