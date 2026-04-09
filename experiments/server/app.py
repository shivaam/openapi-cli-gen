"""
Minimal FastAPI test server for prototyping openapi-cli-gen.

Run: uvicorn experiments.server.app:app --reload
Or:  python experiments/server/app.py
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Test API", version="0.1.0")

# === In-memory storage ===
USERS: dict[str, dict] = {}
ORDERS: dict[str, dict] = {}
TAGS: dict[int, dict] = {}
_tag_counter = 0


# === Models ===
class Address(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None


class UserCreate(BaseModel):
    name: str
    email: str
    age: int | None = None
    role: str = "user"
    address: Address | None = None
    tags: list[str] | None = None


class Company(BaseModel):
    name: str
    website: str | None = None
    address: Address | None = None
    ceo: dict | None = None


class RetryConfig(BaseModel):
    max_attempts: int = 3
    backoff: dict | None = None


class JobConfig(BaseModel):
    name: str
    parallelism: int = 1
    retry: RetryConfig | None = None
    environment: dict[str, str] | None = None
    labels: dict[str, str] | None = None


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float | None = None


class OrderCreate(BaseModel):
    customer_id: str
    items: list[OrderItem]
    notes: str | None = None
    shipping_address: Address | None = None


class TagModel(BaseModel):
    id: int | None = None
    name: str


# === Users CRUD ===
@app.get("/users", tags=["users"])
def list_users(limit: int = 20, offset: int = 0, role: str | None = None):
    users = list(USERS.values())
    if role:
        users = [u for u in users if u.get("role") == role]
    return {"items": users[offset : offset + limit], "total": len(users)}


@app.post("/users", status_code=201, tags=["users"])
def create_user(user: UserCreate):
    user_id = str(uuid.uuid4())
    data = {"id": user_id, **user.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    USERS[user_id] = data
    return data


@app.get("/users/{user_id}", tags=["users"])
def get_user(user_id: str):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    return USERS[user_id]


@app.put("/users/{user_id}", tags=["users"])
def update_user(user_id: str, user: UserCreate):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    USERS[user_id].update(user.model_dump())
    return USERS[user_id]


@app.delete("/users/{user_id}", status_code=204, tags=["users"])
def delete_user(user_id: str):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    del USERS[user_id]


# === Orders ===
@app.get("/orders", tags=["orders"])
def list_orders(status: str | None = None, customer_id: str | None = None):
    orders = list(ORDERS.values())
    if status:
        orders = [o for o in orders if o.get("status") == status]
    if customer_id:
        orders = [o for o in orders if o.get("customer_id") == customer_id]
    return orders


@app.post("/orders", status_code=201, tags=["orders"])
def create_order(order: OrderCreate):
    order_id = str(uuid.uuid4())
    total = sum((item.price or 0) * item.quantity for item in order.items)
    data = {
        "id": order_id,
        **order.model_dump(),
        "total": total,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ORDERS[order_id] = data
    return data


@app.get("/orders/{order_id}", tags=["orders"])
def get_order(order_id: str):
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    return ORDERS[order_id]


# === Companies ===
@app.post("/companies", status_code=201, tags=["companies"])
def create_company(company: Company):
    return company.model_dump()


# === Jobs (deep nesting) ===
JOBS: list[dict] = []


@app.post("/jobs", status_code=201, tags=["jobs"])
def create_job(job: JobConfig):
    data = job.model_dump()
    JOBS.append(data)
    return data


@app.get("/jobs", tags=["jobs"])
def list_jobs():
    return JOBS


# === Notifications (discriminated union) ===
@app.post("/notifications", tags=["notifications"])
def send_notification(notification: dict):
    return {"status": "sent", "notification": notification}


# === Tags (simple flat) ===
@app.get("/tags", tags=["tags"])
def list_tags():
    return list(TAGS.values())


@app.post("/tags", status_code=201, tags=["tags"])
def create_tag(tag: TagModel):
    global _tag_counter
    _tag_counter += 1
    data = {"id": _tag_counter, "name": tag.name}
    TAGS[_tag_counter] = data
    return data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
