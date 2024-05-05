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
        ml, gold, potions = connection.execute(sqlalchemy.text(
            """
            SELECT 
                SUM(CASE WHEN item_sku LIKE '%ml%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%gold%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%POTION%' THEN change ELSE 0 END)
            FROM 
                ledger
            """)).fetchone()
    return {"number_of_potions": potions, "ml_in_barrels": ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        gold, potion_cap, ml_cap = connection.execute(sqlalchemy.text(
            """
            SELECT 
                SUM(CASE WHEN item_sku LIKE '%gold%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%cap_pots%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%cap_mils%' THEN change ELSE 0 END)
            FROM 
                ledger
            """)).fetchone()
    if gold > 3000:
        if(ml_cap < 30000):
            return{
                "potion_capacity": 0,
                "ml_capacity": 2
            }
        elif(ml_cap > 90000):
            return{
                "potion_capacity": 2,
                "ml_capacity": 0
            }
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
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger (item_sku, change)
                VALUES ('gold', :gold)
                """),
            {"gold": -purchase_price})
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger (item_sku, change)
                VALUES ('cap_pots', :potion_capacity)
                """),
            {"potion_capacity": 50*capacity_purchase.potion_capacity})
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger (item_sku, change)
                VALUES ('cap_mils', :ml_capacity)
                """),
            {"ml_capacity": 10000*capacity_purchase.ml_capacity})
        return "OK"
