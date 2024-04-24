from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        inv = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_blue_ml, num_red_ml, num_dark_ml, gold FROM global_inventory")).first()
        ml = inv.num_green_ml + inv.num_blue_ml + inv.num_red_ml + inv.num_dark_ml
        gold = inv.gold
        potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potions")).scalar_one()
    return {"number_of_potions": potions, "ml_in_barrels": ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
    if(gold > 2000):
        return{
            "potion_capacity": 1,
            "ml_capacity": 1
        }
        

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    purchase_price = 1000 * (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity)
    with db.engine.begin() as connection:
        gold, potion_cap, ml_cap = connection.execute(sqlalchemy.text("SELECT gold, potion_cap, ml_cap FROM global_inventory")).one()
        gold -= purchase_price
        potion_cap += 50*capacity_purchase.potion_capacity
        ml_cap += 10000*capacity_purchase.ml_capacity
        connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE global_inventory SET 
                    gold = :gold,
                    potion_cap = :potion_cap,
                    ml_cap = :ml_cap
                    """),
                {"gold": gold, "potion_cap": potion_cap, "ml_cap": ml_cap})
        return "OK"
