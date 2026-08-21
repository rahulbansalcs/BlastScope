from samples.payment_service.checkout import checkout
def test_checkout():
    result=checkout({"id":"ORDER-001"})
    assert result is not None