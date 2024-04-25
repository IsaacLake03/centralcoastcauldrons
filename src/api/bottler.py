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
        greenml, redml, blueml, darkml = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml FROM global_inventory")).first()
        potions = connection.execute(sqlalchemy.text("SELECT quantity, green, red, blue, dark, id FROM potions")).fetchall()

        updated_quantities = {}
        for potion in potions_delivered:
            for pot in potions:
                if pot.red == potion.potion_type[0] and pot.green == potion.potion_type[1] and pot.blue == potion.potion_type[2] and pot.dark == potion.potion_type[3]:
                    updated_quantities[pot.id] = pot.quantity + potion.quantity
                    greenml -= potion.quantity * pot.green
                    redml -= potion.quantity * pot.red
                    blueml -= potion.quantity * pot.blue
                    darkml -= potion.quantity * pot.dark
                    break

        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                num_dark_ml = :darkml,
                num_green_ml = :greenml,
                num_red_ml = :redml,
                num_blue_ml = :blueml
                """),
            {"greenml": greenml, "redml": redml, "blueml": blueml, "darkml":darkml})

        for pot_id, quantity in updated_quantities.items():
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE potions SET
                    quantity = :quantity
                    WHERE id = :potion_id
                    """),
            {"quantity": quantity, "potion_id": pot_id})

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
    order = []
    with db.engine.begin() as connection:
        greenml, redml, blueml, darkml, potion_cap = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml, potion_cap FROM global_inventory")).first()
        potions = connection.execute(sqlalchemy.text("SELECT red, green, blue, dark, id, quantity FROM potions")).fetchall()
        potionqty = 0
        for potion in potions:
            potionqty += potion.quantity
            
        ml = darkml + greenml + redml + blueml


    increments = {potion.id: 0 for potion in potions}
    run = True

    while ml >= 100 and run:
        run = False
        for potion in potions:
            if(potionqty<potion_cap):
                if potion.quantity <= increments[potion.id] and potion.red <= redml and potion.green <= greenml and potion.blue <= blueml and potion.dark <= darkml:
                    increments[potion.id] += 1
                    potionqty +=1
                    darkml -= potion.dark
                    greenml -= potion.green
                    redml -= potion.red
                    blueml -= potion.blue
                    ml -= 100
                    run = True
    if ml>=100:
        while ml >= 100 and potionqty<potion_cap:
            for potion in potions:
                if(potionqty<potion_cap):
                    if potion.red <= redml and potion.green <= greenml and potion.blue <= blueml and potion.dark <= darkml:
                        increments[potion.id] += 1
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
            
    return order

if __name__ == "__main__":
    print(get_bottle_plan())