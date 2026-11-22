from fastapi import APIRouter

from app.api.v1 import auth, orders, payments, shops, subscriptions, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(subscriptions.router)
api_router.include_router(payments.router)
api_router.include_router(shops.router)
api_router.include_router(orders.router)
