# Step 3: World & Overworld - Implementation Review

**Date**: 2025-11-15
**Branch**: `feature/f4-world-overworld`
**Scope**: Tiled map loading, WorldSystem, TimeSystem, OverworldScene
**Status**: ✅ Complete

---

## 1. Overview

Step 3 implements the overworld experience for Tri-Śarīra RPG, including:
- Tiled map loading (.tmx files)
- Zone management with collision detection
- Portal system for zone transitions
- Event triggers and chests (skeleton implementation)
- Player movement and camera system
- Day/night time cycle

The game now starts directly in the overworld (Chandrapur Town) where the player can move around, explore multiple zones, and experience the time system.

---

## 2. New Modules & Classes

### 2.1 `src/tri_sarira_rpg/utils/tiled_loader.py` (NEW)

**Purpose**: Parse Tiled Map Editor .tmx files according to spec 4.3 Tiled Conventions.

**Key Classes**:
- `TileLayer`: Represents a tile layer with 2D grid data
- `ObjectLayer`: Represents an object group with Tiled objects
- `TiledObject`: Represents a single object (spawn, portal, chest, event)
- `TiledMap`: Complete map data structure with layers and properties
- `TiledLoader`: Loads and parses TMX files from the maps directory

**Features**:
- XML parsing with `xml.etree.ElementTree`
- CSV-encoded tile data support
- Custom property parsing with type conversion (int, float, bool, string)
- Helper methods to query spawns, portals, chests, events
- Collision detection via Collision layer

**Example Usage**:
```python
loader = TiledLoader(maps_dir=Path("maps"))
tiled_map = loader.load_map("z_r1_chandrapur_town")

# Query objects
spawns = tiled_map.get_spawns()
portals = tiled_map.get_portals()
chests = tiled_map.get_chests()

# Check collision
is_blocked = tiled_map.get_collision_at(tile_x=5, tile_y=10)
```

---

### 2.2 `src/tri_sarira_rpg/systems/world.py` (MODIFIED)

**Purpose**: Manage zones, player state, collision, portals, and triggers.

**Key Classes**:
- `PlayerState`: Current zone, position, facing direction
- `Trigger`: Event trigger with type (ON_ENTER, ON_INTERACT, ON_STEP)
- `WorldSystem`: Main system managing the game world

**Features**:
- Zone loading from JSON data + TMX files
- Player spawning at spawn points
- Tile-based collision detection
- Portal transitions between zones
- Trigger system for chests and events
- Once-per-save trigger tracking

**Flow**:
1. `load_zone(zone_id, spawn_id)` - Load zone data, TMX map, place player
2. `move_player(dx, dy)` - Move player, check collision, check triggers/portals
3. `interact()` - Trigger ON_INTERACT events at player position or in front
4. Portal transitions happen automatically when stepping on portal tile

**Example Portal Flow**:
```
Player in Chandrapur Town (12, 19) steps south
→ Lands on portal tile
→ Portal has target_zone_id="z_r1_forest_route", target_spawn_id="spawn_from_town"
→ WorldSystem loads z_r1_forest_route
→ Player spawns at spawn_from_town (10, 2)
```

---

### 2.3 `src/tri_sarira_rpg/systems/time.py` (MODIFIED)

**Purpose**: Manage day/night cycle and in-game time.

**Key Classes**:
- `TimeBand(Enum)`: DAWN, DAY, DUSK, NIGHT
- `TimeState`: Current time (day, time_of_day in minutes, season, year)
- `TimeSystem`: Time advancement and time band tracking

**Features**:
- Time in minutes since midnight (0-1439)
- Day rollover at 1440 minutes
- Time band calculation based on time ranges
- Logging when switching time bands
- Time advances on player steps and automatically (for atmosphere)

**Time Bands**:
- DAWN: 5:00-7:00 (300-420 minutes)
- DAY: 7:00-17:00 (420-1020 minutes)
- DUSK: 17:00-19:00 (1020-1140 minutes)
- NIGHT: 19:00-5:00 (1140-300 minutes, wraps around)

