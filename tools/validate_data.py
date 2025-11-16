#!/usr/bin/env python3
"""Data validation tool voor Tri-Sarira RPG.

Dit script valideert alle JSON en TOML bestanden in het project.

Usage:
    python -m tools.validate_data
    python tools/validate_data.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Add src to path so we can import from tri_sarira_rpg
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from tri_sarira_rpg.core.config import Config
from tri_sarira_rpg.data_access.repository import DataRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)


def validate_config() -> bool:
    """Valideer config/default_config.toml.

    Returns
    -------
    bool
        True als config OK is
    """
    logger.info("=" * 70)
    logger.info("Validating TOML Configuration")
    logger.info("=" * 70)

    try:
        config = Config.load(root=project_root)
        logger.info("✓ Config loaded successfully")
        logger.info(f"  - Resolution: {config.resolution}")
        logger.info(f"  - FPS: {config.target_fps}")
        logger.info(f"  - Title: {config.title}")
        logger.info(f"  - Data dir: {config.data_dir}")
        return True
    except FileNotFoundError as e:
        logger.error(f"✗ Config file not found: {e}")
        return False
    except ValueError as e:
        logger.error(f"✗ Invalid TOML: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error loading config: {e}")
        return False


def validate_data() -> bool:
    """Valideer alle JSON data bestanden.

    Returns
    -------
    bool
        True als alle data OK is
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("Validating JSON Data Files")
    logger.info("=" * 70)

    data_dir = project_root / "data"
    repo = DataRepository(data_dir=data_dir)

    # Load and validate all data
    success = repo.load_and_validate_all()

    if not success:
        logger.error("")
        logger.error("Validation errors found:")
        for error in repo.get_validation_errors():
            logger.error(f"  - {error}")
        return False

    # Print summary
    logger.info("")
    logger.info("Data Summary:")
    try:
        actors = repo.get_all_actors()
        logger.info(f"  - Actors: {len(actors)}")
        for actor in actors:
            actor_id = actor.get('id')
            actor_name = actor.get('name')
            actor_level = actor.get('level')
            logger.info(f"    * {actor_id}: {actor_name} (lvl {actor_level})")

        enemies = repo.get_all_enemies()
        logger.info(f"  - Enemies: {len(enemies)}")
        for enemy in enemies:
            enemy_id = enemy.get('id')
            enemy_name = enemy.get('name')
            enemy_level = enemy.get('level')
            logger.info(f"    * {enemy_id}: {enemy_name} (lvl {enemy_level})")

        zones = repo.get_all_zones()
        logger.info(f"  - Zones: {len(zones)}")
        for zone in zones:
            zone_id = zone.get('id')
            zone_name = zone.get('name')
            zone_type = zone.get('type')
            logger.info(f"    * {zone_id}: {zone_name} ({zone_type})")

        # NPC metadata (Step 4+, optional)
        npcs = repo.get_all_npcs()
        if npcs:
            logger.info(f"  - NPCs: {len(npcs)}")
            for npc in npcs:
                npc_id = npc.get('npc_id')
                actor_id = npc.get('actor_id')
                tier = npc.get('tier')
                is_mc = npc.get('is_main_character', False)
                flags = npc.get('companion_flags', {})
                recruited = flags.get('recruited', False)
                in_party = flags.get('in_party', False)
                status = "MC" if is_mc else ("Party" if in_party else ("Recruited" if recruited else "Not recruited"))
                logger.info(f"    * {npc_id} ({actor_id}): Tier {tier}, {status}")

    except Exception as e:
        logger.error(f"✗ Error reading data summary: {e}")
        return False

    # Additional structural checks for stub files
    stub_specs = {
        "dialogue.json": (dict, "dialogues"),
        "quests.json": (dict, "quests"),
        "shops.json": (dict, "shops"),
        "loot_tables.json": (dict, "loot_tables"),
        "chests.json": (dict, "chests"),
        "npc_schedules.json": (dict, "npc_schedules"),
        "events.json": (dict, "events"),
    }

    for filename, (expected_type, top_key) in stub_specs.items():
        path = data_dir / filename
        try:
            payload = path.read_text(encoding="utf-8")
            data = json.loads(payload)
        except FileNotFoundError:
            logger.error(f"✗ Missing data file: {filename}")
            success = False
            continue
        except json.JSONDecodeError as e:
            logger.error(f"✗ Invalid JSON in {filename}: {e}")
            success = False
            continue

        if not isinstance(data, expected_type):
            logger.error(f"✗ {filename} top-level is not a {expected_type.__name__}")
            success = False
            continue

        if top_key not in data:
            logger.error(f"✗ {filename} missing top-level key '{top_key}'")
            success = False

    return success


def main() -> int:
    """Main entry point.

    Returns
    -------
    int
        Exit code (0 = success, 1 = errors found)
    """
    logger.info("Tri-Sarira RPG - Data Validation Tool")
    logger.info("")

    config_ok = validate_config()
    data_ok = validate_data()

    logger.info("")
    logger.info("=" * 70)
    logger.info("Validation Summary")
    logger.info("=" * 70)
    logger.info(f"Config: {'✓ OK' if config_ok else '✗ FAILED'}")
    logger.info(f"Data:   {'✓ OK' if data_ok else '✗ FAILED'}")
    logger.info("")

    if config_ok and data_ok:
        logger.info("✓ All validation checks passed!")
        return 0
    else:
        logger.error("✗ Validation failed. See errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
