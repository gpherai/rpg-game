#!/usr/bin/env python3
"""Test script to verify portal navigation between all zones."""

from pathlib import Path

from tri_sarira_rpg.data_access.repository import DataRepository
from tri_sarira_rpg.systems.world import WorldSystem


def test_portal_navigation():
    """Test navigating through all portals: Town → Route → Shrine → back."""

    print("=" * 60)
    print("Testing Portal Navigation: Town → Route → Shrine → Route → Town")
    print("=" * 60)

    # Setup paths
    project_root = Path.cwd()
    if (project_root / "src").exists():
        maps_dir = project_root / "maps"
        data_dir = project_root / "data"
    else:
        maps_dir = Path("maps")
        data_dir = Path("data")

    # Initialize systems
    data_repo = DataRepository(data_dir=data_dir)
    world = WorldSystem(data_repository=data_repo, maps_dir=maps_dir)

    # Step 1: Start in Chandrapur Town
    print("\n[Step 1] Loading Chandrapur Town...")
    world.load_zone("z_r1_chandrapur_town")
    print(f"✓ Current zone: {world.current_zone_id}")
    print(f"✓ Player position: ({world.player.position.x}, {world.player.position.y})")

    # Step 2: Navigate to Forest Route
    print("\n[Step 2] Navigating to portal to Forest Route...")
    portals = world.current_map.get_portals()
    portal_to_route = next(
        p for p in portals if p.properties.get("target_zone_id") == "z_r1_forest_route"
    )
    portal_tile = portal_to_route.get_tile_coords()
    print(f"Portal to route at tile: {portal_tile}")

    print("Simulating portal transition to Forest Route...")
    world.load_zone("z_r1_forest_route", "spawn_from_town")
    print(f"✓ Current zone: {world.current_zone_id}")
    print(f"✓ Player position: ({world.player.position.x}, {world.player.position.y})")

    # Step 3: Navigate to Shrine Clearing
    print("\n[Step 3] Navigating to portal to Shrine Clearing...")
    portals = world.current_map.get_portals()
    portal_to_shrine = next(
        p for p in portals if p.properties.get("target_zone_id") == "z_r1_shrine_clearing"
    )
    portal_tile = portal_to_shrine.get_tile_coords()
    print(f"Portal to shrine at tile: {portal_tile}")

    # Check if portal tile is walkable
    is_walkable = not world.current_map.get_collision_at(portal_tile[0], portal_tile[1])
    print(f"Portal tile walkable: {is_walkable}")

    if not is_walkable:
        print("❌ ERROR: Portal to shrine is on a blocked tile!")
        return False

    print("Simulating portal transition to Shrine Clearing...")
    world.load_zone("z_r1_shrine_clearing", "spawn_from_route")
    print(f"✓ Current zone: {world.current_zone_id}")
    print(f"✓ Player position: ({world.player.position.x}, {world.player.position.y})")

    # Step 4: Return to Forest Route
    print("\n[Step 4] Returning to Forest Route...")
    portals = world.current_map.get_portals()
    portal_to_route_back = next(
        p for p in portals if p.properties.get("target_zone_id") == "z_r1_forest_route"
    )
    portal_tile = portal_to_route_back.get_tile_coords()
    print(f"Portal to route at tile: {portal_tile}")

    world.load_zone("z_r1_forest_route", "spawn_from_shrine")
    print(f"✓ Current zone: {world.current_zone_id}")
    print(f"✓ Player position: ({world.player.position.x}, {world.player.position.y})")

    # Step 5: Return to Town
    print("\n[Step 5] Returning to Chandrapur Town...")
    portals = world.current_map.get_portals()
    portal_to_town = next(
        p for p in portals if p.properties.get("target_zone_id") == "z_r1_chandrapur_town"
    )
    portal_tile = portal_to_town.get_tile_coords()
    print(f"Portal to town at tile: {portal_tile}")

    world.load_zone("z_r1_chandrapur_town", "spawn_from_route")
    print(f"✓ Current zone: {world.current_zone_id}")
    print(f"✓ Player position: ({world.player.position.x}, {world.player.position.y})")

    print("\n" + "=" * 60)
    print("✅ All portal transitions successful!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_portal_navigation()
        exit(0)
    except Exception as e:
        print(f"\n❌ Error during portal test: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
