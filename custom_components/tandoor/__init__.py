"""The Tandoor integration."""

import logging

from .const import DOMAIN
from .const import ADD_ITEM_SCHEMA
from .const import headers

import aiohttp
from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up the platform from the config entry"""
    hass.data.setdefault(DOMAIN, {})
    
    config = dict(entry.data)
    url = config["url"]
    key = config["key"]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/api/shopping-list-entry/", headers=headers(key)) as response:
                _LOGGER.debug(f"Shopping list response {response}")
                await response.json()
        await session.close()
    except Exception as ex:
        raise ConfigEntryNotReady("Failed to connect") from ex

    hass.data[DOMAIN][entry.entry_id] = config
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def add_shopping_list_item(call: ServiceCall):
        item = call.data["item"]
        _LOGGER.debug(f"Adding shopping list item {item}")
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/api/shopping-list-entry/", headers=headers(key), json={"food": {"name": item}, "amount": ""}) as response:
                _LOGGER.debug(f"Adding shopping list item response {response}")
                _LOGGER.debug(f"Adding shopping list item response JSON {await response.json()}")
        await session.close()

    async def remove_shopping_list_item(call: ServiceCall):
        item = call.data["item"]
        _LOGGER.debug(f"Removing shopping list item {item}")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/api/shopping-list-entry/", headers=headers(key)) as response:
                _LOGGER.debug(f"Removing shopping list item {item} list items response {response}")
                fetched_items = await response.json()
                fetched_items = fetched_items["results"]
                fetched_items = [entry for entry in fetched_items if not entry["checked"]]
                _LOGGER.debug(f"Removing shopping list item {item} list items response JSON {fetched_items}")
            fetched_item = next((fetched_item for fetched_item in fetched_items if fetched_item["food"]["name"].lower() == item.lower()), None)
            if fetched_item is None:
                _LOGGER.info(f"Removing shopping list item {item} not found in shopping list")
            else:
                id = fetched_item["id"]
                fetched_item["checked"] = True
                _LOGGER.debug(f"Removing shopping list item {item} request body {fetched_item}")
                async with session.put(f"{url}/api/shopping-list-entry/{id}/", headers=headers(key), json=fetched_item) as response:
                    _LOGGER.debug(f"Removing shopping list item {item} response {response}")
                    fetched_items = await response.json()
                    _LOGGER.debug(f"Removing shopping list item {item} response JSON {fetched_items}")
        await session.close()

    _LOGGER.debug(f"Registering services for Tandoor {url}")
    hass.services.async_register(DOMAIN, "add_shopping_list_item", add_shopping_list_item, ADD_ITEM_SCHEMA)
    hass.services.async_register(DOMAIN, "remove_shopping_list_item", remove_shopping_list_item, ADD_ITEM_SCHEMA)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
