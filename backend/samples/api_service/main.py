from fastapi import FastAPI
from samples.payment_service.payment import process_payment
app=FastAPI()
@app.post("/checkout")
def checkout():
    order={"id":"ORDER-001"}
    return process_payment(order)
@app.get("/health")
def health():
    return {"status":"healthy"}