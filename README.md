# Tri-Sarira RPG

A single-player, turn-based 2D RPG built with Python and Pygame, exploring spiritual themes through the **Tri-Sarira** (Body/Mind/Spirit) system. This repository contains the **vertical slice** implementation of Region 1 (Chandrapur and surroundings), demonstrating core gameplay systems and data-driven architecture.

## Current Status

**Milestone:** Vertical Slice (Step 4+)
**Version:** 0.9.0
**Status:** ✅ All core systems implemented with modern architecture patterns

This is **not the full game**, but a comprehensive vertical slice demonstrating:
- Complete turn-based combat with skills, items, and equipment
- Overworld exploration with multiple zones and portals
- Party management with equipment slots and stat bonuses
- Quest and dialogue systems with branching narratives
- Economy with shops, buy/sell, and currency (Rupa)
- Save/load with multiple slots and full state persistence
- Protocol-based architecture with dependency injection
- Data validation and comprehensive test suite (100+ tests)

## Implemented Features

### ✅ Core Gameplay
- **Overworld System** - Tile-based 2D movement with Tiled map integration, portals, and zone transitions
- **Combat System** - Turn-based tactical battles with:
  - Action types: Attack, Skill, Defend, Item
  - Resource management (Stamina, Focus, Prana)
  - XP rewards and multi-level progression
  - Victory/defeat handling with ViewModels for UI decoupling
- **Party System** - Recruit companions (max 2: MC + 1), active/reserve pool management
- **NPC System** - Character recruitment with tier-based phases

### ✅ Progression & Stats
- **Tri-Sarira System** - Body/Mind/Spirit attributes affecting combat and growth
- **Leveling** - XP curves (Lv 1-10), stat growth based on character profiles
- **Skills** - 8+ skills across Physical/Mental/Spiritual domains
- **Items & Inventory** - Consumables (healing herbs, tonics) with usage tracking
- **Equipment System** - Gear slots (weapon, armor, accessory) with stat bonuses

### ✅ Content Systems
- **Quest System** - Multi-stage quests with objectives, rewards, and dialogue integration
- **Dialogue System** - Branching conversations with:
  - Condition checking (flags, party composition)
  - Effects (set flags, give items, advance quests)
  - Auto-advance nodes
- **Shop System** - Full buy/sell shops with:
  - Currency management (Rupa)
  - Chapter-based item availability
  - Integrated shop UI overlay with equipment support

### ✅ Infrastructure
- **Save/Load** - Multiple save slots with persistent state:
  - Party state (levels, XP, stats)
  - World state (zone, position, triggered events)
  - Inventory and economy
  - Quest progress and flags
- **Time System** - Calendar with day/night cycles and time tracking
- **Data Validation** - JSON Schema validation for all data files

## Tech Stack

- **Language:** Python 3.12+ (minimum 3.11)
- **Runtime:** CPython
- **Engine:** Pygame 2.6.1
- **Data Format:** JSON (game data), Tiled TMX (maps)
- **Testing:** pytest, ruff, mypy, black

### Architecture

```
src/tri_sarira_rpg/
├── app/              # Game loop, main entry point
├── core/             # Protocols, scene management, config, entities
│   └── protocols.py  # Protocol-based interfaces for all systems (DI)
├── systems/          # Game logic (Combat, Party, Quest, Shop, Equipment, etc.)
│   └── *_viewmodels.py  # Immutable viewmodels for UI
├── services/         # Facades/services (GameDataService)
├── presentation/     # Scenes (Overworld, Battle, Menus) + UI widgets
│   └── theme.py      # UI theming (Colors, Fonts, ThemeProvider)
├── data_access/      # Data loading (Loader, Repository, Cache)
└── utils/            # Helpers (Tiled loader, math, formatting)

data/                 # JSON game data (actors, enemies, items, quests, etc.)
maps/                 # Tiled TMX map files
schema/               # JSON Schema validation files
tests/                # pytest test suite
```

