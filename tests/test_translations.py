"""Every state a user can see has a translation, and no language file keeps a key en.json does not have."""

import json
from pathlib import Path
from typing import Any

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.defa_balancer.const import DOMAIN
from homeassistant.const import (
    ATTR_ASSUMED_STATE,
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_PICTURE,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_SUPPORTED_FEATURES,
    ATTR_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations, recursive_flatten

TRANSLATIONS = Path(__file__).parent.parent / "custom_components" / DOMAIN / "translations"

# Attributes every entity can carry; the frontend names them itself.
GENERIC_ATTRIBUTES = frozenset(
    {
        ATTR_ASSUMED_STATE,
        ATTR_ATTRIBUTION,
        ATTR_DEVICE_CLASS,
        ATTR_ENTITY_PICTURE,
        ATTR_FRIENDLY_NAME,
        ATTR_ICON,
        ATTR_SUPPORTED_FEATURES,
        ATTR_UNIT_OF_MEASUREMENT,
    }
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _key_paths(path: Path) -> set[str]:
    return set(recursive_flatten("", _load(path)))


def _translation(entity_translations: dict[str, Any], entry: er.RegistryEntry) -> dict[str, Any]:
    """Return the en.json block of one entity: its name, states and state attributes."""
    return entity_translations.get(entry.domain, {}).get(entry.translation_key, {})


@pytest.fixture
async def entity_translations(hass: HomeAssistant) -> dict[str, Any]:
    """Return the `entity` section of en.json."""
    return (await hass.async_add_executor_job(_load, TRANSLATIONS / "en.json")).get("entity", {})


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_every_option_has_a_state_translation(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    entity_translations: dict[str, Any],
) -> None:
    """Each option of an enum sensor or a select is translated, so no raw code reaches the UI."""
    missing = [
        f"entity.{entry.domain}.{entry.translation_key}.state.{option}"
        for entry in er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
        if (state := hass.states.get(entry.entity_id)) is not None
        for option in state.attributes.get("options") or []
        if option not in _translation(entity_translations, entry).get("state", {})
    ]

    assert not missing, f"missing in en.json: {missing}"


async def _platform_attributes(hass: HomeAssistant, domains: set[str]) -> set[tuple[str, str]]:
    """Return the (domain, attribute) pairs Home Assistant's entity platforms translate themselves."""
    keys = await async_get_translations(hass, "en", "entity_component", domains)
    return {
        (parts[1], parts[-2])
        for key in keys
        if ".state_attributes." in key and key.endswith(".name")
        for parts in [key.split(".")]
    }


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_every_attribute_has_a_display_name(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
    entity_translations: dict[str, Any],
) -> None:
    """Each attribute the integration adds has a translated display name, not the raw key."""
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    platform_attributes = await _platform_attributes(hass, {entry.domain for entry in entries})

    missing = [
        f"entity.{entry.domain}.{entry.translation_key}.state_attributes.{attribute}.name"
        for entry in entries
        if (state := hass.states.get(entry.entity_id)) is not None
        for attribute in state.attributes
        if attribute not in GENERIC_ATTRIBUTES
        and (entry.domain, attribute) not in platform_attributes
        and "name" not in _translation(entity_translations, entry).get("state_attributes", {}).get(attribute, {})
    ]

    assert not missing, f"missing in en.json: {missing}"


def test_language_files_keep_no_stale_keys() -> None:
    """A language file has no key en.json lacks; a key it lacks falls back to English."""
    reference = _key_paths(TRANSLATIONS / "en.json")

    stale = {
        path.name: sorted(extra)
        for path in sorted(TRANSLATIONS.glob("*.json"))
        if (extra := _key_paths(path) - reference)
    }

    assert not stale, json.dumps(stale, indent=2)
