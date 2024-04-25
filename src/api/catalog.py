from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    #Max of 6 potions
    order = []
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT potion_sku, name, price, red, green, blue, dark FROM potions")).fetchall()
        for potion in potions:
            quantity = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ledger WHERE item_sku = :sku"), {"sku": potion.potion_sku}).scalar_one() or 0
            if(quantity>=1):
                order.append({
                    "sku": potion.potion_sku,
                    "name": potion.name,
                    "quantity": quantity,
                    "price": potion.price,
                    "potion_type": [potion.red, potion.green, potion.blue, potion.dark],
                })
    return order
