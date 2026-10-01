from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
import mysql.connector

from app.models import ProductCreate, ProductUpdate, ProductResponse
from database.connection import execute_insert, fetch_one, execute_select, execute_update, execute_delete
from queries.product_queries import (
    INSERT_PRODUCT, SELECT_PRODUCT_BY_ID, SELECT_ALL_PRODUCTS, UPDATE_PRODUCT, DELETE_PRODUCT
)
from queries.category_queries import SELECT_CATEGORY_BY_ID

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    # Verify category exists
    cat = fetch_one(SELECT_CATEGORY_BY_ID, (product.category_id,))
    if not cat:
        raise HTTPException(status_code=400, detail=f"Category {product.category_id} does not exist.")

    if product.price < 0:
        raise HTTPException(status_code=422, detail="Price cannot be negative.")
    if product.stock_quantity < 0:
        raise HTTPException(status_code=422, detail="Stock quantity cannot be negative.")

    try:
        new_id = execute_insert(
            INSERT_PRODUCT,
            (product.category_id, product.product_name, product.description, product.price, product.stock_quantity, product.status)
        )
        return fetch_one(SELECT_PRODUCT_BY_ID, (new_id,))
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ProductResponse])
def get_products(limit: int = 50, offset: int = 0):
    return execute_select(SELECT_ALL_PRODUCTS, (limit, offset))

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    prod = fetch_one(SELECT_PRODUCT_BY_ID, (product_id,))
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found.")
    return prod

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, updates: ProductUpdate):
    prod = fetch_one(SELECT_PRODUCT_BY_ID, (product_id,))
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found.")

    name = updates.product_name or prod["product_name"]
    desc = updates.description if updates.description is not None else prod["description"]
    price = updates.price if updates.price is not None else float(prod["price"])
    stock = updates.stock_quantity if updates.stock_quantity is not None else prod["stock_quantity"]
    status_val = updates.status or prod["status"]

    if price < 0 or stock < 0:
        raise HTTPException(status_code=422, detail="Price and stock must be non-negative.")

    execute_update(UPDATE_PRODUCT, (name, desc, price, stock, status_val, product_id))
    return fetch_one(SELECT_PRODUCT_BY_ID, (product_id,))

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int):
    prod = fetch_one(SELECT_PRODUCT_BY_ID, (product_id,))
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found.")

    try:
        execute_delete(DELETE_PRODUCT, (product_id,))
        return {"detail": f"Product {product_id} deleted successfully."}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=400, detail=f"Cannot delete product: {str(e)}")
