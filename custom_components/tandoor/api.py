"""Tandoor HTTP helpers"""

import logging

from .const import headers

import aiohttp

_LOGGER = logging.getLogger(__name__)


async def fetch_items(url: str, key: str) -> list[dict]:
    """Fetch the open (unchecked) shopping list items."""
    _LOGGER.debug(f"Fetching shopping list {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/api/shopping-list-entry/", headers=headers(key)) as response:
            _LOGGER.debug(f"Shopping list response {response}")
            payload = await response.json()
    items = payload["results"]
    return [entry for entry in items if not entry["checked"]]


async def add_item(url: str, key: str, item: str) -> None:
    """Add an item to the shopping list."""
    _LOGGER.debug(f"Adding shopping list item {item}")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{url}/api/shopping-list-entry/", headers=headers(key), json={"food": {"name": item}, "amount": "1"}) as response:
            _LOGGER.debug(f"Adding shopping list item response {response}")
            _LOGGER.debug(f"Adding shopping list item response JSON {await response.json()}")


async def remove_item(url: str, key: str, item: str) -> None:
    """Mark a shopping list item as checked."""
    _LOGGER.debug(f"Removing shopping list item {item}")
    items = await fetch_items(url, key)
    fetched_item = next((i for i in items if i["food"]["name"].lower() == item.lower()), None)
    if fetched_item is None:
        _LOGGER.info(f"Removing shopping list item {item} not found in shopping list")
        return
    fetched_item["checked"] = True
    item_id = fetched_item["id"]
    _LOGGER.debug(f"Removing shopping list item {item} request body {fetched_item}")
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{url}/api/shopping-list-entry/{item_id}/", headers=headers(key), json=fetched_item) as response:
            _LOGGER.debug(f"Removing shopping list item {item} response {response}")
            _LOGGER.debug(f"Removing shopping list item {item} response JSON {await response.json()}")


async def update_item(url: str, key: str, item_id, entry: dict) -> None:
    """Update a shopping list entry with the given body."""
    _LOGGER.debug(f"Updating shopping list item {item_id} request body {entry}")
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{url}/api/shopping-list-entry/{item_id}/", headers=headers(key), json=entry) as response:
            _LOGGER.debug(f"Updating shopping list item {item_id} response {response}")
            _LOGGER.debug(f"Updating shopping list item {item_id} response JSON {await response.json()}")


async def delete_item(url: str, key: str, item_id) -> None:
    """Permanently delete a shopping list entry by id."""
    _LOGGER.debug(f"Deleting shopping list item {item_id}")
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{url}/api/shopping-list-entry/{item_id}/", headers=headers(key)) as response:
            _LOGGER.debug(f"Deleting shopping list item {item_id} response {response}")
