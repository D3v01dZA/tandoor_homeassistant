"""The Tandoor shopping list todo entity"""

import logging

from .api import add_item, delete_item, update_item
from .const import DOMAIN

from homeassistant import config_entries
from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][config_entry.entry_id]
    config = data["config"]
    async_add_entities([TandoorShoppingListTodo(data["coordinator"], config_entry.entry_id, config["url"], config["key"])])


class TandoorShoppingListTodo(CoordinatorEntity, TodoListEntity):
    """Todo list backed by the Tandoor shopping list, supporting add/update/delete."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(self, coordinator, entry_id, url, key):
        super().__init__(coordinator)
        self._url = url
        self._key = key
        self._attr_unique_id = f"{entry_id}-shopping-list-todo"
        self._attr_name = "Shopping List"
        self.entity_id = "todo.tandoor_shopping_list"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Tandoor",
            manufacturer="Tandoor",
            configuration_url=url,
        )

    @property
    def todo_items(self) -> list[TodoItem]:
        items = self.coordinator.data or []
        return [
            TodoItem(
                summary=entry["food"]["name"],
                uid=str(entry["id"]),
                status=TodoItemStatus.NEEDS_ACTION,
            )
            for entry in items
        ]

    @property
    def extra_state_attributes(self):
        """Expose the item names as an attribute for templating."""
        items = self.coordinator.data or []
        return {"items": ",".join([entry["food"]["name"].lower() for entry in items])}

    async def async_create_todo_item(self, item: TodoItem) -> None:
        await add_item(self._url, self._key, item.summary)
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        entries = self.coordinator.data or []
        entry = next((e for e in entries if str(e["id"]) == item.uid), None)
        if entry is None:
            _LOGGER.info(f"Updating shopping list item {item.uid} not found in shopping list")
            return
        entry = dict(entry)
        if item.summary is not None:
            entry["food"] = {**entry["food"], "name": item.summary}
        if item.status is not None:
            entry["checked"] = item.status == TodoItemStatus.COMPLETED
        await update_item(self._url, self._key, item.uid, entry)
        # Refresh immediately (rather than the debounced request) so a checked
        # item drops off the list straight away.
        await self.coordinator.async_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            await delete_item(self._url, self._key, uid)
        await self.coordinator.async_request_refresh()
