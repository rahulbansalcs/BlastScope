from samples.payment_service.payment import process_payment
def test_process_payment():
    result=process_payment({"id":"ORDER-001"},"INR")
    assert result["status"]=="paid"