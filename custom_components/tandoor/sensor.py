"""The Tandoor sensors"""

import logging

from .const import DOMAIN

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([ShoppingList(data["coordinator"], config_entry.entry_id)])


class ShoppingList(CoordinatorEntity):
    """The shopping list sensor"""

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}-shopping-list"
        self._attr_name = "Shopping List"

    @property
    def state(self) -> str:
        items = self.coordinator.data or []
        if len(items) == 0:
            return "Empty"
        return "Full"

    @property
    def extra_state_attributes(self):
        """Return the state attributes"""
        items = self.coordinator.data or []
        return {"items": ",".join([item["food"]["name"].lower() for item in items])}
