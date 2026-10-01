from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
import mysql.connector

from app.models import OrderCreate, OrderResponse, OrderItemResponse, OrderStatusUpdate
from database.connection import DatabaseManager, fetch_one, execute_select, execute_update
from queries.customer_queries import SELECT_CUSTOMER_BY_ID
from queries.product_queries import SELECT_PRODUCT_BY_ID, UPDATE_PRODUCT_STOCK
from queries.cart_queries import SELECT_CART_BY_CUSTOMER, SELECT_CART_ITEMS_BY_CART_ID, DELETE_CART_ITEMS_BY_CART
from queries.order_queries import (
    INSERT_ORDER, SELECT_ORDER_BY_ID, INSERT_ORDER_ITEM,
    SELECT_ORDER_ITEMS_BY_ORDER_ID, UPDATE_ORDER_STATUS
)
from utils.data_generator import TestDataGenerator

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_req: OrderCreate):
    cust = fetch_one(SELECT_CUSTOMER_BY_ID, (order_req.customer_id,))
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer {order_req.customer_id} not found.")

    items_to_order = []
    if order_req.from_cart:
        cart = fetch_one(SELECT_CART_BY_CUSTOMER, (order_req.customer_id,))
        if not cart:
            raise HTTPException(status_code=400, detail="No cart found for customer.")
        cart_items = execute_select(SELECT_CART_ITEMS_BY_CART_ID, (cart["cart_id"],))
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty.")
        for ci in cart_items:
            items_to_order.append({"product_id": ci["product_id"], "quantity": ci["quantity"]})
    elif order_req.items:
        for it in order_req.items:
            items_to_order.append({"product_id": it.product_id, "quantity": it.quantity})
    else:
        raise HTTPException(status_code=400, detail="Must provide order items or specify from_cart=True.")

    # Execute order creation in a single ACID transaction
    order_number = TestDataGenerator.generate_order_number()
    with DatabaseManager() as db:
        conn = db.connect()
        cursor = conn.cursor(dictionary=True)
        try:
            total_amount = 0.0
            order_items_prepared = []

            for item in items_to_order:
                cursor.execute(SELECT_PRODUCT_BY_ID, (item["product_id"],))
                prod = cursor.fetchone()
                if not prod:
                    raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found.")
                if prod["stock_quantity"] < item["quantity"]:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for product {prod['product_name']}.")

                unit_price = float(prod["price"])
                subtotal = round(unit_price * item["quantity"], 2)
                total_amount += subtotal

                order_items_prepared.append({
                    "product_id": prod["product_id"],
                    "product_name": prod["product_name"],
                    "quantity": item["quantity"],
                    "unit_price": unit_price,
                    "subtotal": subtotal
                })

                # Deduct stock
                cursor.execute(UPDATE_PRODUCT_STOCK, (item["quantity"], prod["product_id"], item["quantity"]))

            # Insert order
            cursor.execute(INSERT_ORDER, (order_req.customer_id, order_number, total_amount, "pending"))
            new_order_id = cursor.lastrowid

            # Insert order items
            for oi in order_items_prepared:
                cursor.execute(
                    INSERT_ORDER_ITEM,
                    (new_order_id, oi["product_id"], oi["quantity"], oi["unit_price"], oi["subtotal"])
                )

            # Clear cart if checked out from cart
            if order_req.from_cart and cart:
                cursor.execute(DELETE_CART_ITEMS_BY_CART, (cart["cart_id"],))

            conn.commit()

            return get_order(new_order_id)
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int):
    order = fetch_one(SELECT_ORDER_BY_ID, (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")

    items_data = execute_select(SELECT_ORDER_ITEMS_BY_ORDER_ID, (order_id,))
    items = [
        OrderItemResponse(
            order_item_id=row["order_item_id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            quantity=row["quantity"],
            unit_price=float(row["unit_price"]),
            subtotal=float(row["subtotal"])
        )
        for row in items_data
    ]

    return OrderResponse(
        order_id=order["order_id"],
        customer_id=order["customer_id"],
        order_number=order["order_number"],
        total_amount=float(order["total_amount"]),
        status=order["status"],
        items=items
    )

@router.put("/{order_id}/status", response_model=OrderResponse)
def update_status(order_id: int, status_update: OrderStatusUpdate):
    order = fetch_one(SELECT_ORDER_BY_ID, (order_id,))
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")

    execute_update(UPDATE_ORDER_STATUS, (status_update.status, order_id))
    return get_order(order_id)
