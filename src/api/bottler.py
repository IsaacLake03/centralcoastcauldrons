from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT green, red, blue, dark, potion_sku FROM potions")).fetchall()
        
        # This iterates through the potions_delivered list and checks if the potion delivered is in the potions list.
        # If it is, it will add the quantity of the potion delivered to the ledger. And subtract the ml of the potions
        # used to make the potion from the ledger.
        for potion in potions_delivered:
            for pot in potions:
                if pot.red == potion.potion_type[0] and pot.green == potion.potion_type[1] and pot.blue == potion.potion_type[2] and pot.dark == potion.potion_type[3]:
                    connection.execute(
                        sqlalchemy.text(
                            """
                            INSERT INTO ledger (item_sku, change)
                            VALUES (:sku, :quantity)
                            """
                        ),
                        {"sku": pot.potion_sku, "quantity": potion.quantity})
                    connection.execute(
                        sqlalchemy.text(
                            """
                            INSERT INTO ledger (item_sku, change)
                            VALUES ('red_ml', :red)
                            """
                        ),
                        {"red": -(pot.red*potion.quantity)})
                    connection.execute(
                        sqlalchemy.text(
                            """
                            INSERT INTO ledger (item_sku, change)
                            VALUES ('green_ml', :green)
                            """
                        ),
                        {"green": -(pot.green*potion.quantity)})
                    connection.execute(
                        sqlalchemy.text(
                            """
                            INSERT INTO ledger (item_sku, change)
                            VALUES ('blue_ml', :blue)
                            """
                        ),
                        {"blue": -(pot.blue*potion.quantity)})
                    connection.execute(
                        sqlalchemy.text(
                            """
                            INSERT INTO ledger (item_sku, change)
                            VALUES ('dark_ml', :dark)
                            """
                        ),
                        {"dark": -(pot.dark*potion.quantity)})
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    order = []
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text("SELECT red, green, blue, dark, id, quantity FROM potions")).fetchall()
        potionqty, potion_cap, greenml, redml, blueml, darkml = connection.execute(sqlalchemy.text("""
            SELECT 
                SUM(CASE WHEN item_sku LIKE '%POTION%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%cap_pots%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%green_ml%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%red_ml%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%blue_ml%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%dark_ml%' THEN change ELSE 0 END)
            FROM 
                ledger
            """)).fetchone()
        ml = darkml + greenml + redml + blueml


    increments = {potion.id: 0 for potion in potions}
    run = True

    while ml >= 100 and run and potionqty<potion_cap:
        run = False
        for potion in potions:
            if(potionqty<potion_cap):
                if potion.quantity <= increments[potion.id] and potion.red <= redml and potion.green <= greenml and potion.blue <= blueml and potion.dark <= darkml:
                    increments[potion.id] += 1
                    potionqty +=1
                    print(potionqty, potion_cap)
                    darkml -= potion.dark
                    greenml -= potion.green
                    redml -= potion.red
                    blueml -= potion.blue
                    ml -= 100
                    run = True
    while ml >= 100 and potionqty<potion_cap:
        for potion in potions:
            if(potionqty<potion_cap):
                if potion.red <= redml and potion.green <= greenml and potion.blue <= blueml and potion.dark <= darkml:
                    increments[potion.id] += 1
                    potionqty +=1
                    darkml -= potion.dark
                    greenml -= potion.green
                    redml -= potion.red
                    blueml -= potion.blue
                    ml -= 100
    for potion in potions:
        if increments[potion.id] >= 1:
            order.append({
                "potion_type": [potion.red, potion.green, potion.blue, potion.dark],
                "quantity": increments[potion.id],
            })
        increments[potion.id] = 0
            
    print(potionqty, potion_cap)
    return order

if __name__ == "__main__":
    print(get_bottle_plan())