**Example**:
```python
time_system.on_player_step()  # Advance 1 minute
time_system.advance_time(60)   # Advance 1 hour

display = time_system.get_time_display()
# "Day 1, 07:00 (DAY)"
```

---

### 2.4 `src/tri_sarira_rpg/presentation/overworld.py` (MODIFIED)

**Purpose**: Overworld scene with rendering and player control.

**Features**:
- Placeholder tile rendering (green=walkable, gray=blocked)
- Portal rendering (yellow outlines)
- Chest rendering (brown rectangles)
- Player rendering (blue circle with direction indicator)
- Camera system that follows player with bounds clamping
- Movement with WASD/Arrow keys
- Interaction with Space/E/Enter
- Movement cooldown to prevent instant movement
- HUD showing zone name, time, position, controls

**Rendering Strategy**:
- No actual tilesets used (placeholder colors for testing)
- Renders only visible tiles within camera view
- Camera centered on player, clamped to map bounds
- Player drawn as blue circle with white dot showing facing direction

**Controls**:
- **WASD / Arrow keys**: Move player
- **Space / E / Enter**: Interact (activate triggers in front of player)
- **ESC**: Quit (not implemented yet)

---

### 2.5 `src/tri_sarira_rpg/app/game.py` (MODIFIED)

**Changes**:
- Initialize `WorldSystem` and `TimeSystem` in `__init__`
- Load starting zone `z_r1_chandrapur_town` on startup
- Create `OverworldScene` instead of `TitleScene`
- Push `OverworldScene` to scene manager
- Path detection for `maps_dir` and `data_dir`

---

## 3. Tiled Maps

Three test maps were created in the `maps/` directory:

### 3.1 `z_r1_chandrapur_town.tmx`
- **Type**: TOWN
- **Size**: 25x20 tiles
- **Features**:
  - 2 spawns: spawn_default (12, 9), spawn_from_route (12, 19)
  - 1 portal: portal_to_route → z_r1_forest_route
  - Collision: walls around perimeter, 2 buildings in grid pattern
- **Purpose**: Safe starting zone

### 3.2 `z_r1_forest_route.tmx`
- **Type**: ROUTE
- **Size**: 20x30 tiles
- **Features**:
  - 2 spawns: spawn_from_town (10, 2), spawn_from_shrine (10, 28)
  - 2 portals: to town and to shrine
  - 1 chest: ch_route_01 (4, 10)
  - Collision: winding path through trees
- **Purpose**: Route between town and shrine, has random encounters enabled

### 3.3 `z_r1_shrine_clearing.tmx`
- **Type**: DUNGEON
- **Size**: 18x15 tiles
- **Features**:
  - 1 spawn: spawn_from_route (9, 2)
  - 1 portal: portal_to_route → z_r1_forest_route
  - 1 event: ev_shrine_guardian (9, 11) - ON_ENTER trigger
  - Collision: circular clearing pattern
- **Purpose**: Boss/shrine area

**Map Structure**:
```
Chandrapur Town
    ↓ portal_to_route
Forest Route
    ↓ portal_to_shrine
Shrine Clearing
```

---

## 4. How Tiled Maps Are Loaded

### 4.1 TMX File Structure

```xml
<map version="1.10" orientation="orthogonal" width="25" height="20" tilewidth="32" tileheight="32">
  <properties>
    <property name="zone_id" value="z_r1_chandrapur_town"/>
    <property name="zone_type" value="TOWN"/>
    <property name="recommended_level" type="int" value="1"/>
    <property name="allow_random_encounters" type="bool" value="false"/>
  </properties>

  <layer id="1" name="Ground" width="25" height="20">
    <data encoding="csv">
      0,0,0,0,0,...
    </data>
  </layer>

  <layer id="2" name="Collision" width="25" height="20">
    <data encoding="csv">
      1,1,1,1,1,...
    </data>
  </layer>

  <objectgroup id="3" name="Spawns">
    <object id="1" name="spawn_default" type="PlayerSpawn" x="384" y="288" width="32" height="32">
      <properties>
        <property name="spawn_id" value="spawn_default"/>
        <property name="is_default" type="bool" value="true"/>
      </properties>
    </object>
  </objectgroup>

  <objectgroup id="4" name="Portals">
    <object id="2" name="portal_to_route" type="Portal" x="384" y="608" width="32" height="32">
      <properties>
        <property name="target_zone_id" value="z_r1_forest_route"/>
        <property name="target_spawn_id" value="spawn_from_town"/>
      </properties>
    </object>
  </objectgroup>
</map>
```

