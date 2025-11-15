# ARCHITECTUUR REVIEW: feature/f1-architecture-skeleton

**Review datum:** 2025-11-15
**Reviewer:** Claude (AI Architecture Review)
**Branch:** feature/f1-architecture-skeleton
**Baseline:** docs/architecture/5.2, 5.3, architect_handover.md, 5.4

---

## 1. SAMENVATTING

**Status:** ⚠️ **INCOMPLETE SKELETON**

De branch bevat een **100% complete folder structuur** volgens spec 5.3, maar vrijwel **alle bestanden zijn leeg**. Er zijn slechts 3 core dataclasses geïmplementeerd (76 regels totaal).

**Positief:**
- ✓ Folder structuur 100% compliant met spec 5.3
- ✓ Alle verwachte bestanden bestaan (161 files)
- ✓ Goede .gitignore (runtime artifacts excluded)
- ✓ Geen Pygame dependencies in core modules

**Kritisch:**
- ✗ Alle 23 spec 5.3 critical Python modules zijn leeg (0 bytes)
- ✗ pyproject.toml is leeg (geen dependencies, geen build config)
- ✗ Alle config, data, schema, maps, tools, tests zijn leeg
- ✗ Geen werkende Game class of entrypoint
- ✗ Voldoet NIET aan architect_handover Step 1 criteria

---

## 2. FOLDER STRUCTUUR VALIDATIE (SPEC 5.3)

### ✓ PASS - 100% Compliant

Alle verwachte mappen bestaan:
```
tri_sarira_rpg/
├── src/tri_sarira_rpg/
│   ├── app/           ✓
│   ├── core/          ✓
│   ├── systems/       ✓
│   ├── data_access/   ✓
│   ├── presentation/  ✓
│   └── utils/         ✓
├── data/              ✓
├── schema/            ✓
├── maps/              ✓
├── assets/            ✓ (empty subfolders present)
├── config/            ✓
├── tools/             ✓
├── tests/             ✓
└── scripts/           ✓
```

**Verdict:** Folder structuur is perfect volgens spec 5.3.

---

## 3. BESTANDSSTATUS (SPEC 5.3 VERTICAL SLICE MINIMAL FILES)

### 3.1 SRC Files (23 critical modules)

| File | Exists | Content | Status |
|------|--------|---------|--------|
| src/tri_sarira_rpg/app/game.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/app/main.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/core/config.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/core/scene.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/core/resources.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/core/logging_setup.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/world.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/combat.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/party.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/quests.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/dialogue.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/time.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/items.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/economy.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/progression.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/systems/save.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/data_access/repository.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/data_access/loader.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/presentation/overworld.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/presentation/battle.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/presentation/main_menu.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/presentation/ui/dialogue_box.py | ✓ | ○ | EMPTY |
| src/tri_sarira_rpg/presentation/ui/widgets.py | ✓ | ○ | EMPTY |

**Result:** 23/23 exist, 0/23 have content

### 3.2 Extra Core Files (NOT in spec, but present)

| File | Exists | Content | Lines | Status |
|------|--------|---------|-------|--------|
| src/tri_sarira_rpg/core/entities.py | ✓ | ● | 28 | HAS CODE |
| src/tri_sarira_rpg/core/game_state.py | ✓ | ● | 26 | HAS CODE |
| src/tri_sarira_rpg/core/stat_blocks.py | ✓ | ● | 22 | HAS CODE |

**Result:** 3 extra files with 76 total lines of code

### 3.3 Data/Config/Tools Files

