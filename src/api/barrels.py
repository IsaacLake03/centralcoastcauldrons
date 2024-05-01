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
    with db.engine.begin() as connection:

        
        for barrel in barrels_delivered:
            if barrel.potion_type == [0, 1, 0, 0]:
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO ledger (item_sku, change)
                        VALUES ('green_ml', :green)
                        """
                    ),
                    {"green": barrel.ml_per_barrel*barrel.quantity})
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO ledger (item_sku, change)
                        VALUES ('gold', :cost)
                        """
                    ),
                    {"cost": -(barrel.price*barrel.quantity)})

            elif barrel.potion_type == [1, 0, 0, 0]:
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO ledger (item_sku, change)
                        VALUES ('red_ml', :red)
                        """
                    ),
                    {"red": barrel.ml_per_barrel*barrel.quantity})
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO ledger (item_sku, change)
                        VALUES ('gold', :cost)
                        """
                    ),
                    {"cost": -(barrel.price*barrel.quantity)})
            elif barrel.potion_type == [0, 0, 1, 0]:
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO ledger (item_sku, change)
                        VALUES ('blue_ml', :blue)
                        """
                    ),
                    {"blue": barrel.ml_per_barrel*barrel.quantity})
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO ledger (item_sku, change)
                        VALUES ('gold', :cost)
                        """
                    ),
                    {"cost": -(barrel.price*barrel.quantity)})
            elif barrel.potion_type == [0, 0, 0, 1]:
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO ledger (item_sku, change)
                        VALUES ('dark_ml', :dark)
                        """
                    ),
                    {"dark": barrel.ml_per_barrel*barrel.quantity})
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO ledger (item_sku, change)
                        VALUES ('gold', :cost)
                        """
                    ),
                    {"cost": -(barrel.price*barrel.quantity)})
            else:
                raise Exception("Invalid potion type")
    return "OK"
# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    order = []
    barrelsize = 200
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        greenml, blueml, darkml, redml, gold, ml_capacity = connection.execute(sqlalchemy.text(
            """
            SELECT 
                SUM(CASE WHEN item_sku LIKE '%green_ml%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%blue_ml%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%dark_ml%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%red_ml%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%gold%' THEN change ELSE 0 END),
                SUM(CASE WHEN item_sku LIKE '%cap_mils%' THEN change ELSE 0 END)
            FROM 
                ledger
            """)).first()
        
        if ml_capacity >= 50000:
            barrelsize = 5000
            connection.execute(sqlalchemy.text(
                """
                UPDATE potions
                SET price = base_price * 0.9
                """))
        else:
            connection.execute(sqlalchemy.text(
                """
                UPDATE potions
                SET price = base_price
                """))

    wholesale_catalog = sorted(wholesale_catalog, key=lambda barrel: barrel.ml_per_barrel, reverse=True)

    for barrel in wholesale_catalog:
        if barrel.potion_type == [0, 1, 0, 0] and (barrel.ml_per_barrel > barrelsize or (greenml < 1000 and barrel.ml_per_barrel > 500)):
            cap = ml_capacity/3 - greenml
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

        elif barrel.potion_type == [1, 0, 0, 0] and (barrel.ml_per_barrel > barrelsize or (greenml < 1000 and barrel.ml_per_barrel > 500)):
            cap = ml_capacity/3 - redml
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
    
        elif barrel.potion_type == [0, 0, 1, 0] and (barrel.ml_per_barrel > barrelsize or (greenml < 1000 and barrel.ml_per_barrel > 500)):
            cap = ml_capacity/3 - blueml
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
                

    return order