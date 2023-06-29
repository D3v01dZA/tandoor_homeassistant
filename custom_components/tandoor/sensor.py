"""The Tandoor sensors"""

import logging

from .const import DOMAIN
from .const import headers

import aiohttp
from homeassistant import config_entries
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    config = hass.data[DOMAIN][config_entry.entry_id]
    url = config["url"]
    _LOGGER.debug(f"Creating shopping list for {url}")
    list = ShoppingList(config_entry.entry_id, url, config["key"])
    _LOGGER.debug(f"Updating shopping list for {url}")
    await list.async_update()
    _LOGGER.debug(f"Adding shopping list for {url}")
    async_add_entities([list])
    

class ShoppingList(Entity):
    """An item on the shopping list"""

    def __init__(self, entry_id, url, key):
        self._unique_id = f"{entry_id}-shopping-list"
        self._url = url
        self._key = key
        self._items = []
    
    @property
    def name(self):
        """Return the name of the sensor."""
        return "Shopping List"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this client."""
        return self._unique_id

    @property
    def state(self) -> str:
        if len(self._items) == 0:
            return "Empty"
        return "Full"
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes"""
        attr = {}
        attr["items"] = ",".join([item["food"]["name"] for item in self._items])
        return attr
    
    async def async_update(self):
        _LOGGER.debug(f"Updating shopping list {self._url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self._url}/api/shopping-list-entry/?checked=false", headers=headers(self._key)) as response:
                _LOGGER.debug(f"Shopping list response {response}")
                items = await response.json()
                _LOGGER.debug(f"Shopping list response JSON {items}")
                self._items = items
        await session.close()