| Category | Files Exist | Files with Content |
|----------|-------------|-------------------|
| data/*.json (12 files) | 12/12 | 0/12 |
| config/*.toml (2 files) | 2/2 | 0/2 |
| maps/*.tmx (5 files) | 5/5 | 0/5 |
| schema/*.schema.json | 12/12 | 0/12 |
| tools/*.py (5 files) | 5/5 | 0/5 |
| tests/*.py (4 files) | 4/4 | 0/4 |

**Result:** All exist, none have content

---

## 4. CODE ARCHITECTUUR VALIDATIE (SPEC 5.2)

### 4.1 entities.py

**Location:** `src/tri_sarira_rpg/core/entities.py`

**Classes:**
- `Entity` - Generic entity with entity_id
- `Position` - 2D tile-space position (x, y)

**Validation:**
```
✓ Generic infrastructure (correct for core/)
✓ No Pygame dependencies
✓ No cross-module dependencies
✓ Follows PEP8/naming conventions
✓ Has type hints
✓ Has docstrings (Dutch)
⚠️ Entity.to_dict() serialization might belong in save system
```

**Verdict:** ✓ ACCEPTABLE (minor note on to_dict placement)

### 4.2 game_state.py

**Location:** `src/tri_sarira_rpg/core/game_state.py`

**Classes:**
- `GameState` - Container for systems and high-level flags

**Methods:**
- `get_system(name: str) -> Any`
- `reset() -> None` (stub)

**Validation:**
```
✓ Generic container (correct for core/)
✓ No Pygame dependencies
✓ No cross-module dependencies
✓ Follows PEP8/naming conventions
✓ Has docstrings (Dutch)
⚠️ Uses Any typing (acceptable for early stage but not ideal)
⚠️ reset() is empty stub
```

**Verdict:** ✓ ACCEPTABLE (with caveats)

### 4.3 stat_blocks.py

**Location:** `src/tri_sarira_rpg/core/stat_blocks.py`

**Classes:**
- `StatBlock` - Stats per actor (strength, mind, spirit)

**Methods:**
- `apply_growth(other: StatBlock) -> None` (stub)

**Validation:**
```
✗ Contains game-specific content (strength/mind/spirit)
✗ Belongs in systems/ or data models, NOT core/
✗ Violates spec 5.2: "No game-content in core/"
✗ Simplified model (3 stats vs spec 3.1 requiring 12 stats)
✗ Naming deviation: uses "strength/mind/spirit" instead of "body_score/mind_score/spirit_score" (spec 5.4 §9.1)
✗ apply_growth() belongs in ProgressionSystem, not here
⚠️ Method is stub (pass)
```

**Verdict:** ✗ MISPLACED - architectural violation

---

## 5. DEPENDENCY VALIDATIE

### 5.1 Import Analysis

All 3 files import ONLY from stdlib:
```
entities.py:    dataclasses, __future__
game_state.py:  dataclasses, typing, __future__
stat_blocks.py: dataclasses, __future__
```

**Validation:**
```
✓ No Pygame dependencies
✓ No cross-module dependencies
✓ No external packages
✓ Fully self-contained
```

**Verdict:** ✓ EXCELLENT - clean dependencies

---

## 6. CODING GUIDELINES VALIDATIE (SPEC 5.4)

### 6.1 Naming Conventions

| Aspect | Required | Actual | Status |
|--------|----------|--------|--------|
| Modules | lower_snake_case | entities.py, game_state.py, stat_blocks.py | ✓ |
| Classes | CamelCase | Entity, Position, GameState, StatBlock | ✓ |
| Methods | lower_snake_case | to_dict, get_system, reset, apply_growth | ✓ |
| Type hints | Required in core/ | Present (with Any in GameState) | ⚠️ |
| Docstrings | Required | Present (Dutch) | ✓ |

### 6.2 Tri-Śarīra Specific (§9.1)

```
✗ StatBlock uses "strength/mind/spirit"
  → Should use "body_score/mind_score/spirit_score"
```

### 6.3 Code Quality

```
✓ Short, clear classes
✓ No clever tricks
✓ Explicit dataclasses
⚠️ Multiple stub methods (pass bodies)
```

---

## 7. ARCHITECT_HANDOVER STEP 1 VALIDATIE

**Step 1 Requirements:**
1. Project structure exact zoals 5.3 (folders + empty modules)
2. Minimal pyproject.toml met pygame, pytest, ruff, mypy
3. Implement app/game.py + app/main.py:
   - Game class, Pygame init, main-loop, SceneManager plumbing
4. Implement core.config, core.scene, core.resources, core.logging_setup (minimal but working)
5. Goal: `python -m tri_sarira_rpg.app.main` should show empty window / simple test scene

**Status Check:**

| Requirement | Status | Notes |
|-------------|--------|-------|
| Project structure (5.3) | ✓ PASS | 100% complete |
| pyproject.toml with deps | ✗ FAIL | File is empty (0 bytes) |
| app/game.py (Game class) | ✗ FAIL | File is empty |
| app/main.py (entrypoint) | ✗ FAIL | File is empty |
| core.config | ✗ FAIL | File is empty |
| core.scene | ✗ FAIL | File is empty |
| core.resources | ✗ FAIL | File is empty |
| core.logging_setup | ✗ FAIL | File is empty |
| Can run main | ✗ FAIL | No code to run |

**Verdict:** ✗ **DOES NOT MEET STEP 1 CRITERIA**

The branch has completed **Step 0** (folder structure) but has NOT completed **Step 1** (skeleton implementation).

---

## 8. ISSUES IDENTIFICATIE

### 8.1 Critical Issues (Blockers)

1. **CRITICAL**: pyproject.toml is empty
   - No dependencies defined (pygame, pytest, ruff, mypy)
   - No build configuration
   - Cannot install or run the project

2. **CRITICAL**: No Game class or entrypoint
   - app/game.py is empty
   - app/main.py is empty
   - Cannot run `python -m tri_sarira_rpg.app.main`

3. **CRITICAL**: All core infrastructure modules are empty
   - core/config.py (0 bytes)
   - core/scene.py (0 bytes)
   - core/resources.py (0 bytes)
   - core/logging_setup.py (0 bytes)

### 8.2 Architectural Issues

4. **ARCHITECTURAL**: stat_blocks.py misplaced
   - Game-specific content in core/ violates spec 5.2
   - Should be in systems/ or as data model
   - Uses wrong naming convention (strength vs body_score)

5. **ARCHITECTURAL**: Incomplete stat model
   - StatBlock has 3 stats (strength, mind, spirit)
   - Spec 3.1 requires 12 stats: STR, END, DEF, FOC, INS, WILL, MAG, PRA, RES, SPD, ACC, DEV
   - Missing resource pools: Stamina, Focus, Prāṇa

### 8.3 Code Quality Issues

6. **QUALITY**: Multiple stub methods with `pass`
   - GameState.reset()
   - StatBlock.apply_growth()
   - Should either be implemented or have clear TODO comments

7. **QUALITY**: Any typing in GameState
   - systems: dict[str, Any]
   - get_system() -> Any
   - Should use Protocol or base System class for type safety

### 8.4 Missing Critical Components

8. **MISSING**: All systems modules (10 files, 0 bytes each)
9. **MISSING**: All presentation modules (6 files, 0 bytes each)
10. **MISSING**: All data_access modules (2 files, 0 bytes each)
11. **MISSING**: All data files (12 JSON files, 0 bytes each)
12. **MISSING**: All config files (2 TOML files, 0 bytes each)
13. **MISSING**: All tools (5 Python files, 0 bytes each)
14. **MISSING**: All tests (4 Python files, 0 bytes each)

---

## 9. VOORGESTELDE REFACTORS

### 9.1 Immediate (before any new development)

**REFACTOR 1: Move or remove stat_blocks.py**

Option A - Remove temporarily:
```bash
# stat_blocks.py hoort niet in core/
# Verwijder tot ProgressionSystem/Actor models worden geïmplementeerd
git rm src/tri_sarira_rpg/core/stat_blocks.py
```

Option B - Move to correct location (premature):
```bash
# Alleen als je direct aan stats wilt werken
# Hernoem naar correct domeinmodel + pas stats aan naar spec 3.1
```

**Reasoning:** Core should only contain generic infrastructure. Stats are game-specific domain models.

**REFACTOR 2: Add TODO markers to stub methods**

```python
# In game_state.py
def reset(self) -> None:
    """Reset tijdelijke runtime-state."""
    # TODO: Implement reset logic when systems are defined
    pass

# In entities.py (optional)
def to_dict(self) -> dict[str, object]:
    """Serieel uitgangspunt voor saves."""
    # TODO: Consider moving to SaveSystem when implemented
    return {"entity_id": self.entity_id}
```

**REFACTOR 3: Improve GameState typing**

```python
# Option A: Keep simple for now
from typing import Any, Protocol

class System(Protocol):
    """Base protocol for game systems."""
    pass

@dataclass
class GameState:
    systems: dict[str, System]  # More specific than Any

    def get_system(self, name: str) -> System | None:
        return self.systems.get(name)
```

### 9.2 Before Step 1 completion

**REFACTOR 4: Implement minimal pyproject.toml**

See section 10.2 for complete pyproject.toml template.

**REFACTOR 5: Implement minimal Game skeleton**

See section 10.3 for minimal Game class template.

**REFACTOR 6: Implement minimal Scene infrastructure**

See section 10.4 for minimal Scene/SceneManager template.

---

## 10. AANBEVELINGEN

### 10.1 Prioriteit: Complete Step 1 eerst

De branch moet EERST Step 1 van architect_handover voltooien voordat er aan Step 2+ wordt gewerkt:

**Step 1 Checklist:**
- [ ] pyproject.toml met dependencies
- [ ] app/game.py met Game class (Pygame init, main loop)
- [ ] app/main.py met entrypoint
- [ ] core/config.py met Config class (TOML loading)
- [ ] core/scene.py met Scene baseclass + SceneManager
- [ ] core/resources.py met ResourceManager stub
- [ ] core/logging_setup.py met logging config
- [ ] Test: `python -m tri_sarira_rpg.app.main` toont venster

**Na Step 1:**
- Pas dan naar Step 2 (data layer)
- Bewaar entities.py en game_state.py (acceptable)
- Verwijder of refactor stat_blocks.py

### 10.2 Template: pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "tri-sarira-rpg"
version = "0.1.0"
description = "Tri-Śarīra RPG - A spiritual journey through dharma and karma"
requires-python = ">=3.12"
dependencies = [
    "pygame>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.ruff]
line-length = 100
target-version = "py312"
select = ["E", "F", "W", "I", "N"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Voor vroege fase
files = ["src/tri_sarira_rpg/core", "src/tri_sarira_rpg/systems", "src/tri_sarira_rpg/data_access"]
```

### 10.3 Template: Minimal Game class

```python
# src/tri_sarira_rpg/app/game.py
"""Main game class en bootstrap."""

from __future__ import annotations

import pygame


class Game:
    """Hoofdgame-klasse: init, main-loop, bootstrap."""

    def __init__(self) -> None:
        """Initialiseer Pygame en basiscomponenten."""
        pygame.init()

        # TODO: Load from config
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Tri-Śarīra RPG")

        self.clock = pygame.time.Clock()
        self.running = False

        # TODO: Initialize systems, scene manager, etc.

    def run(self) -> None:
        """Main game loop."""
        self.running = True

        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds

            # Input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Update
            # TODO: scene_manager.update(dt)

            # Render
            self.screen.fill((0, 0, 0))  # Black background
            # TODO: scene_manager.render(self.screen)

            pygame.display.flip()

        pygame.quit()


__all__ = ["Game"]
```

### 10.4 Template: Minimal main.py

```python
# src/tri_sarira_rpg/app/main.py
"""Entrypoint voor het spel."""

from __future__ import annotations

from tri_sarira_rpg.app.game import Game


def main() -> None:
    """Start het spel."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
```

### 10.5 Development Workflow

**Aanbevolen volgorde:**

1. **Implementeer templates hierboven** → Test dat venster opent
2. **Implement minimal Config** → TOML loading works
3. **Implement minimal Scene/SceneManager** → Can switch scenes
4. **Add simple test scene** → Proves architecture works
5. **Dan pas** → Step 2 (data layer)

**Commit strategie:**
```bash
git add pyproject.toml
git commit -m "Add project dependencies and tool config"

git add src/tri_sarira_rpg/app/game.py src/tri_sarira_rpg/app/main.py
git commit -m "Implement minimal Game class and entrypoint"

git add src/tri_sarira_rpg/core/scene.py
git commit -m "Implement Scene baseclass and SceneManager"

# etc.
```

---

## 11. FINALE BEOORDELING

### 11.1 Huidige Status

**Feature branch:** feature/f1-architecture-skeleton
**Completion level:** ~5% (folder structure only)

**Wat werkt:**
- ✓ Perfecte folder structuur (spec 5.3)
- ✓ Goede .gitignore
- ✓ 2 acceptabele core dataclasses (entities, game_state)
- ✓ Schone dependencies (stdlib only)

**Wat niet werkt:**
- ✗ Geen werkende code (kan niet runnen)
- ✗ Geen pyproject.toml dependencies
- ✗ Alle spec 5.3 critical modules leeg
- ✗ 1 misplaced dataclass (stat_blocks)

### 11.2 Voldoet aan Fase 1?

**Nee.** De branch heeft:
- ✓ Step 0: Folder structure
- ✗ Step 1: Skeleton implementation

Step 1 vereist een werkend skeleton met Game class, Pygame init, en scene infrastructure. Niets hiervan is geïmplementeerd.

### 11.3 Aanbeveling

**Optie A: Complete Step 1 in deze branch (AANBEVOLEN)**
```
1. Gebruik templates uit sectie 10
2. Implementeer minimal maar werkend skeleton
3. Verwijder of refactor stat_blocks.py
4. Test dat main draait en venster toont
5. Commit als "Complete Step 1 skeleton"
```

**Optie B: Start fresh vanuit docs**
```
1. Gebruik deze branch alleen voor structuur-referentie
2. Implementeer Step 1 compleet in nieuwe commits
3. Focus op werkende code, niet op lege bestanden
```

**Optie C: Gebruik Codex voor bulk implementation**
```
1. Geef Codex de templates + specs
2. Laat alle modules in één keer genereren
3. Review en refactor waar nodig
4. Risico: veel code om te reviewen
```

### 11.4 Next Steps

**Onmiddellijk:**
1. Besluit: refactor deze branch of start fresh?
2. Implementeer pyproject.toml
3. Implementeer minimal Game + entrypoint
4. Test dat het draait

**Daarna:**
5. Complete rest van Step 1 (Config, Scene, Resources)
6. Refactor stat_blocks.py weg uit core/
7. Add TODO markers aan stub methods
8. Proceed naar Step 2 (data layer)

---

## APPENDIX A: Complete File Inventory

### Python Files with Content (3 files, 76 lines)
1. `src/tri_sarira_rpg/core/entities.py` - 28 lines - ✓ ACCEPTABLE
2. `src/tri_sarira_rpg/core/game_state.py` - 26 lines - ✓ ACCEPTABLE
3. `src/tri_sarira_rpg/core/stat_blocks.py` - 22 lines - ✗ MISPLACED

### Empty Python Files (43 files, 0 bytes each)
- All app/ modules (3 files)
- All systems/ modules (10 files)
- All data_access/ modules (4 files)
- All presentation/ modules (10 files)
- All utils/ modules (5 files)
- All tools/ modules (6 files)
- All tests/ modules (5 files)

### Empty Data/Config Files
- data/*.json - 12 files
- config/*.toml - 2 files
- maps/*.tmx - 5 files
- schema/*.schema.json - 12 files

### Scripts (7 files)
- All present, all empty

---

## APPENDIX B: References

**Architecture Documentation:**
- docs/architecture/5.1 Tech Overview – Tri-Śarīra RPG.md
- docs/architecture/5.2 Code Architectuur-overzicht (light) – Tri-Śarīra RPG.md
- docs/architecture/5.3 Folder- & Module-structuur – Tri-Śarīra RPG.md
- docs/architecture/5.4 Coding Guidelines – Tri-Śarīra RPG.md
- docs/architecture/architect_handover.md

**System Specifications:**
- docs/architecture/3.1 Combat & Stats Spec – Tri-Śarīra RPG.md
- docs/architecture/3.2 Time, World & Overworld Spec – Tri-Śarīra RPG.md
- docs/architecture/3.3 NPC & Party System Spec – Tri-Śarīra RPG.md
- docs/architecture/3.4 Quests & Dialogue System Spec – Tri-Śarīra RPG.md
- docs/architecture/3.5 Progression & Leveling Spec – Tri-Śarīra RPG.md
- docs/architecture/3.6 Items, Gear & Economy Spec – Tri-Śarīra RPG.md
- docs/architecture/3.7 Post-game & NG+ Spec – Tri-Śarīra RPG.md
- docs/architecture/3.8 Save & Trilogy Continuity Spec – Tri-Śarīra RPG.md

---

**Review completed:** 2025-11-15
**Total files analyzed:** 161
**Code lines analyzed:** 76
**Issues identified:** 14
**Recommendations:** 6

**Overall grade:** ⚠️ **INCOMPLETE** - Requires Step 1 implementation before proceeding
