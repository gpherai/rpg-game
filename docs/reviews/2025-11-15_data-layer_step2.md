# Step 2: Data Layer - Review

## Toegevoegde data-bestanden

### Configuratie (TOML)
- `config/default_config.toml` met volledige game-configuratie:
  - Display settings (resolutie, fps, titel, fullscreen)
  - Paden (data_dir, assets_dir, maps_dir, schema_dir)
  - Development flags (debug_mode, show_fps, skip_intro)
  - Logging level

### Game data (JSON)
- `data/actors.json` - Speelbare characters:
  - `mc_adhira` - Protagonist (lvl 1, Body/Spirit focus)
  - `comp_rajani` - Companion (lvl 2, Mind focus)
  - Elk met base_stats (9 stats), tags, starting_skills

- `data/enemies.json` - Vijanden:
  - `en_forest_sprout` - Minion (lvl 2, plant type)
  - `en_shrine_guardian` - Boss (lvl 6, spirit type)
  - Elk met base_stats, skills, xp/money rewards

- `data/zones.json` - Wereld-locaties:
  - `z_r1_chandrapur_town` - Startplaats (safe zone, shops, inn)
  - `z_r1_forest_route` - Route met encounters
  - `z_r1_shrine_clearing` - Dungeon/boss area
  - Elk met type, beschrijving, recommended_level, connected_zones

## Loader & Validatie implementatie

### Config loader (src/tri_sarira_rpg/core/config.py)
- Volledige `Config` dataclass met alle TOML-velden
- `Config.load()` class method voor TOML-parsing:
  - Automatische project-root detectie
  - Python 3.11+ `tomllib` support (fallback naar `tomli` voor oudere versies)
  - FileNotFoundError bij ontbrekende config
  - ValueError bij ongeldige TOML syntax
  - Duidelijke error messages

### Data loader (src/tri_sarira_rpg/data_access/loader.py)
- `DataLoader.load_json()` met cache en error handling:
  - FileNotFoundError voor ontbrekende bestanden
  - ValueError voor ongeldige JSON
  - In-memory cache voor performance

- `DataLoader.validate_data()` voor validatie:
  - Controleert top-level structuur ("actors", "enemies", "zones" keys)
  - Valideert list types
  - Controleert required keys per entry (id, name, type, level/description)
  - Type validatie voor string/int velden
  - Retourneert lijst met specifieke error messages

### Repository (src/tri_sarira_rpg/data_access/repository.py)
- `REQUIRED_KEYS` constant met validatie-regels per data type
- `DataRepository.load_and_validate_all()` voor batch validatie van alle data
- `DataRepository.get_validation_errors()` om errors op te halen
- Specifieke accessor methods:
  - `get_all_actors()`, `get_actor(actor_id)`
  - `get_all_enemies()`, `get_enemy(enemy_id)`
  - `get_all_zones()`, `get_zone(zone_id)`

## Validatie tool

### tools/validate_data.py
Standalone script voor data-validatie met twee functies:

**validate_config()**
- Laadt `config/default_config.toml`
- Print config details (resolutie, fps, titel, data_dir)
- Retourneert True/False

**validate_data()**
- Laadt alle JSON data via `DataRepository`
- Valideert structuur en required fields
- Print samenvatting met aantallen + details per entry
- Retourneert True/False

### Aanroepen validation tool

```bash
# Als module (aanbevolen)
python -m tools.validate_data

# Als script
python tools/validate_data.py
```

**Exit codes:**
- `0` = alle validatie checks geslaagd
- `1` = errors gevonden (zie output voor details)

**Voorbeeld output bij succes:**
```
INFO: Tri-Sarira RPG - Data Validation Tool
INFO: ======================================================================
INFO: Validating TOML Configuration
INFO: ======================================================================
INFO: ✓ Config loaded successfully
INFO:   - Resolution: (1280, 720)
INFO:   - FPS: 60
INFO:   - Title: Tri-Śarīra RPG
INFO:   - Data dir: data

INFO: ======================================================================
INFO: Validating JSON Data Files
INFO: ======================================================================
INFO: ✓ actors.json validated successfully
INFO: ✓ enemies.json validated successfully
INFO: ✓ zones.json validated successfully

INFO: Data Summary:
INFO:   - Actors: 2
INFO:     * mc_adhira: Adhira (lvl 1)
INFO:     * comp_rajani: Rajani (lvl 2)
INFO:   - Enemies: 2
INFO:     * en_forest_sprout: Forest Sprout (lvl 2)
INFO:     * en_shrine_guardian: Shrine Guardian (lvl 6)
INFO:   - Zones: 3
INFO:     * z_r1_chandrapur_town: Chandrapur Town (town)
INFO:     * z_r1_forest_route: Forest Route (route)
INFO:     * z_r1_shrine_clearing: Shrine Clearing (dungeon)

INFO: ======================================================================
INFO: Validation Summary
INFO: ======================================================================
INFO: Config: ✓ OK
INFO: Data:   ✓ OK

INFO: ✓ All validation checks passed!
```

## Getest

✅ `pip install -e ".[dev]"` - Package installeert correct
✅ `python -m tri_sarira_rpg.app.main` - Game start en laadt TOML config
✅ `python -m tools.validate_data` - Validatie tool werkt, alle checks OK

## Architectuur naleving

- Geen gameplay logic toegevoegd aan systems (blijven pass stubs)
- Geen scene-flow of rendering changes
- Geen refactors of herbenamingen
- Data Layer architectuur behouden (loader → repository → systems)
- Clean separation tussen config (TOML) en data (JSON)
