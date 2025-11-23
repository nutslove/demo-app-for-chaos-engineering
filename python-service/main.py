import os
import sqlite3
import logging
from contextlib import asynccontextmanager
import time
import random
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# Configure logging - log format is set by OTEL_PYTHON_LOG_FORMAT environment variable
# Trace context injection is enabled by OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
logging.basicConfig(
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_PATH = "/data/orders.db"

# Create instrumented httpx client
httpx_client = httpx.AsyncClient()

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    await httpx_client.aclose()

app = FastAPI(title="Python Order Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_headers=["*"],
)

class Order(BaseModel):
    user_id: int
    product_name: str
    quantity: int
    address: str = "123 Main St, City, Country"
    card_number: str = "1234567890123456"

@app.get("/")
async def root():
    logger.info("Python service root endpoint called")
    return {"service": "python-fastapi", "status": "running"}

@app.post("/orders")
async def create_order(order: Order, x_chaos_scenario: str | None = Header(default=None)):
    logger.info(f"Creating order for user {order.user_id}")

    # Natural Chaos Injection
    # 1. Header-based: High Load
    if x_chaos_scenario == "high-load":
        latency = random.uniform(0.5, 2.0)
        logger.warning(f"Simulating high load: sleeping for {latency:.2f}s")
        time.sleep(latency)

    # 2. Data-based: User ID ending in 9 -> Database Timeout (simulated)
    if str(order.user_id).endswith("9"):
        logger.error(f"Simulating DB timeout for user {order.user_id}")
        time.sleep(5)
        raise HTTPException(status_code=504, detail="Database timeout")

    # Database insert (Pending)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, product_name, quantity, status) VALUES (?, ?, ?, ?)",
        (order.user_id, order.product_name, order.quantity, "pending")
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 1. Inventory Check (Node.js)
    inventory_result = None
    try:
        response = await httpx_client.post(
            "http://nodejs-service:3000/inventory/check",
            json={"product_name": order.product_name, "quantity": order.quantity}
        )
        inventory_result = response.json()
        logger.info(f"Inventory check result: {inventory_result}")
    except Exception as e:
        logger.error(f"Failed to check inventory: {e}")
        inventory_result = {"available": False, "error": str(e)}

    if not inventory_result.get("available"):
        return {
            "order_id": order_id,
            "status": "failed",
            "reason": "Inventory not available",
            "inventory_check": inventory_result
        }

    # 2. Fraud Check (Python - New Service)
    fraud_result = None
    try:
        # Calculate total amount (mock calculation for fraud check)
        estimated_amount = order.quantity * 100.0 
        
        fraud_response = await httpx_client.post(
            "http://fraud-service:5000/fraud/check",
            json={"user_id": order.user_id, "total_amount": estimated_amount}
        )
        fraud_result = fraud_response.json()
        logger.info(f"Fraud check result: {fraud_result}")
    except Exception as e:
        logger.error(f"Failed to check fraud: {e}")
        fraud_result = {"is_fraud": False, "error": str(e)} # Fail open or closed? Let's fail open for demo

    if fraud_result.get("is_fraud"):
        # Update DB status
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", ("rejected_fraud", order_id))
        conn.commit()
        conn.close()
        
        return {
            "order_id": order_id,
            "status": "rejected",
            "reason": "Fraud detected",
            "fraud_check": fraud_result
        }

    # 3. Reserve Inventory (Node.js -> Go)
    pricing_result = None
    try:
        reserve_response = await httpx_client.post(
            "http://nodejs-service:3000/inventory/reserve",
            json={"product_name": order.product_name, "quantity": order.quantity}
        )
        pricing_result = reserve_response.json()
        logger.info(f"Inventory reserved with pricing: {pricing_result}")
    except Exception as e:
        logger.error(f"Failed to reserve inventory: {e}")
        return {
            "order_id": order_id,
            "status": "failed",
            "reason": "Failed to reserve inventory",
            "error": str(e)
        }

    # 4. Payment Process (Go - New Service)
    payment_result = None
    try:
        total_price = pricing_result.get("pricing", {}).get("total_price", 0)
        payment_response = await httpx_client.post(
            "http://payment-service:8082/payment/process",
            json={"order_id": order_id, "amount": total_price, "card_number": order.card_number}
        )
        
        if payment_response.status_code != 200:
             raise Exception(f"Payment failed with status {payment_response.status_code}")
             
        payment_result = payment_response.json()
        logger.info(f"Payment result: {payment_result}")
        
    except Exception as e:
        logger.error(f"Payment failed: {e}")
        
        # COMPENSATING TRANSACTION: Release Inventory
        # In a real system, we would call a release endpoint. 
        # For this demo, we'll just log it as a compensation action.
        logger.warning(f"COMPENSATING TRANSACTION: Releasing inventory for order {order_id}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", ("payment_failed", order_id))
        conn.commit()
        conn.close()
        
        return {
            "order_id": order_id,
            "status": "failed",
            "reason": "Payment failed",
            "error": str(e),
            "compensation": "Inventory released"
        }

    # 5. Shipping Service (Python FastAPI)
    shipping_result = None
    try:
        shipping_response = await httpx_client.post(
            "http://shipping-service:5000/ship",
            json={"order_id": order_id, "address": order.address}
        )
        shipping_result = shipping_response.json()
        logger.info(f"Shipping result: {shipping_result}")
    except Exception as e:
        logger.error(f"Failed to ship order: {e}")
        shipping_result = {"error": str(e)}

    # 6. Send notification (Java)
    notification_result = None
    try:
        # Chaos: If user_id starts with 666, send to @fail.com to trigger Java service error
        email_domain = "example.com"
        if str(order.user_id).startswith("666"):
            email_domain = "fail.com"

        notification_response = await httpx_client.post(
            "http://java-service:8081/notifications/send",
            json={
                "recipient": f"user_{order.user_id}@{email_domain}",
                "message": f"Your order #{order_id} for {order.quantity}x {order.product_name} has been placed!",
                "type": "email"
            }
        )
        notification_result = notification_response.json()
        logger.info(f"Notification sent: {notification_result}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        notification_result = {"error": str(e)}

    # Update DB status to completed
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", ("completed", order_id))
    conn.commit()
    conn.close()

    logger.info(f"Order {order_id} created successfully")

    return {
        "order_id": order_id,
        "status": "completed",
        "inventory_check": inventory_result,
        "fraud_check": fraud_result,
        "pricing": pricing_result,
        "payment": payment_result,
        "shipping": shipping_result,
        "notification": notification_result
    }

@app.get("/orders")
async def get_orders():
    logger.info("Fetching all orders")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()

    logger.info(f"Retrieved {len(orders)} orders")
    return {"orders": orders}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/error")
async def intentional_error():
    logger.error("Intentional error triggered")
    raise HTTPException(status_code=500, detail="Intentional error for testing")

@app.post("/orders/error")
async def create_order_with_error(order: Order):
    logger.info(f"Creating order with intentional error for user {order.user_id}")
    # Simplified error flow for testing
    return {"status": "error", "message": "Not implemented for new flow yet"}

