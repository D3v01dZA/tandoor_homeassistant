"""The Tandoor switches"""

import logging

from .api import add_item, remove_item
from .const import CONF_SWITCH_ITEMS, DOMAIN

from homeassistant import config_entries
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][config_entry.entry_id]
    config = data["config"]
    coordinator = data["coordinator"]
    items = config_entry.options.get(CONF_SWITCH_ITEMS, [])
    async_add_entities(
        ShoppingListItemSwitch(coordinator, config_entry.entry_id, config["url"], config["key"], item)
        for item in items
    )


class ShoppingListItemSwitch(CoordinatorEntity, SwitchEntity):
    """Switch that toggles a configured item on/off the shopping list."""

    def __init__(self, coordinator, entry_id, url, key, item_name):
        super().__init__(coordinator)
        self._url = url
        self._key = key
        self._item_name = item_name
        slug = slugify(item_name)
        self._attr_unique_id = f"{entry_id}-shopping-list-switch-{slug}"
        self._attr_name = item_name
        self.entity_id = f"switch.tandoor_{slug}"

    @property
    def is_on(self) -> bool:
        items = self.coordinator.data or []
        return any(item["food"]["name"].lower() == self._item_name.lower() for item in items)

    async def async_turn_on(self, **kwargs) -> None:
        await add_item(self._url, self._key, self._item_name)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await remove_item(self._url, self._key, self._item_name)
        await self.coordinator.async_request_refresh()
