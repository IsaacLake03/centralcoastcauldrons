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
            result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
            greenml = result.scalar_one()
            greenml += barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity
            result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
            gold = result.scalar_one()
            gold -= barrels_delivered[i].price * barrels_delivered[i].quantity
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :greenml"),
            {"greenml": greenml})
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold"),
            {"gold": gold})
            i+=1

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    greenOrder = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        greenPot = result.scalar_one()
        if greenPot < 10:
            greenOrder = 1
    green=0
    i=0
    for barrel in wholesale_catalog:
        i+=1
        if barrel.potion_type == [0, 100, 0, 0]:
            green=i
    if greenOrder == 0:
        return []
 
    return [
        {
            "sku": wholesale_catalog[green].sku,
            "quantity": greenOrder,
        }
    ]

