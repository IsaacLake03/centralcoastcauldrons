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
        redml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar_one()
        greenml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar_one()
        blueml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar_one()
        darkml = connection.execute(sqlalchemy.text("SELECT num_dark_ml FROM global_inventory")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar_one()
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions")).fetchall()
        greenpotions = 0
        redpotions = 0
        bluepotions = 0
        darkpotions = 0
        for potion in potions:
            if potion.red >= 10:
                redpotions += potion.quantity
            if potion.green >= 10:
                greenpotions += potion.quantity
            if potion.blue >= 10:
                bluepotions += potion.quantity
            if potion.dark >= 10:
                darkpotions += potion.quantity

    for barrel in wholesale_catalog:
        if barrel.potion_type == [0, 1, 0, 0]:
            if greenml < 100 and gold > barrel.price and greenpotions < 15:
                gold -= barrel.price
                order.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
        elif barrel.potion_type == [1, 0, 0, 0]:
            if redml < 100 and gold > barrel.price and redpotions < 15:
                gold -= barrel.price
                order.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
        elif barrel.potion_type == [0, 0, 1, 0]:
            if blueml < 100 and gold > barrel.price and bluepotions < 15:
                gold -= barrel.price
                order.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })
        elif barrel.potion_type == [0, 0, 0, 1]:
            if darkml < 100 and gold > barrel.price and darkpotions < 15:
                gold -= barrel.price
                order.append({
                    "sku": barrel.sku,
                    "quantity": 1,
                })

        
    return order