### 4.2 Loading Process

1. **WorldSystem.load_zone(zone_id, spawn_id)**
   - Load zone data from `data/zones.json` via DataRepository
   - Load TMX file from `maps/{zone_id}.tmx` via TiledLoader
   - If TMX not found, create placeholder map

2. **TiledLoader.load_map(zone_id)**
   - Parse XML file with ElementTree
   - Extract map properties (zone_id, zone_type, etc.)
   - Parse tile layers: convert CSV data to 2D array
   - Parse object layers: extract spawns, portals, chests, events
   - Return TiledMap dataclass

3. **Player Spawning**
   - Find spawn by spawn_id or default spawn or map center
   - Convert pixel coordinates to tile coordinates
   - Set player position

4. **Trigger Setup**
   - Extract chests (ON_INTERACT triggers)
   - Extract events (ON_ENTER, ON_INTERACT, ON_STEP triggers)
   - Store in WorldSystem._triggers dict

---

## 5. How Portals Work

### 5.1 Portal Object Structure

```python
TiledObject(
    id=3,
    name="portal_to_route",
    type="Portal",
    x=384,    # Pixel coordinates
    y=608,
    width=32,
    height=32,
    properties={
        "target_zone_id": "z_r1_forest_route",
        "target_spawn_id": "spawn_from_town"
    }
)
```

### 5.2 Portal Transition Flow

1. Player moves with `WorldSystem.move_player(dx, dy)`
2. Check collision - if blocked, return False
3. Update player position
4. Call `_check_portal_transition()`
5. Check if current tile has a portal:
   ```python
   for portal in self._current_map.get_portals():
       tile_x, tile_y = portal.get_tile_coords()
       if (tile_x, tile_y) == (player.position.x, player.position.y):
           # Portal found!
   ```
6. Extract target_zone_id and target_spawn_id from portal properties
7. Log transition: `Portal transition: current_zone → target_zone`
8. Call `load_zone(target_zone_id, target_spawn_id)` recursively
9. Player now in new zone at target spawn point

**Example Log Output**:
```
[INFO] WorldSystem: Portal transition: z_r1_chandrapur_town → z_r1_forest_route
[INFO] WorldSystem: Loading zone: z_r1_forest_route (spawn: spawn_from_town)
[INFO] TiledLoader: Loading Tiled map: /path/to/maps/z_r1_forest_route.tmx
[INFO] WorldSystem: Player spawned at (10, 2)
[INFO] WorldSystem: ✓ Zone loaded: z_r1_forest_route
```

---

## 6. How Triggers Work

### 6.1 Trigger Types

According to spec 3.2, there are three trigger types:
- **ON_ENTER**: Activated when player steps on trigger tile
- **ON_STEP**: Activated every time player is on trigger tile
- **ON_INTERACT**: Activated when player presses interact key while on/facing trigger

### 6.2 Trigger Object Examples

**Chest** (always ON_INTERACT):
```xml
<object id="5" name="ch_route_01" type="Chest" x="128" y="320" width="32" height="32">
  <properties>
    <property name="chest_id" value="ch_route_01"/>
  </properties>
</object>
```

**Event Trigger** (configurable):
```xml
<object id="3" name="ev_shrine_guardian" type="EventTrigger" x="288" y="352" width="32" height="32">
  <properties>
    <property name="event_id" value="ev_shrine_guardian_encounter"/>
    <property name="trigger_type" value="ON_ENTER"/>
    <property name="once_per_save" type="bool" value="true"/>
  </properties>
</object>
```

### 6.3 Trigger Activation Flow

