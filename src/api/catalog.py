from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    order = []
    with db.engine.begin() as connection:
        #greenPot = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
        #redPot = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
        #bluePot = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions")).fetchall()
        
        for potion in potions:
            if(potion.quantity>=1):
                order.append({
                    "sku": potion.potion_sku,
                    "name": potion.name,
                    "quantity": potion.quantity,
                    "price": potion.price,
                    "potion_type": [potion.red, potion.green, potion.blue, potion.dark],
                })
                
        #if greenPot >= 1:
        #    order.append({
        #        "sku": "GREEN_POTION_1",
        #        "name": "green potion",
        #        "quantity": 1,
        #        "price": 50,
        #        "potion_type": [0, 100, 0, 0],
        #    })
        #if redPot >= 1:
        #    order.append({
        #        "sku": "RED_POTION_0",
        #        "name": "red potion",
        #        "quantity": 1,
        #        "price": 50,
        #        "potion_type": [100, 0, 0, 0],
        #    })
        #if bluePot >= 1:
        #    order.append({
        #        "sku": "BLUE_POTION_2",
        #        "name": "blue potion",
        #        "quantity": 1,
        #        "price": 50,
        #        "potion_type": [0, 0, 100, 0],
        #    })
        
    return order
