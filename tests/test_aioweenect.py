"""Tests for `aioweenect.aioweenect`."""
import json
import os

import aiohttp
import pytest

from aioweenect import AioWeenect

API_HOST = "apiv4.weenect.com"
API_VERSION = "/v4"


@pytest.mark.asyncio
async def test_get_user(aresponses):
    """Test getting user information."""
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/login",
        "POST",
        response=load_json_fixture("login_response.json"),
    )
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/100000",
        "GET",
        response=load_json_fixture("get_user_response.json"),
    )
    async with aiohttp.ClientSession() as session:
        aioweenect = AioWeenect(username="user", password="password", session=session)
        response = await aioweenect.get_user("100000")

        assert response["postal_code"] == "55128"


@pytest.mark.asyncio
async def test_get_subscription_offers(aresponses):
    """Test getting subscription offer information."""
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/login",
        "POST",
        response=load_json_fixture("login_response.json"),
    )
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/subscriptionoffer",
        "GET",
        response=load_json_fixture("get_subscription_offer_response.json"),
    )
    async with aiohttp.ClientSession() as session:
        aioweenect = AioWeenect(username="user", password="password", session=session)
        response = await aioweenect.get_subscription_offers()

        assert (
            response["items"][0]["option_offers"][0]["price_offer"]["de"]["amount"]
            == 199
        )


@pytest.mark.asyncio
async def test_get_subscription(aresponses):
    """Test getting subscription information."""
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/login",
        "POST",
        response=load_json_fixture("login_response.json"),
    )
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/mysubscription/100000",
        "GET",
        response=load_json_fixture("get_subscription_response.json"),
    )
    async with aiohttp.ClientSession() as session:
        aioweenect = AioWeenect(username="user", password="password", session=session)
        response = await aioweenect.get_subscription("100000")

        assert response["options"][0]["amount"] == 99


@pytest.mark.asyncio
async def test_get_zones(aresponses):
    """Test getting zone information."""
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/login",
        "POST",
        response=load_json_fixture("login_response.json"),
    )
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/mytracker/100000/zones",
        "GET",
        response=load_json_fixture("get_zones_response.json"),
    )
    async with aiohttp.ClientSession() as session:
        aioweenect = AioWeenect(username="user", password="password", session=session)
        response = await aioweenect.get_zones("100000")

        assert response["items"][0]["distance"] == 100


@pytest.mark.asyncio
async def test_add_zone(aresponses):
    """Test adding a zone."""
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/login",
        "POST",
        response=load_json_fixture("login_response.json"),
    )
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/mytracker/100000/zones",
        "POST",
        response=load_json_fixture("add_zone_response.json"),
    )
    async with aiohttp.ClientSession() as session:
        aioweenect = AioWeenect(username="user", password="password", session=session)
        response = await aioweenect.add_zone(
            tracker_id=100000, address="test", latitude=90.0, longitude=1.0, name="test"
        )

        assert response["number"] == 186177


@pytest.mark.asyncio
async def test_get_position(aresponses):
    """Test getting position information."""
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/login",
        "POST",
        response=load_json_fixture("login_response.json"),
    )
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/mytracker/100000/position",
        "GET",
        response=load_json_fixture("get_position_response.json"),
    )
    async with aiohttp.ClientSession() as session:
        aioweenect = AioWeenect(username="user", password="password", session=session)
        response = await aioweenect.get_position("100000")

        assert response[0]["latitude"] == 49.0268016


@pytest.mark.asyncio
async def test_get_activity(aresponses):
    """Test getting activity information."""
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/login",
        "POST",
        response=load_json_fixture("login_response.json"),
    )
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/mytracker/100000/activity",
        "GET",
        response=load_json_fixture("get_activity_response.json"),
    )
    async with aiohttp.ClientSession() as session:
        aioweenect = AioWeenect(username="user", password="password", session=session)
        response = await aioweenect.get_activity(
            tracker_id="100000",
            start="2019-04-14T23:05:00.000Z",
            end="2019-04-15T23:05:00.000Z",
        )

        assert response["distance"] == 31246.108984983595


@pytest.mark.asyncio
async def test_get_trackers(aresponses):
    """Test getting tracker information."""
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/user/login",
        "POST",
        response=load_json_fixture("login_response.json"),
    )
    aresponses.add(
        API_HOST,
        f"{API_VERSION}/mytracker",
        "GET",
        response=load_json_fixture("get_trackers_response.json"),
    )
    async with aiohttp.ClientSession() as session:
        aioweenect = AioWeenect(username="user", password="password", session=session)
        response = await aioweenect.get_trackers()

        assert response["items"][0]["user"]["firstname"] == "Test"


def load_json_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, encoding="utf-8") as fptr:
        content = fptr.read()
        json_content = json.loads(content)
        return json_content
