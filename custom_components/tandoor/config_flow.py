"""Config flow to setup Tandoor"""

import logging

from .const import SCHEMA
from .const import DOMAIN
from .const import headers

import aiohttp
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
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
    """Config flow to set up whirlpool laundry"""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the user step"""
        logging.error("Step user")
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
    
class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect"""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth"""
