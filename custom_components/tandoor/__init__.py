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

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up the platform from the config entry"""
    hass.data.setdefault(DOMAIN, {})
    
    config = dict(entry.data)
    url = config["url"]
    key = config["key"]
    _LOGGER.debug(f"Setting up Tandoor {url}")

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

    _LOGGER.debug(f"Registering services for Tandoor {url}")
    hass.services.async_register(DOMAIN, "add_shopping_list_item", add_shopping_list_item, ADD_ITEM_SCHEMA)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok