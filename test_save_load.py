#!/usr/bin/env python3
"""Simple test script for save/load functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tri_sarira_rpg.systems.party import PartySystem, PartyMember
from tri_sarira_rpg.systems.world import WorldSystem, PlayerState
from tri_sarira_rpg.systems.time import TimeSystem
from tri_sarira_rpg.systems.inventory import InventorySystem
from tri_sarira_rpg.systems.state import GameStateFlags
from tri_sarira_rpg.systems.save import SaveSystem
from tri_sarira_rpg.core.entities import Position

print("=" * 60)
print("SAVE/LOAD SYSTEM TEST")
print("=" * 60)

# 1. Create test systems with some state
print("\n1. Creating test systems...")
party = PartySystem()
time_sys = TimeSystem()
inventory = InventorySystem()
flags = GameStateFlags()

# Clear the auto-added MC and add our test MC
print("   Clearing default party and adding test MC...")
party._state.active_party.clear()
party._state.active_party.append(
    PartyMember(
        npc_id="npc_mc_adhira",
        actor_id="mc_adhira",
        is_main_character=True,
        level=5,
        xp=123,
        base_stats={"STR": 10, "END": 8, "FOC": 6},
    )
)

# Add some items
print("   Adding items to inventory...")
inventory.add_item("item_small_herb", 3)
inventory.add_item("item_stamina_tonic", 2)

# Set some time
print("   Setting time...")
time_sys._state.day_index = 7
time_sys._state.time_of_day = 540  # 9:00 AM

# Set some flags
print("   Setting story flags...")
flags.set_flag("intro_complete")
flags.set_flag("met_rajani")
flags.record_choice("first_choice", "helped_npc")

print("   ✓ Test data created")

# 2. Create save system and save
print("\n2. Creating save...")
save_sys = SaveSystem(
    party_system=party,
    time_system=time_sys,
    inventory_system=inventory,
    flags_system=flags,
)

save_data = save_sys.build_save(play_time=3600.0)  # 1 hour played
success = save_sys.save_to_file(slot_id=99, save_data=save_data)  # Use slot 99 for test

if not success:
    print("   ✗ FAILED to save!")
    sys.exit(1)

print("   ✓ Save created successfully")

# 3. Create new systems (simulating fresh start)
print("\n3. Creating fresh systems (simulating game restart)...")
party2 = PartySystem()
time_sys2 = TimeSystem()
inventory2 = InventorySystem()
flags2 = GameStateFlags()

print("   ✓ Fresh systems created (empty)")

# 4. Load save
print("\n4. Loading save...")
save_sys2 = SaveSystem(
    party_system=party2,
    time_system=time_sys2,
    inventory_system=inventory2,
    flags_system=flags2,
)

loaded_data = save_sys2.load_from_file(slot_id=99)
if not loaded_data:
    print("   ✗ FAILED to load save file!")
    sys.exit(1)

success = save_sys2.load_save(loaded_data)
if not success:
    print("   ✗ FAILED to restore game state!")
    sys.exit(1)

print("   ✓ Save loaded successfully")

# 5. Verify data
print("\n5. Verifying loaded data...")

errors = []

# Check party
if len(party2._state.active_party) != 1:
    errors.append(f"Party count mismatch: expected 1, got {len(party2._state.active_party)}")
else:
    mc = party2._state.active_party[0]
    if mc.level != 5:
        errors.append(f"MC level mismatch: expected 5, got {mc.level}")
    if mc.xp != 123:
        errors.append(f"MC XP mismatch: expected 123, got {mc.xp}")
    if mc.base_stats.get("STR") != 10:
        errors.append(f"MC STR mismatch: expected 10, got {mc.base_stats.get('STR')}")

# Check inventory
herb_count = inventory2.get_quantity("item_small_herb")
if herb_count != 3:
    errors.append(f"Herb count mismatch: expected 3, got {herb_count}")

tonic_count = inventory2.get_quantity("item_stamina_tonic")
if tonic_count != 2:
    errors.append(f"Tonic count mismatch: expected 2, got {tonic_count}")

# Check time
if time_sys2._state.day_index != 7:
    errors.append(f"Day mismatch: expected 7, got {time_sys2._state.day_index}")

if time_sys2._state.time_of_day != 540:
    errors.append(f"Time mismatch: expected 540, got {time_sys2._state.time_of_day}")

# Check flags
if not flags2.has_flag("intro_complete"):
    errors.append("Flag 'intro_complete' not restored")

if not flags2.has_flag("met_rajani"):
    errors.append("Flag 'met_rajani' not restored")

if flags2._choices.get("first_choice") != "helped_npc":
    errors.append(f"Choice mismatch: expected 'helped_npc', got {flags2._choices.get('first_choice')}")

# Check meta
meta = loaded_data.get("meta", {})
play_time = meta.get("play_time", 0)
if play_time != 3600.0:
    errors.append(f"Play time mismatch: expected 3600.0, got {play_time}")

# 6. Report results
print("\n" + "=" * 60)
if errors:
    print("✗ TEST FAILED - Errors found:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("✓ ALL TESTS PASSED!")
    print("\nVerified:")
    print("  - Party state (MC level, XP, stats)")
    print("  - Inventory state (items and quantities)")
    print("  - Time state (day, time of day)")
    print("  - Game flags and choices")
    print("  - Save metadata (play time)")
    print("\n✓ Save/Load system is working correctly!")

print("=" * 60)

# Cleanup test save
import os
test_save = Path("saves/save_slot_99.json")
if test_save.exists():
    os.remove(test_save)
    print("\n✓ Test save file cleaned up")
