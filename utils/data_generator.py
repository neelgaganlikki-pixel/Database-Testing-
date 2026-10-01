import uuid
import time
import random
from typing import Dict, Any
from faker import Faker

fake = Faker()

class TestDataGenerator:
    """Utility class to generate realistic and unique test data."""

    @staticmethod
    def generate_customer_data(status: str = "active") -> Dict[str, Any]:
        """Generates unique customer information."""
        unique_suffix = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}.{unique_suffix}@example.com"
        phone = f"+1-555-{random.randint(1000, 9999)}"
        password = f"TestP@ss!{random.randint(100, 999)}"
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "password": password,
            "status": status,
        }

    @staticmethod
    def generate_product_data(category_id: int, status: str = "active") -> Dict[str, Any]:
        """Generates realistic product data."""
        adjective = fake.word().capitalize()
        item_name = random.choice([
            "Smart Wireless Keyboard", "Ergonomic Optical Mouse", "4K Ultra Gaming Monitor",
            "Thermal Insulated Water Bottle", "Stainless Steel Travel Mug", "Wireless Charger Pad",
            "USB-C Multiport Hub", "Bluetooth Portable Speaker", "Noise Isolating Earbuds",
            "Adjustable Laptop Stand"
        ])
        unique_suffix = uuid.uuid4().hex[:5]
        product_name = f"{adjective} {item_name} {unique_suffix}"
        description = fake.sentence(nb_words=10)
        price = round(random.uniform(9.99, 499.99), 2)
        stock_quantity = random.randint(10, 200)

        return {
            "category_id": category_id,
            "product_name": product_name,
            "description": description,
            "price": price,
            "stock_quantity": stock_quantity,
            "status": status,
        }

    @staticmethod
    def generate_category_data() -> Dict[str, Any]:
        """Generates unique product category data."""
        unique_suffix = uuid.uuid4().hex[:6]
        category_name = f"Category_{fake.word().capitalize()}_{unique_suffix}"
        description = fake.sentence(nb_words=8)
        return {
            "category_name": category_name,
            "description": description,
            "status": "active"
        }

    @staticmethod
    def generate_address_data(customer_id: int, is_default: bool = True) -> Dict[str, Any]:
        """Generates customer address data."""
        return {
            "customer_id": customer_id,
            "address_line": fake.street_address(),
            "city": fake.city(),
            "state": fake.state(),
            "postal_code": fake.zipcode(),
            "country": "USA",
            "is_default": is_default
        }

    @staticmethod
    def generate_order_number() -> str:
        """Generates unique e-commerce order number."""
        timestamp = time.strftime("%Y%m%d%H%M%S")
        rand_hex = uuid.uuid4().hex[:4].upper()
        return f"ORD-{timestamp}-{rand_hex}"

    @staticmethod
    def generate_payment_reference() -> str:
        """Generates unique payment transaction reference."""
        timestamp = time.strftime("%Y%m%d%H%M%S")
        rand_hex = uuid.uuid4().hex[:6].upper()
        return f"PAY-{timestamp}-{rand_hex}"

    @staticmethod
    def generate_order_data(customer_id: int, total_amount: float = 0.0, status: str = "pending") -> Dict[str, Any]:
        """Generates order data structure."""
        return {
            "customer_id": customer_id,
            "order_number": TestDataGenerator.generate_order_number(),
            "total_amount": round(total_amount, 2),
            "status": status
        }

    @staticmethod
    def generate_payment_data(order_id: int, amount: float, method: str = "credit_card", status: str = "completed") -> Dict[str, Any]:
        """Generates payment data."""
        return {
            "order_id": order_id,
            "payment_reference": TestDataGenerator.generate_payment_reference(),
            "amount": round(amount, 2),
            "payment_method": method,
            "payment_status": status
        }
