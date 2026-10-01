from typing import List
from fastapi import APIRouter, HTTPException, status
import mysql.connector

from app.models import CategoryCreate, CategoryResponse
from database.connection import execute_insert, fetch_one, execute_select
from queries.category_queries import INSERT_CATEGORY, SELECT_CATEGORY_BY_ID, SELECT_CATEGORY_BY_NAME, SELECT_ALL_CATEGORIES

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(cat: CategoryCreate):
    existing = fetch_one(SELECT_CATEGORY_BY_NAME, (cat.category_name,))
    if existing:
        raise HTTPException(status_code=409, detail=f"Category '{cat.category_name}' already exists.")

    try:
        new_id = execute_insert(INSERT_CATEGORY, (cat.category_name, cat.description, cat.status))
        return fetch_one(SELECT_CATEGORY_BY_ID, (new_id,))
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[CategoryResponse])
def get_all_categories():
    return execute_select(SELECT_ALL_CATEGORIES)

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int):
    cat = fetch_one(SELECT_CATEGORY_BY_ID, (category_id,))
    if not cat:
        raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found.")
    return cat
