from fastapi import APIRouter, HTTPException, status
import mysql.connector

from app.models import PaymentCreate, PaymentResponse
from database.connection import execute_insert, fetch_one, execute_update
from queries.payment_queries import INSERT_PAYMENT, SELECT_PAYMENT_BY_ID
from queries.order_queries import SELECT_ORDER_BY_ID, UPDATE_ORDER_STATUS
from utils.data_generator import TestDataGenerator

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payment_req: PaymentCreate):
    order = fetch_one(SELECT_ORDER_BY_ID, (payment_req.order_id,))
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {payment_req.order_id} not found.")

    payment_ref = TestDataGenerator.generate_payment_reference()
    payment_status = "completed"

    try:
        new_id = execute_insert(
            INSERT_PAYMENT,
            (payment_req.order_id, payment_ref, payment_req.amount, payment_req.payment_method, payment_status)
        )
        # Update order status to confirmed
        execute_update(UPDATE_ORDER_STATUS, ("confirmed", payment_req.order_id))
        return fetch_one(SELECT_PAYMENT_BY_ID, (new_id,))
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int):
    payment = fetch_one(SELECT_PAYMENT_BY_ID, (payment_id,))
    if not payment:
        raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found.")
    return payment
