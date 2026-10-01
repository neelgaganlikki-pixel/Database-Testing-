from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# Customer Models
class CustomerCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=4)
    status: Optional[str] = Field("active", pattern="^(active|inactive|suspended)$")

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")

class CustomerResponse(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    status: str

# Category Models
class CategoryCreate(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = "active"

class CategoryResponse(BaseModel):
    category_id: int
    category_name: str
    description: Optional[str] = None
    status: str

# Product Models
class ProductCreate(BaseModel):
    category_id: int
    product_name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    stock_quantity: int = Field(0, ge=0)
    status: Optional[str] = "active"

class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0.0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None

class ProductResponse(BaseModel):
    product_id: int
    category_id: int
    product_name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int
    status: str

# Cart Models
class CartCreate(BaseModel):
    customer_id: int

class CartItemCreate(BaseModel):
    customer_id: int
    product_id: int
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel):
    cart_item_id: int
    product_id: int
    product_name: str
    quantity: int
    price: float
    item_total: float

class CartResponse(BaseModel):
    cart_id: int
    customer_id: int
    status: str
    items: List[CartItemResponse] = []
    total_amount: float = 0.0

# Order Models
class OrderItemInput(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    customer_id: int
    items: Optional[List[OrderItemInput]] = None
    from_cart: bool = False

class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|processing|shipped|delivered|cancelled)$")

class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    order_number: str
    total_amount: float
    status: str
    items: List[OrderItemResponse] = []

# Payment Models
class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str = Field("credit_card", pattern="^(credit_card|debit_card|paypal|bank_transfer|crypto)$")
    amount: float = Field(..., ge=0.0)

class PaymentResponse(BaseModel):
    payment_id: int
    order_id: int
    payment_reference: str
    amount: float
    payment_method: str
    payment_status: str
