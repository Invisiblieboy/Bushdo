from v1 import price, info,auth
from fastapi import APIRouter

v1_router = APIRouter(prefix='/v1')
# v1_router.include_router(price.price_router)


async def init():
    pass
