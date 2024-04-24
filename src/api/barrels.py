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
    with db.engine.begin() as transaction:
        greenml = transaction.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar_one()
        redml = transaction.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar_one()
        blueml = transaction.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar_one()
        gold = transaction.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
        darkml = transaction.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).scalar_one()
        
        for barrel in barrels_delivered:
            if barrel.potion_type == [0, 1, 0, 0]:
                greenml += barrel.ml_per_barrel * barrel.quantity
                gold -= barrel.price*barrel.quantity
            elif barrel.potion_type == [1, 0, 0, 0]:
                redml += barrel.ml_per_barrel * barrel.quantity
                gold -= barrel.price*barrel.quantity
            elif barrel.potion_type == [0, 0, 1, 0]:
                blueml += barrel.ml_per_barrel * barrel.quantity
                gold -= barrel.price*barrel.quantity
            elif barrel.potion_type == [0, 0, 0, 1]:
                darkml += barrel.ml_per_barrel * barrel.quantity
                gold -= barrel.price*barrel.quantity
            else:
                raise Exception("Invalid potion type")

        transaction.execute(sqlalchemy.text(
            """
            UPDATE global_inventory SET 
            num_green_ml = :greenml,
            num_red_ml = :redml,
            num_blue_ml = :blueml,
            gold = :gold
            """),
            {"darkml": darkml, "greenml": greenml, "redml": redml, "blueml": blueml, "gold": gold}
        )
        
    return "OK"
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    order = []
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        greenml, blueml, darkml, redml, gold, ml_capacity = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_blue_ml, num_dark_ml, num_red_ml, gold, ml_cap FROM global_inventory")).first()

        wholesale_catalog = sorted(wholesale_catalog, key=lambda barrel: barrel.ml_per_barrel, reverse=True)

    for barrel in wholesale_catalog:
        if barrel.potion_type == [0, 1, 0, 0] and barrel.ml_per_barrel > 200:
            cap = ml_capacity/4 - greenml
            qty = int(cap // barrel.ml_per_barrel)
            while barrel.price*qty > gold and qty > 0:
                qty -= 1
            if qty > 0:
                gold -= barrel.price*qty
                order.append({
                    "sku": barrel.sku,
                    "quantity": qty,
                })
                greenml += barrel.ml_per_barrel * qty

        elif barrel.potion_type == [1, 0, 0, 0] and barrel.ml_per_barrel > 200:
            cap = ml_capacity/4 - redml
            qty = int(cap // barrel.ml_per_barrel)
            while barrel.price*qty > gold and qty > 0:
                qty -= 1
            if qty > 0:
                gold -= barrel.price*qty
                order.append({
                    "sku": barrel.sku,
                    "quantity": qty,
                })
                redml += barrel.ml_per_barrel * qty
    
        elif barrel.potion_type == [0, 0, 1, 0] and barrel.ml_per_barrel > 200:
            cap = ml_capacity/4 - redml
            qty = int(cap // barrel.ml_per_barrel)
            while barrel.price*qty > gold and qty > 0:
                qty -= 1
            if qty > 0:
                gold -= barrel.price*qty
                order.append({
                    "sku": barrel.sku,
                    "quantity": qty,
                })
                blueml += barrel.ml_per_barrel * qty
                
        elif barrel.potion_type == [0, 0, 0, 1] and barrel.ml_per_barrel > 200:
            cap = ml_capacity/4 - redml
            qty = int(cap // barrel.ml_per_barrel)
            while barrel.price*qty > gold and qty > 0:
                qty -= 1
            if qty > 0:
                gold -= barrel.price*qty
                order.append({
                    "sku": barrel.sku,
                    "quantity": qty,
                })
                darkml += barrel.ml_per_barrel * qty

    return order