**For ON_ENTER and ON_STEP**:
1. Player moves to new tile
2. WorldSystem checks all triggers at new position
3. For each trigger:
   - If ON_ENTER and already triggered, skip
   - If trigger.active, call `_trigger_event(trigger)`
   - Log activation
   - If once_per_save, mark as used

**For ON_INTERACT**:
1. Player presses Space/E/Enter
2. OverworldScene calls `WorldSystem.interact()`
3. Check player position and tile in front of player (based on facing)
4. Find ON_INTERACT triggers at those positions
5. Activate first found trigger

### 6.4 Trigger Implementation

```python
@dataclass
class Trigger:
    trigger_id: str
    trigger_type: str  # "ON_ENTER", "ON_INTERACT", "ON_STEP"
    position: Position
    event_id: str | None = None
    once_per_save: bool = True
    active: bool = True

def _trigger_event(self, trigger: Trigger) -> None:
    logger.info(f"🎯 Triggered: {trigger.trigger_id} ({trigger.trigger_type})")

    if trigger.event_id:
        logger.info(f"   Event: {trigger.event_id}")

    # Mark as used if once_per_save
    if trigger.once_per_save:
        self._triggered_ids.add(trigger.trigger_id)
        trigger.active = False
```

---

## 7. How TimeSystem Works

### 7.1 Time Advancement

Time advances in two ways:

**1. Automatic (for atmosphere)**:
```python
def update(self, dt: float) -> None:
    minutes_to_add = self._minutes_per_tick * (dt * 60)
    self.advance_time(int(minutes_to_add))
```
- Called every frame in game loop
- Advances time slowly for visual feedback
- Config: `_minutes_per_tick = 0.5` (tunable)

**2. On player steps**:
```python
def on_player_step(self) -> None:
    self.advance_time(self._minutes_per_step)
```
- Called when player moves
- Config: `_minutes_per_step = 1` (tunable)

### 7.2 Day Rollover

```python
def advance_time(self, minutes: int) -> None:
    self._state.time_of_day += minutes

    # Check for day rollover
    while self._state.time_of_day >= 1440:  # 24 hours
        self._state.time_of_day -= 1440
        self._state.day_index += 1
        logger.info(f"New day: Day {self._state.day_index + 1}")
```

### 7.3 Time Band Tracking

```python
def get_time_band(self) -> TimeBand:
    if 300 <= self.time_of_day < 420:    # 5:00-7:00
        return TimeBand.DAWN
    elif 420 <= self.time_of_day < 1020:  # 7:00-17:00
        return TimeBand.DAY
    elif 1020 <= self.time_of_day < 1140: # 17:00-19:00
        return TimeBand.DUSK
    else:                                  # 19:00-5:00
        return TimeBand.NIGHT
```

When time band changes, log it:
```
[INFO] TimeSystem: switched to DUSK (time: 17:00)
```

### 7.4 Time Display

```python
def get_time_display(self) -> str:
    return (
        f"Day {self._state.day_index + 1}, "
        f"{self._state.format_time()} ({self.time_band.value})"
    )
```

Output: `"Day 1, 07:00 (DAY)"`

---

## 8. Testing Commands

### 8.1 Install & Validate

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run type checking
mypy src/tri_sarira_rpg

# Run linting
ruff check src/tri_sarira_rpg

