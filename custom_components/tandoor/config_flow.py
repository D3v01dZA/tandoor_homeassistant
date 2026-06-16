"""Config flow to setup Tandoor"""

import logging

from .const import CONF_SWITCH_ITEMS, DOMAIN, SCHEMA, headers

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from typing import Any

_LOGGER = logging.getLogger(__name__)

async def validate_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate that the data is correct"""
    url = user_input["url"]
    key = user_input["key"]

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/api/", headers=headers(key)) as response:
            if not response.ok:
                logging.error(f"Response: {response}")
                raise CannotConnect
            await response.json()
        await session.close()

class TandoorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow to set up Tandoor"""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the user step"""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=SCHEMA)

        errors = {}

        try:
            await validate_input(user_input)
            self._abort_if_unique_id_configured()
            await self.async_set_unique_id(user_input["key"].lower(), raise_on_progress=False)
            return self.async_create_entry(title=user_input["url"], data=user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except aiohttp.client_exceptions.InvalidURL:
            errors["base"] = "cannot_connect"
        except Exception:
            errors["base"] = "unknown"

        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return TandoorOptionsFlow()


class TandoorOptionsFlow(config_entries.OptionsFlow):
    """Options flow to manage URL, key, and shopping list item switches."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        entry = self.config_entry
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input["url"]
            key = user_input["key"]
            items = user_input.get(CONF_SWITCH_ITEMS, [])
            try:
                await validate_input({"url": url, "key": key})
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except aiohttp.client_exceptions.InvalidURL:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

            if not errors:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={"url": url, "key": key},
                )
                return self.async_create_entry(title="", data={CONF_SWITCH_ITEMS: items})

        current_items = entry.options.get(CONF_SWITCH_ITEMS, [])
        current_url = (user_input or {}).get("url", entry.data.get("url", ""))
        current_key = (user_input or {}).get("key", entry.data.get("key", ""))
        schema = vol.Schema(
            {
                vol.Required("url", default=current_url): str,
                vol.Required("key", default=current_key): str,
                vol.Optional(CONF_SWITCH_ITEMS, default=current_items): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=current_items,
                        multiple=True,
                        custom_value=True,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect"""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth"""
