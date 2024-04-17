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

cart_ids: Dict[int, Dict[str, int]] = {}

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

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
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
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    cart_id = len(cart_ids)+1
    cart_ids[cart_id] = {}
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int



@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    cart_ids[cart_id][item_sku] = cart_item.quantity
    return cart_ids[cart_id][item_sku]

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    if cart_id not in cart_ids:
        return []

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
        Gpotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
        Rpotions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
        Bpotions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()
        payment = 0
        potionsBought = 0
        
        if "GREEN_POTION_1" in cart_ids[cart_id]:
            payment += cart_ids[cart_id]["GREEN_POTION_1"]*50
            Gpotions -= cart_ids[cart_id]["GREEN_POTION_1"]
            potionsBought += cart_ids[cart_id]["GREEN_POTION_1"]
            
        if "RED_POTION_0" in cart_ids[cart_id]:
            payment += cart_ids[cart_id]["RED_POTION_0"]*50
            Rpotions -= cart_ids[cart_id]["RED_POTION_0"]
            potionsBought += cart_ids[cart_id]["RED_POTION_0"]
    
        if "BLUE_POTION_2" in cart_ids[cart_id]:
            payment += cart_ids[cart_id]["BLUE_POTION_2"]*50
            Bpotions -= cart_ids[cart_id]["BLUE_POTION_2"]
            potionsBought += cart_ids[cart_id]["BLUE_POTION_2"]

    print("Payment: ", payment, "Gold: ", gold, "Gpotions: ", Gpotions, "Rpotions: ", Rpotions, "Bpotions: ", Bpotions)
    
    gold += payment
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                gold = :gold,
                num_green_potions = :Gpotions,
                num_red_potions = :Rpotions,
                num_blue_potions = :Bpotions
                """),
        {"gold": gold, "Gpotions": Gpotions, "Rpotions": Rpotions, "Bpotions": Bpotions})
    
    if(potionsBought > 0):
        return {"total_potions_bought": potionsBought, "total_gold_paid": payment}
    else:
        return []