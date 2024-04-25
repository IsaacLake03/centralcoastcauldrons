from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:

        connection.execute(
            sqlalchemy.text(
                """
                DELETE FROM carts
                """))
        connection.execute(
            sqlalchemy.text(
                """
                DELETE FROM cart_items
                """))
        connection.execute(
            sqlalchemy.text(
                """
                DELETE FROM ledger
                """))
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger (item_sku, change)
                VALUES ('gold', 100)
                """))
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger (item_sku, change)
                VALUES ('cap_mils', 10000)
                """))
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ledger (item_sku, change)
                VALUES ('cap_pots', 50)
                """))
    return "OK"

