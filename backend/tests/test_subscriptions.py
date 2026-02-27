"""Tests for subscriptions API."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Subscription
from app.models.subscription import SourceType


class TestSubscriptionsAPI:
    """Tests for subscriptions endpoints."""

    @pytest.mark.asyncio
    async def test_list_subscriptions_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing subscriptions when empty."""
        response = await client.get("/api/subscriptions", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_subscriptions(
        self, client: AsyncClient, auth_headers: dict, test_subscription: Subscription
    ):
        """Test listing subscriptions."""
        response = await client.get("/api/subscriptions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test RSS Feed"
        assert data[0]["source_type"] == "rss"

    @pytest.mark.asyncio
    async def test_create_subscription_rss(self, client: AsyncClient, auth_headers: dict):
        """Test creating an RSS subscription."""
        response = await client.post(
            "/api/subscriptions",
            headers=auth_headers,
            json={
                "name": "New RSS Feed",
                "source_type": "rss",
                "source_config": {"url": "https://test.com/feed.xml"},
                "enabled": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New RSS Feed"
        assert data["source_type"] == "rss"
        assert data["source_config"]["url"] == "https://test.com/feed.xml"

    @pytest.mark.asyncio
    async def test_create_subscription_twitter(self, client: AsyncClient, auth_headers: dict):
        """Test creating a Twitter subscription."""
        response = await client.post(
            "/api/subscriptions",
            headers=auth_headers,
            json={
                "name": "Twitter Feed",
                "source_type": "twitter",
                "source_config": {
                    "usernames": ["user1", "user2"],
                    "keywords": ["keyword1"],
                },
                "enabled": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_type"] == "twitter"
        assert "user1" in data["source_config"]["usernames"]

    @pytest.mark.asyncio
    async def test_create_subscription_webhook(self, client: AsyncClient, auth_headers: dict):
        """Test creating a webhook subscription."""
        response = await client.post(
            "/api/subscriptions",
            headers=auth_headers,
            json={
                "name": "Webhook",
                "source_type": "webhook",
                "source_config": {"source": "my-app", "secret": "secret123"},
                "enabled": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_type"] == "webhook"

    @pytest.mark.asyncio
    async def test_get_subscription(
        self, client: AsyncClient, auth_headers: dict, test_subscription: Subscription
    ):
        """Test getting a specific subscription."""
        response = await client.get(
            f"/api/subscriptions/{test_subscription.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_subscription.id
        assert data["name"] == "Test RSS Feed"

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting nonexistent subscription."""
        response = await client.get("/api/subscriptions/999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_subscription(
        self, client: AsyncClient, auth_headers: dict, test_subscription: Subscription
    ):
        """Test updating a subscription."""
        response = await client.put(
            f"/api/subscriptions/{test_subscription.id}",
            headers=auth_headers,
            json={
                "name": "Updated Feed",
                "enabled": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Feed"
        assert data["enabled"] is False

    @pytest.mark.asyncio
    async def test_update_subscription_config(
        self, client: AsyncClient, auth_headers: dict, test_subscription: Subscription
    ):
        """Test updating subscription config."""
        response = await client.put(
            f"/api/subscriptions/{test_subscription.id}",
            headers=auth_headers,
            json={
                "source_config": {"url": "https://newurl.com/feed.xml"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_config"]["url"] == "https://newurl.com/feed.xml"

    @pytest.mark.asyncio
    async def test_delete_subscription(
        self, client: AsyncClient, auth_headers: dict, test_subscription: Subscription
    ):
        """Test deleting a subscription."""
        response = await client.delete(
            f"/api/subscriptions/{test_subscription.id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = await client.get(
            f"/api/subscriptions/{test_subscription.id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing subscriptions without auth."""
        response = await client.get("/api/subscriptions")
        assert response.status_code == 401
