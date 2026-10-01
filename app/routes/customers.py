from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import mysql.connector

from app.models import CustomerCreate, CustomerUpdate, CustomerResponse
from database.connection import execute_insert, execute_select, execute_update, execute_delete, fetch_one
from queries.customer_queries import (
    INSERT_CUSTOMER, SELECT_CUSTOMER_BY_ID, SELECT_CUSTOMER_BY_EMAIL,
    SELECT_ALL_CUSTOMERS, UPDATE_CUSTOMER, DELETE_CUSTOMER
)
from utils.logger import logger

router = APIRouter(prefix="/customers", tags=["Customers"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreate):
    """Registers a new customer and stores in MySQL."""
    # Check for duplicate email
    existing = fetch_one(SELECT_CUSTOMER_BY_EMAIL, (customer.email,))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with email '{customer.email}' already exists."
        )

    try:
        new_id = execute_insert(
            INSERT_CUSTOMER,
            (customer.first_name, customer.last_name, customer.email, customer.phone, customer.password, customer.status)
        )
        created = fetch_one(SELECT_CUSTOMER_BY_ID, (new_id,))
        return created
    except mysql.connector.Error as e:
        logger.error(f"Failed to create customer: {e}")
        raise HTTPException(status_code=500, detail="Database insertion error.")

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int):
    """Retrieves customer by ID."""
    customer = fetch_one(SELECT_CUSTOMER_BY_ID, (customer_id,))
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer with id {customer_id} not found.")
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, updates: CustomerUpdate):
    """Updates customer details."""
    existing = fetch_one(SELECT_CUSTOMER_BY_ID, (customer_id,))
    if not existing:
        raise HTTPException(status_code=404, detail=f"Customer with id {customer_id} not found.")

    first_name = updates.first_name or existing["first_name"]
    last_name = updates.last_name or existing["last_name"]
    phone = updates.phone if updates.phone is not None else existing["phone"]
    status_val = updates.status or existing["status"]

    execute_update(UPDATE_CUSTOMER, (first_name, last_name, phone, status_val, customer_id))
    return fetch_one(SELECT_CUSTOMER_BY_ID, (customer_id,))

@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
def delete_customer(customer_id: int):
    """Deletes customer by ID."""
    existing = fetch_one(SELECT_CUSTOMER_BY_ID, (customer_id,))
    if not existing:
        raise HTTPException(status_code=404, detail=f"Customer with id {customer_id} not found.")

    try:
        execute_delete(DELETE_CUSTOMER, (customer_id,))
        return {"detail": f"Customer {customer_id} deleted successfully."}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=400, detail=f"Cannot delete customer: {str(e)}")

@router.post("/login")
def login_customer(req: LoginRequest):
    """Authenticates customer by email and password."""
    query = "SELECT customer_id, first_name, last_name, email, password, status FROM customers WHERE email = %s;"
    user = fetch_one(query, (req.email,))
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "success": True,
        "customer_id": user["customer_id"],
        "name": f"{user['first_name']} {user['last_name']}",
        "email": user["email"]
    }
