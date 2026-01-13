"""The Zyxel integration."""
import asyncio
import logging
from datetime import timedelta
import requests

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.ha_zyxel.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Block excessive nr7101 debug logging
nr7101_logger = logging.getLogger("nr7101.nr7101")
nr7101_logger.setLevel(logging.WARNING)

from nr7101 import nr7101

PLATFORMS = ["sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zyxel integration from a config entry."""


    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    try:
        router = await hass.async_add_executor_job(
            nr7101.NR7101, host, username, password
        )
    except Exception as ex:
        _LOGGER.error("Could not connect to Zyxel router: %s", ex)
        raise ConfigEntryNotReady from ex

    async def async_update_data():
        """Fetch data from the router."""
        def get_all_data(retries=2):
            while retries > 0:
                try:                        
                    data = router.get_json_object('status')
                    if data:
                        return data
                    
                    # when data is empty but does not throw an exception
                    retries -= 1
                    
                except requests.exceptions.HTTPError as e:
                    _LOGGER.debug("Zyxel HTTP Error (%s), retries left: %s", e.response.status_code, retries - 1)
                    if e.response.status_code == 401:
                        # Unauthorized - attempt login
                        login_success = router.login()
                        if not login_success:
                            break
                    elif e.response.status_code == 500:
                        # Internal server error - retry without cookies
                        router.clear_cookies()
                    retries -= 1
                except Exception as err:
                    _LOGGER.error("Unexpected error reading from Zyxel: %s", err)
                    break
            
            return None
        
        try:
            async with async_timeout.timeout(30):
                return await hass.async_add_executor_job(get_all_data)
        except Exception as err:
            # Force new login at next retry
            router._session_valid = False 
            _LOGGER.debug("Error updating Zyxel data: %s", err)
            raise UpdateFailed(f"Error communicating with router: {err}") from err


    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "router": router,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
