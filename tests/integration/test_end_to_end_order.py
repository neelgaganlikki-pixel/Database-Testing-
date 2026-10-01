import pytest
from database.connection import execute_insert, fetch_one, execute_select, execute_delete
from queries.customer_queries import INSERT_CUSTOMER, SELECT_CUSTOMER_BY_ID, DELETE_CUSTOMER
from queries.product_queries import INSERT_PRODUCT, SELECT_PRODUCT_BY_ID, DELETE_PRODUCT
from queries.order_queries import SELECT_ORDER_BY_ID, SELECT_ORDER_ITEMS_BY_ORDER_ID, DELETE_ORDER
from queries.payment_queries import SELECT_PAYMENT_BY_ORDER_ID
from utils.data_generator import TestDataGenerator

@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.smoke
class TestEndToEndOrderBusinessFlow:
    """Full End-to-End E-Commerce Business Scenario validating data flow across:
       Customer -> Address -> Cart -> Order -> Order Items -> Payment -> Inventory Stock
    """

    def test_complete_end_to_end_order_lifecycle(self, api_client):
        """Validates complete business order lifecycle:
           1. Create customer via API
           2. Insert customer address in DB
           3. Create product in DB with known initial stock
           4. Add product to customer cart via API
           5. Checkout / Create order from cart via API
           6. Process payment for order via API
           7. Validate order status in DB ('confirmed')
           8. Query database to validate all related records:
              - Customer exists and is active
              - Order belongs to customer
              - Order items correctly record quantity and subtotal
              - Product stock is accurately decremented in MySQL
              - Payment amount matches order total
           9. Cleanup test data safely
        """
        # Step 1: Create Customer via API
        cust_payload = TestDataGenerator.generate_customer_data()
        cust_resp = api_client.post("/customers", json=cust_payload)
        assert cust_resp.status_code == 201
        customer = cust_resp.json()
        customer_id = customer["customer_id"]

        try:
            # Step 2: Create Address in DB
            addr_data = TestDataGenerator.generate_address_data(customer_id)
            addr_id = execute_insert(
                """
                INSERT INTO addresses (customer_id, address_line, city, state, postal_code, country, is_default)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (customer_id, addr_data["address_line"], addr_data["city"], addr_data["state"],
                 addr_data["postal_code"], addr_data["country"], addr_data["is_default"])
            )
            assert addr_id > 0

            # Step 3: Create Product with known stock (e.g. stock=50, price=75.00)
            initial_stock = 50
            order_qty = 3
            unit_price = 75.00
            prod_payload = {
                "category_id": 1,
                "product_name": f"E2E High-Tech Gadget {TestDataGenerator.generate_order_number()}",
                "description": "Used for end-to-end integration test",
                "price": unit_price,
                "stock_quantity": initial_stock,
                "status": "active"
            }
            prod_resp = api_client.post("/products", json=prod_payload)
            assert prod_resp.status_code == 201
            product = prod_resp.json()
            product_id = product["product_id"]

            # Step 4: Add Product to Cart via API
            cart_item_resp = api_client.post("/cart/items", json={
                "customer_id": customer_id,
                "product_id": product_id,
                "quantity": order_qty
            })
            assert cart_item_resp.status_code == 201

            # Verify Cart via API
            cart_resp = api_client.get(f"/cart/{customer_id}")
            assert cart_resp.status_code == 200
            cart_data = cart_resp.json()
            assert len(cart_data["items"]) == 1
            assert cart_data["items"][0]["quantity"] == order_qty

            # Step 5: Place Order from Cart via API
            order_resp = api_client.post("/orders", json={
                "customer_id": customer_id,
                "from_cart": True
            })
            assert order_resp.status_code == 201
            order_data = order_resp.json()
            order_id = order_data["order_id"]
            expected_total = round(order_qty * unit_price, 2)
            assert round(order_data["total_amount"], 2) == expected_total

            # Step 6: Process Payment via API
            pay_resp = api_client.post("/payments", json={
                "order_id": order_id,
                "payment_method": "credit_card",
                "amount": expected_total
            })
            assert pay_resp.status_code == 201
            payment_data = pay_resp.json()

            # Step 7: Direct MySQL Database Validations
            # 7a. Verify Customer in DB
            db_cust = fetch_one(SELECT_CUSTOMER_BY_ID, (customer_id,))
            assert db_cust["email"] == cust_payload["email"]

            # 7b. Verify Order in DB
            db_order = fetch_one(SELECT_ORDER_BY_ID, (order_id,))
            assert db_order is not None
            assert db_order["customer_id"] == customer_id
            assert round(float(db_order["total_amount"]), 2) == expected_total
            assert db_order["status"] == "confirmed"

            # 7c. Verify Order Items in DB
            db_items = execute_select(SELECT_ORDER_ITEMS_BY_ORDER_ID, (order_id,))
            assert len(db_items) == 1
            assert db_items[0]["product_id"] == product_id
            assert db_items[0]["quantity"] == order_qty
            assert round(float(db_items[0]["unit_price"]), 2) == unit_price
            assert round(float(db_items[0]["subtotal"]), 2) == expected_total

            # 7d. Verify Product Stock decremented in MySQL
            db_prod = fetch_one(SELECT_PRODUCT_BY_ID, (product_id,))
            expected_remaining_stock = initial_stock - order_qty
            assert db_prod["stock_quantity"] == expected_remaining_stock, (
                f"Inventory stock was not properly decremented! "
                f"Expected: {expected_remaining_stock}, Actual: {db_prod['stock_quantity']}"
            )

            # 7e. Verify Payment in DB
            db_pay = fetch_one(SELECT_PAYMENT_BY_ORDER_ID, (order_id,))
            assert db_pay is not None
            assert round(float(db_pay["amount"]), 2) == expected_total
            assert db_pay["payment_status"] == "completed"

        finally:
            # Step 8: Safe cleanup of test data
            if "order_id" in locals():
                execute_delete("DELETE FROM payments WHERE order_id = %s;", (order_id,))
                execute_delete(DELETE_ORDER, (order_id,))
            if "product_id" in locals():
                execute_delete(DELETE_PRODUCT, (product_id,))
            if customer_id:
                execute_delete(DELETE_CUSTOMER, (customer_id,))