**Design Principles:**
- **Data-driven**: All game content (actors, enemies, items, skills, quests, dialogue, shops, zones) defined in JSON
- **Protocol-based DI**: Systems communicate via Protocols (`core/protocols.py`), not concrete classes - enables loose coupling and easy testing
- **Scene-based**: SceneStackManager (via `SceneManagerProtocol`) coordinates transitions with stack-based navigation (push/pop/switch)
- **ViewModel pattern**: Systems provide immutable viewmodels (`combat_viewmodels.py`, `dialogue_viewmodels.py`) to the UI layer
- **Services layer**: `GameDataService` acts as facade between presentation and data_access with typed view models
- **System separation**: Core game logic in `systems/`, rendering in `presentation/`, data access in `data_access/`
- **Type-safe**: Extensive use of type hints, dataclasses, and frozen immutable structures

## Getting Started

### Prerequisites

- **Git**
- **Python 3.12** (or 3.11+) with venv support
- **Linux/WSL**: SDL2 development libraries (required for Pygame)
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-dev libsdl2-dev libsdl2-image-dev \
                       libsdl2-mixer-dev libsdl2-ttf-dev
  ```

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rpg-game
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Install core package
   pip install -e .

   # Install development dependencies
   pip install -e .[dev]
   ```

4. **Verify installation**
   ```bash
   python -m tri_sarira_rpg.app.main
   ```

### Running the Game

```bash
python -m tri_sarira_rpg.app.main
```

**In-game controls:**
- **WASD / Arrow Keys** - Move player
- **Space / E / Enter** - Interact
- **F5** - Quick save (slot 1)
- **F9** - Quick load (slot 1)
- **Q** - Toggle quest log
- **Esc** - Pause menu
- **G** - Open shop (debug, only in Chandrapur)

See `docs/architecture/5.5 Run- & Build-instructies - Tri-Sarira RPG.md` for detailed instructions and troubleshooting.

## Testing & Validation

### Run all tests
```bash
pytest
# or
python -m pytest tests/ -v
```

### Run data validation
```bash
python -m tools.validate_data
```

The data validation tool:
- Validates JSON files against schemas
- Checks reference integrity (actor IDs, item IDs, zone IDs, etc.)
- Verifies TOML configuration
- Serves as a pre-flight check before running the game

**Test coverage:**
- 100+ unit tests (combat, party, quests, dialogue, shops, equipment, save/load, data validation)
- All tests passing ✅

## Data & Content

All gameplay content is defined in JSON files under `data/`:

| File | Description |
|------|-------------|
| `actors.json` | Playable characters (Adhira, Rajani) |
| `enemies.json` | Enemy definitions (stats, skills, loot) |
| `items.json` | Items (consumables, gear, quest items) |
| `equipment.json` | Equipment definitions (weapons, armor, accessories) |
| `skills.json` | Combat skills (Physical/Mental/Spiritual) |
| `quests.json` | Quest definitions (stages, objectives, rewards) |
| `dialogue.json` | Branching dialogue trees |
| `shops.json` | Shop inventories and prices |
| `zones.json` | Zone metadata (encounter rates, type) |
| `npc_meta.json` | NPC metadata (tiers, phases) |
| `loot_tables.json` | Loot drop definitions |
| `chests.json` | Treasure chest contents |

Maps are created in **Tiled** (`.tmx` format) under `maps/`. See `docs/architecture/4.3 Tiled Conventions & Map Metadata Spec - Tri-Sarira RPG.md` for mapping conventions.

For detailed data schemas, see `docs/architecture/4.1 JSON-schemas - Overzicht per type.md`.

## Developer Notes

### Coding Guidelines

- **PEP 8** compliance with 100-character line limit
- **black** for code formatting
- **ruff** for linting
- **mypy** for type checking (especially in `core/`, `systems/`, `data_access/`)
- **NumPy-style docstrings** for public APIs

