from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        greenPot = result.scalar()
        if greenPot is not None and greenPot >= 1:
            greenPot = 1
        else:
            return []

    return [
            {
                "sku": "GREEN_POTION_1",
                "name": "green potion",
                "quantity": greenPot,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        ]
