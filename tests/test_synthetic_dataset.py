from scripts.generate_synthetic_offers import rows


def test_synthetic_dataset_has_exact_size_and_distribution():
    offers = rows()
    assert len(offers) == 1000
    assert len({item["offer_id"] for item in offers}) == 1000
    assert len({item["platform_id"] for item in offers}) == 5
    assert len({item["bank_id"] for item in offers if item["bank_id"]}) == 10
    assert {item["payment_method"] for item in offers} == {
        "CREDIT",
        "DEBIT",
        "NO_CARD",
    }


def test_synthetic_dataset_is_varied_and_unambiguously_classified():
    offers = rows()
    assert len({item["discount_value"] for item in offers}) >= 8
    assert len({item["min_transaction"] for item in offers}) == 8
    assert {item["publish_status"] for item in offers} == {
        "READY",
        "DRAFT",
        "HIDDEN",
    }
    assert all(item["data_classification"] == "SYNTHETIC_TEST" for item in offers)
    assert all(item["is_test_data"] is True for item in offers)
