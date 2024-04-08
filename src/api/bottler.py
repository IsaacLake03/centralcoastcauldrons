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
        greenml -= potions_delivered[0].quantity * 100
        greenPot += potions_delivered[0].quantity 
        connection.execute(
            sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :greenPot"),
            {"greenPot": greenPot})
        connection.execute(
            sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :greenml"),
            {"greenml": greenml})

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
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        greenml = result.scalar_one()

    greenPotQty = greenml // 100
    greenml = greenml % 100


    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": greenPotQty,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())