# Run formatting check
ruff format --check src/tri_sarira_rpg
```

### 8.2 Run the Game

```bash
# Start game directly in overworld
python -m tri_sarira_rpg.app.main
```

**Expected Behavior**:
- Window opens with Chandrapur Town map
- Player visible as blue circle in center
- Can move with WASD/Arrow keys
- Cannot walk through gray (blocked) tiles
- Walking onto yellow portal (bottom of town) transitions to Forest Route
- Time displayed in HUD: "Day 1, 07:00 (DAY)"
- Console shows zone loading and time changes

### 8.3 Test Checklist

- ✅ Game starts without errors
- ✅ Chandrapur Town loads from TMX file
- ✅ Player spawns at correct position (12, 9)
- ✅ Player can move with WASD/Arrows
- ✅ Collision works (cannot walk through walls)
- ✅ Portal to Forest Route works
- ✅ Zone transitions logged to console
- ✅ TimeSystem runs and displays time
- ✅ HUD shows zone name, time, position, controls

### 8.4 Portal Navigation Test

```
1. Start in Chandrapur Town
2. Move south to portal (12, 19)
3. → Should transition to Forest Route, spawn at (10, 2)
4. Move south through winding path
5. → Should find chest at (4, 10) - interact to trigger
6. Continue south to shrine portal (10, 29)
7. → Should transition to Shrine Clearing, spawn at (9, 2)
8. Move south to event trigger (9, 11)
9. → Should log "ev_shrine_guardian_encounter"
10. Move north to portal (9, 1)
11. → Should transition back to Forest Route
```

---

## 9. Known Limitations & Future Work

### 9.1 Current Limitations

**No actual graphics**:
- Placeholder colored rectangles for tiles
- No tileset rendering
- No sprite animations

**Minimal UI**:
- Basic HUD only
- No menus, inventory, dialogue

**Time system simplifications**:
- Time advances automatically (not ideal for turn-based)
- No time-based events yet
- No seasonal changes implemented

**Trigger system**:
- Only logging, no actual event execution
- No quest integration
- No dialogue or cutscenes

### 9.2 Future Enhancements (Out of Scope for Step 3)

**Step 4: Battle System**:
- Combat triggers in routes (random encounters)
- Shrine guardian boss battle

**Step 5: Quests & Dialogue**:
- Event triggers execute actual events
- NPC dialogue
- Quest tracking

**Step 6: Items & Inventory**:
- Chest triggers give items
- Inventory UI
- Item usage

**Step 7: Polish & Content**:
- Actual tileset rendering
- Sprite animations
- Sound effects and music
- More zones and content

---

## 10. Architecture Compliance

### 10.1 Follows Spec 3.2 (Time, World & Overworld)

✅ **TimeSystem**:
- TimeBand enum (DAWN, DAY, DUSK, NIGHT)
- TimeState dataclass
- Time advancement on player steps
- Day rollover and logging

✅ **WorldSystem**:
- Zone management
- Collision detection
- Portal transitions
- Event triggers
- PlayerState tracking

✅ **OverworldScene**:
- Rendering with camera
- Player movement
- Interaction system
- HUD display

### 10.2 Follows Spec 4.3 (Tiled Conventions)

✅ **Map Properties**:
- zone_id, region_id, zone_type
- recommended_level
- allow_random_encounters

✅ **Tile Layers**:
- Ground layer
- Collision layer (1=blocked, 0=walkable)

✅ **Object Layers**:
- Spawns (PlayerSpawn objects with spawn_id, is_default)
- Portals (Portal objects with target_zone_id, target_spawn_id)
- Chests (Chest objects with chest_id)
- Events (EventTrigger objects with event_id, trigger_type, once_per_save)

✅ **CSV Encoding**:
- Tile data encoded as CSV
- Parsed correctly into 2D arrays

---

## 11. Summary

Step 3 successfully implements the core overworld experience:

**What Works**:
- ✅ Tiled map loading from .tmx files
- ✅ Zone management with JSON data + TMX maps
- ✅ Player movement with collision detection
- ✅ Portal transitions between 3 zones
- ✅ Event triggers (logging only)
- ✅ Day/night time cycle
- ✅ Camera system following player
- ✅ Basic HUD with zone/time info

**What's Missing** (intentionally out of scope):
- ❌ Combat system
- ❌ Dialogue and quests
- ❌ Inventory and items
- ❌ Actual tileset graphics
- ❌ Save/load system
- ❌ Menus and UI

**Next Steps**:
- Branch: Push to `claude/f4-world-overworld-01L7zbTT5gLxNKbsnXfKvHJN`
- User will merge into `feature/f4-world-overworld`
- Future: Implement Step 4 (Battle System)

---

**Reviewer**: Claude (Sonnet 4.5)
**Date**: 2025-11-15
**Status**: ✅ Ready for merge
