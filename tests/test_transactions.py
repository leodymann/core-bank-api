import httpx
import pytest


pytestmark = pytest.mark.asyncio


async def test_enqueue_transfer_is_idempotent(client: httpx.AsyncClient) -> None:
    headers = {"X-API-Key": "test-secret"}

    source = (
        await client.post(
            "/accounts",
            headers=headers,
            json={"owner_name": "Source Account", "initial_balance": "500.00"},
        )
    ).json()
    destination = (
        await client.post(
            "/accounts",
            headers=headers,
            json={"owner_name": "Destination Account", "initial_balance": "25.00"},
        )
    ).json()

    payload = {
        "source_account_id": source["id"],
        "destination_account_id": destination["id"],
        "amount": "75.00",
    }
    transfer_headers = {**headers, "Idempotency-Key": "transfer-key-0001"}

    first_response = await client.post(
        "/transactions/transfers",
        headers=transfer_headers,
        json=payload,
    )
    second_response = await client.post(
        "/transactions/transfers",
        headers=transfer_headers,
        json=payload,
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 202

    first = first_response.json()
    second = second_response.json()
    assert first["transaction_id"] == second["transaction_id"]
    assert first["duplicated"] is False
    assert second["duplicated"] is True
