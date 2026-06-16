"""The Tandoor integration."""

import logging
from datetime import timedelta
from functools import partial

from .api import add_item, fetch_items, remove_item
from .const import ADD_ITEM_SCHEMA, DOMAIN

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up the platform from the config entry"""
    hass.data.setdefault(DOMAIN, {})

    config = dict(entry.data)
    url = config["url"]
    key = config["key"]

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"tandoor {url}",
        update_interval=SCAN_INTERVAL,
        update_method=partial(fetch_items, url, key),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady("Failed to connect") from ex

    hass.data[DOMAIN][entry.entry_id] = {
        "config": config,
        "coordinator": coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    async def add_shopping_list_item(call: ServiceCall):
        item = call.data["item"]
        await add_item(url, key, item)
        await coordinator.async_request_refresh()

    async def remove_shopping_list_item(call: ServiceCall):
        item = call.data["item"]
        await remove_item(url, key, item)
        await coordinator.async_request_refresh()

    _LOGGER.debug(f"Registering services for Tandoor {url}")
    hass.services.async_register(DOMAIN, "add_shopping_list_item", add_shopping_list_item, ADD_ITEM_SCHEMA)
    hass.services.async_register(DOMAIN, "remove_shopping_list_item", remove_shopping_list_item, ADD_ITEM_SCHEMA)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry so switch entities reflect updated options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
