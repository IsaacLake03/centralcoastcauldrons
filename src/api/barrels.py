from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    i=0
    for barrel in barrels_delivered:
        with db.engine.begin() as connection:
            greenml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar_one()
            redml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar_one()
            blueml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar_one()
            gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
            
            for barrel in barrels_delivered:
                if barrel.potion_type == [0, 100, 0, 0]:
                    greenml += barrel.ml_per_barrel * barrel.quantity
                    gold -= barrel.price.quantity
                elif barrel.potion_type == [100, 0, 0, 0]:
                    redml += barrel.ml_per_barrel * barrel.quantity
                    gold -= barrel.price.quantity
                elif barrel.potion_type == [0, 0, 100, 0]:
                    blueml += barrel.ml_per_barrel * barrel.quantity
                    gold -= barrel.price.quantity
                
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :greenml"),
            {"greenml": greenml})
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :redml"),
            {"redml": redml})
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = :blueml"),
            {"blueml": blueml})
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold"),
            {"gold": gold})
            connection.commit()

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    order = []
    print(wholesale_catalog)
    greenOrder = 0
    with db.engine.begin() as connection:
        greenPot = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar_one()
        redPot = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar_one()
        bluePot = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()

    for barrel in wholesale_catalog:
        if barrel.potion_type == [0, 100, 0, 0]:
            if greenPot < 10 and gold > barrel.price:
                gold -= barrel.price
                order.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
        elif barrel.potion_type == [100, 0, 0, 0]:
            if redPot < 10 and gold > barrel.price:
                gold -= barrel.price
                order.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
        elif barrel.potion_type == [0, 0, 100, 0]:
            if bluePot < 10 and gold > barrel.price:
                gold -= barrel.price
                order.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
    return order