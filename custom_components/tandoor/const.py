"""Constants"""

import voluptuous as vol

DOMAIN = "tandoor"

CONF_SWITCH_ITEMS = "switch_items"

SCHEMA = vol.Schema(
    {
        vol.Required("url"): str,
        vol.Required("key"): str,
    }
)

ADD_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required("item"): str,
    }
)

def headers(key: str):
    return {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
