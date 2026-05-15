from decimal import Decimal

import httpx
import pytest


pytestmark = pytest.mark.asyncio


async def test_create_and_get_account(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/accounts",
        headers={"X-API-Key": "test-secret"},
        json={"owner_name": "Ada Lovelace", "initial_balance": "120.50"},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["owner_name"] == "Ada Lovelace"
    assert Decimal(created["balance"]) == Decimal("120.50")

    response = await client.get(
        f"/accounts/{created['id']}",
        headers={"X-API-Key": "test-secret"},
    )

    assert response.status_code == 200
    fetched = response.json()
    assert fetched["id"] == created["id"]
    assert fetched["owner_name"] == "Ada Lovelace"


async def test_requires_api_key(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/accounts",
        json={"owner_name": "Grace Hopper", "initial_balance": "10.00"},
    )

    assert response.status_code == 401
