# Portal & Spawn Facing System

## Overview

This document describes the elegant system for automatically orienting the player character when entering a new map through portals.

## Design Principle

**Spawn at map edge → face INTO the map**

When a player enters a map through a portal, they should face the direction that makes sense for continuing into the map, not the direction they came from.

## Implementation

### Map Data Property

Each `PlayerSpawn` object in Tiled maps has a `spawn_facing` property with one of four values:
- `north` - Player faces up
- `south` - Player faces down
- `east` - Player faces right
- `west` - Player faces left

### Example

```xml
<object id="1" name="spawn_from_clearing" type="PlayerSpawn" x="384" y="576">
  <properties>
    <property name="spawn_id" value="spawn_from_clearing"/>
    <property name="is_default" type="bool" value="true"/>
    <property name="spawn_facing" value="north"/>
  </properties>
</object>
```

### Logic

When a player teleports to a spawn point:
1. Load the target zone/map
2. Find the spawn point by `spawn_id`
3. Read the `spawn_facing` property
4. Set player orientation to that direction

If `spawn_facing` is missing, use a sensible default (e.g., `south`).

**Direction Mapping (Top-Down View):**
- `north` = Face down/bottom of screen (toward higher Y values)
- `south` = Face up/top of screen (toward lower Y values)
- `east` = Face right
- `west` = Face left

## Current Map Configuration

| Map | Spawn Point | Facing | Reason |
|-----|-------------|--------|--------|
| **chandrapur_town** | spawn_default | south | Default center, face upward |
| | spawn_from_route | south | At bottom edge, face up into town |
| **forest_route** | spawn_from_town | north | At top edge, face down the path |
| | spawn_from_shrine | south | At bottom edge, face up the path |
| **shrine_clearing** | spawn_from_route | north | At top edge, face down into clearing |
| | spawn_from_inner | south | At bottom edge, face up toward route |
| **shrine_inner** | spawn_from_clearing | south | At bottom edge, face up into dungeon |

## Benefits

✅ **Declarative** - Defined in map data, not code
✅ **Flexible** - Each spawn can have different facing
✅ **Intuitive** - Player faces the direction they'd naturally move
✅ **Maintainable** - Easy to adjust per spawn without code changes
✅ **No hardcoding** - System works for any new maps automatically

## Future Extensions

This system can be extended with:
- Auto-calculation based on walkable tiles (face the most open direction)
- Animation transitions (turn smoothly when spawning)
- Camera orientation sync (camera follows facing direction)
