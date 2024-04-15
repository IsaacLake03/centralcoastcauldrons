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
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        greenPot = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
        greenml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar_one()
        redml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar_one()
        redPot = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
        blueml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar_one()
        bluePot = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()
        
        for potion in potions_delivered:
            if potion.potion_type == [0, 100, 0, 0]:
                greenPot += potion.quantity
                greenml -= potion.quantity*100
            elif potion.potion_type == [100, 0, 0, 0]:
                redPot += potion.quantity
                redml -= potion.quantity*100
            elif potion.potion_type == [0, 0, 100, 0]:
                bluePot += potion.quantity
                blueml -= potion.quantity*100
        connection.execute(
            sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :greenPot"),
            {"greenPot": greenPot})
        connection.execute(
            sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :greenml"),
            {"greenml": greenml})
        connection.execute(
            sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :redPot"),
            {"redPot": redPot})
        connection.execute(
            sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :redml"),
            {"redml": redml})
        connection.execute(
            sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = :bluePot"),
            {"bluePot": bluePot})
        connection.execute(
            sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = :blueml"),
            {"blueml": blueml})


    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    greenPotQty = 0
    redPotQty = 0
    bluePotQty = 0
    order = []
    with db.engine.begin() as connection:
        greenml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar_one()
        redml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar_one()
        blueml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar_one()

    while greenml >= 100:
        greenml -= 100
        greenPotQty += 1
    while redml >= 100:
        redml -= 100
        redPotQty += 1
    while blueml >= 100:
        blueml -= 100
        bluePotQty += 1
        
    if greenPotQty > 0:
        order.append(
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": greenPotQty,
            }
        )
    if redPotQty > 0:
        order.append(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": redPotQty,
            }
        )
    if bluePotQty > 0:
        order.append(
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": bluePotQty,
            }
        )
    
    return order

if __name__ == "__main__":
    print(get_bottle_plan())