### Architecture Principles

**Separation of Concerns:**
- `systems/` - Pure game logic (no Pygame dependencies), implements SystemProtocols
- `presentation/` - Scenes and UI (Pygame rendering and input), consumes ViewModels
- `services/` - Facades between presentation and data_access
- `data_access/` - Data loading and caching
- `core/` - Protocols, scene management, shared infrastructure

**Key Patterns:**
- **Protocol-based DI**: All systems implement Protocols from `core/protocols.py`
- **ViewModels**: UI receives immutable snapshots (`CombatantView`, `DialogueView`, etc.)
- **Theme System**: Centralized UI styling via `ThemeProviderProtocol` and `UITheme`
- **Scene Stack**: `SceneStackManager` enables push/pop navigation with overlays

**Adding a New Feature:**
1. Create a feature branch from `main`
2. Define Protocol interface in `core/protocols.py` if adding a new system
3. Implement system in `systems/`, add viewmodels if UI needs data
4. Keep code consistent with existing architecture (data-driven, scene-based)
5. Add/update tests in `tests/`
6. If adding/changing JSON data, run `python -m tools.validate_data`
7. Format code with `black`, lint with `ruff`
8. Open a pull request or merge via your workflow

### Documentation

Key architecture docs in `docs/architecture/`:
- **1.1 Game Overview - Vision One-Pager** - Game vision and themes
- **5.1 Tech Overview** - Technical stack and design
- **5.3 Folder- & Module-structuur** - Code organization
- **5.4 Coding Guidelines** - Style and best practices
- **3.1 Combat & Stats Spec** - Combat system design
- **3.4 Quests & Dialogue System Spec** - Quest and dialogue mechanics
- **3.6 Items, Gear & Economy Spec** - Items and economy design
- **3.8 Save & Trilogy Continuity Spec** - Save system design

## Roadmap

**Recently Completed:**
- ✅ **Equipment System** - Gear slots (weapon, armor, accessory), stat bonuses, equip/unequip
- ✅ **Protocol-based Architecture** - Full DI with SystemProtocols
- ✅ **ViewModels** - Immutable UI data for combat and dialogue
- ✅ **Theme System** - Centralized UI styling with ThemeProvider

**Planned / Future Work:**
- ⏳ **Enhanced UI/UX** - Polish menus, add animations, improve accessibility
- ⏳ **Expanded R1 Content** - More quests, encounters, NPCs, and areas
- ⏳ **Post-game & NG+** - End-game content, New Game Plus with carryover
- ⏳ **Multi-enemy Battles** - Support for 2v2, 2v3 combat formations
- ⏳ **Audio Integration** - BGM and SFX with zone-based music

See `docs/architecture/1.3 Feature Roadmap & Milestones - Tri-Sarira RPG.md` for the full development roadmap.

## Project Structure

```
tri-sarira-rpg/
├── src/
│   └── tri_sarira_rpg/
│       ├── app/              # Game initialization and main loop
│       ├── core/             # Protocols, scenes, config, resources
│       ├── systems/          # Game logic systems + viewmodels
│       ├── services/         # Facades (GameDataService)
│       ├── presentation/     # Scenes, UI components, theme
│       ├── data_access/      # Data loading and caching
│       └── utils/            # Utility functions
├── data/                     # JSON game data
├── maps/                     # Tiled TMX map files
├── schema/                   # JSON Schema validation
├── assets/                   # Graphics and audio (future)
├── config/                   # TOML configuration files
├── docs/                     # Architecture documentation
├── tests/                    # pytest test suite
├── tools/                    # Development tools (validation, etc.)
└── pyproject.toml           # Project metadata and dependencies
```

## License

MIT

---

**Ready to explore Chandrapur?** Start the game and press F1 for help, or check out the Run & Build Instructions to dive deeper.
