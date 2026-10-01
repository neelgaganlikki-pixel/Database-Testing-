from typing import List
from fastapi import APIRouter, HTTPException, status
import mysql.connector

from app.models import CartCreate, CartItemCreate, CartResponse, CartItemResponse
from database.connection import execute_insert, fetch_one, execute_select, execute_query
from queries.cart_queries import (
    INSERT_OR_GET_CART, SELECT_CART_BY_CUSTOMER, INSERT_CART_ITEM,
    SELECT_CART_ITEMS_BY_CART_ID
)
from queries.customer_queries import SELECT_CUSTOMER_BY_ID
from queries.product_queries import SELECT_PRODUCT_BY_ID

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.post("", status_code=status.HTTP_201_CREATED)
def get_or_create_cart(cart_req: CartCreate):
    cust = fetch_one(SELECT_CUSTOMER_BY_ID, (cart_req.customer_id,))
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer {cart_req.customer_id} not found.")

    execute_query(INSERT_OR_GET_CART, (cart_req.customer_id,))
    cart = fetch_one(SELECT_CART_BY_CUSTOMER, (cart_req.customer_id,))
    return cart

@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_to_cart(item: CartItemCreate):
    # Verify customer and get cart
    cust = fetch_one(SELECT_CUSTOMER_BY_ID, (item.customer_id,))
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer {item.customer_id} not found.")

    execute_query(INSERT_OR_GET_CART, (item.customer_id,))
    cart = fetch_one(SELECT_CART_BY_CUSTOMER, (item.customer_id,))
    cart_id = cart["cart_id"]

    # Verify product
    product = fetch_one(SELECT_PRODUCT_BY_ID, (item.product_id,))
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found.")

    if product["stock_quantity"] < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock available.")

    price = float(product["price"])
    execute_query(INSERT_CART_ITEM, (cart_id, item.product_id, item.quantity, price))

    return {"message": "Item added to cart successfully", "cart_id": cart_id, "product_id": item.product_id}

@router.get("/{customer_id}", response_model=CartResponse)
def get_customer_cart(customer_id: int):
    cust = fetch_one(SELECT_CUSTOMER_BY_ID, (customer_id,))
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")

    execute_query(INSERT_OR_GET_CART, (customer_id,))
    cart = fetch_one(SELECT_CART_BY_CUSTOMER, (customer_id,))

    items_data = execute_select(SELECT_CART_ITEMS_BY_CART_ID, (cart["cart_id"],))
    cart_items = []
    total = 0.0
    for row in items_data:
        it = CartItemResponse(
            cart_item_id=row["cart_item_id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            quantity=row["quantity"],
            price=float(row["price"]),
            item_total=round(float(row["item_total"]), 2)
        )
        total += it.item_total
        cart_items.append(it)

    return CartResponse(
        cart_id=cart["cart_id"],
        customer_id=customer_id,
        status=cart["status"],
        items=cart_items,
        total_amount=round(total, 2)
    )
