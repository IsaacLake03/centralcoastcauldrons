from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from typing import Dict

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    result = []

        
    previous = ""
    query = """
        SELECT cartItems.item_sku, cart.customer_id, cust.name, cust.class, cust.level, cartItems.item_qty, cartItems.date AS timestamp, pot.id AS potion_id
        FROM cart_items cartItems
        JOIN carts cart ON cartItems.cart_id = cart.id
        JOIN customers cust ON cart.customer_id = cust.id
        JOIN potions pot ON cartItems.item_sku = pot.potion_sku
    """
    params = {}
    if customer_name != "":
        query += " WHERE cust.name = :name"
        params["name"] = customer_name

    if potion_sku != "":
        query += " AND cartItems.item_sku = :item_sku" if "WHERE" in query else " WHERE cartItems.item_sku = :item_sku"
        params["item_sku"] = potion_sku
        
    if not search_page:
        search_page = "1"
    
    params["page"] = search_page
    
    if search_page and int(search_page) > 1:
        previous = str(int(search_page) - 1)
    if sort_col == "":
        sort_col = "cartItems.date"
    if sort_order == "":
        sort_order = "desc"
        
    

    query += f" ORDER BY {sort_col} {sort_order} LIMIT 5 OFFSET 5*(:page-1)"
    

    count_query = """
        SELECT COUNT(*)
        FROM cart_items cartItems
        JOIN carts cart ON cartItems.cart_id = cart.id
        JOIN customers cust ON cart.customer_id = cust.id
        JOIN potions pot ON cartItems.item_sku = pot.potion_sku
    """
    if customer_name != "":
        count_query += " WHERE cust.name = :name"
    if potion_sku != "":
        count_query += " AND cartItems.item_sku = :item_sku" if "WHERE" in count_query else " WHERE cartItems.item_sku = :item_sku"

    with db.engine.begin() as connection:
        total_results = connection.execute(sqlalchemy.text(count_query), params).scalar()

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text(query), params).fetchall()
    
    for row in results:
        result.append({
            "line_item_id": row.potion_id,
            "item_sku": row.item_sku,
            "customer_name": row.name,
            "line_item_total": row.item_qty,
            "timestamp": row.timestamp,
        })
    if total_results > 5:
        next = str(int(search_page) + 1)
    else:
        next = ""
    

    return {
        "previous": previous,
        "next": next,
        "results": result,
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    with db.engine.begin() as connection:
        day = connection.execute(sqlalchemy.text("SELECT day FROM current_day")).scalar_one()
        customerVisits = [customer.customer_name for customer in customers]
        connection.execute(sqlalchemy.text(
            f"""
            UPDATE customers
            SET "{day}" = "{day}" + 1
            WHERE name IN :customerVisits
            """
        ), {"customerVisits": tuple(customerVisits)})

    

    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
                        """
                        INSERT INTO customers (name, class, level) 
                        VALUES (:customer_name, :character_class, :level)
                        ON CONFLICT (name, class, level) DO NOTHING
                        """), 
                        {"customer_name": new_cart.customer_name, "character_class": new_cart.character_class, "level":new_cart.level})
        cust_id = connection.execute(sqlalchemy.text("SELECT id FROM customers WHERE name = :customer_name AND class = :character_class AND level = :level"),
                        {"customer_name": new_cart.customer_name, "character_class": new_cart.character_class, "level":new_cart.level}).scalar_one()
        
        cart_id = connection.execute(sqlalchemy.text(
                        """
                        INSERT INTO carts (customer_id) 
                        VALUES (:customer_id)
                        RETURNING id
                        """),
                        {"customer_id": cust_id}).scalar_one()
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int



@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:

        connection.execute(sqlalchemy.text(
                    """
                    INSERT INTO cart_items (cart_id, item_sku, item_qty)
                    VALUES (:cart_id, :sku, :quantity)
                    ON CONFLICT (cart_id, item_sku) DO UPDATE SET item_qty = :quantity
                    """),
                    {"cart_id": cart_id, "sku": item_sku, "quantity": cart_item.quantity})
    return cart_id

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potionsBought = 0
    payment = 0

    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text("SELECT item_sku, item_qty FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart_id}).fetchall()
        day = connection.execute(sqlalchemy.text("SELECT day FROM current_day")).scalar_one()
        
        for item in cart:
            price = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE potion_sku = :sku"), {"sku": item.item_sku}).scalar_one()
            payment += price*item.item_qty
            potionsBought += item.item_qty
            connection.execute(sqlalchemy.text("INSERT INTO ledger (item_sku, change) VALUES (:sku, :change)"), {"sku": item.item_sku, "change": -(item.item_qty)})
            connection.execute(sqlalchemy.text("INSERT INTO ledger (item_sku, change) VALUES ('gold', :change)"), {"change": price*item.item_qty})

    print("Payment: ", payment, "Payment type: ", cart_checkout.payment)
    
    if(potionsBought > 0):
        return {"total_potions_bought": potionsBought, "total_gold_paid": payment}
    else:
        return []