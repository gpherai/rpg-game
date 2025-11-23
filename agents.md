# Agents Guide – Tri-Śarīra RPG

Een korte, actuele leidraad voor AI-agents (analyserend of implementerend) die aan deze codebase werken.

## Doel & Rollen
- **Doel:** consistente, architecture-first bijdragen leveren; data-gedreven, testbaar, en in lijn met de 5.x-architectuurdocs.
- **Analyse-agent (bv. Gemini):** vergelijkt implementatie met specs, identificeert gaps/deviaties, stelt fixes voor.
- **Implementatie-agent (bv. Codex/CLI):** voert afgesproken fixes uit, schrijft code/tests/docs, valideert lokaal.

## Kernbronnen (bron van waarheid)
- Architectuur & stijl: `docs/architecture/5.1–5.5` (stack, lagen, folders, coding guidelines, run/build).
- Domein/specs: `docs/architecture/1.x–4.x` (visie, Tri-Śarīra, systems, data, Tiled).
- Status & reviews: `docs/CODEBASE_STATUS.md`, `docs/reviews/`.
- Werkwijze-analyse: `gemini.md`.
- Code & data: `src/tri_sarira_rpg/`, `data/`, `schema/`, `maps/`.

## Guardrails (altijd)
- **Scheiding:** systems = pure logica (geen Pygame); presentation = UI/scenes; data_access via repository; services voor UI-facades; DI via `core/protocols.py`; UI praat met immutable viewmodels.
- **Data-driven:** content in JSON/Tiled, niet hardcoded. Respecteer ID-conventies (`mc_adhira`, `q_r1_*`, `z_r1_*`).
- **Coding style:** black, ruff, type hints (verplicht in core/systems/data_access), korte leesbare functies, logging ipv print, asserts voor invariants, comments alleen voor “waarom”.
- **Geen nieuwe top-level mappen** zonder afstemming met 5.3; pas bestaande structuur toe.

## Workflow per wijziging
1. **Scope & context:** lees relevante specs (5.x + betreffende 3.x/4.x) en reviews voor het onderdeel.
2. **Analyse:** identificeer gaps tov specs (architectuur, data, tests). Noteer afhankelijke modules/data.
3. **Plan & implementatie:** wijzig alleen in de juiste laag; houd Protocol-/ViewModel-contracten intact.
4. **Tests & checks:** minimaal `python -m tools.validate_data`; bij codewijzigingen `pytest` (of gerichte tests); formatter/linter via scripts/format of handmatig (`black src tests tools`, `ruff check src tests tools`).
5. **Rapporteren:** vermeld paden, kernwijzigingen, uitgevoerde tests/validatie, bekende resterende risico’s.

## Snelle checklists
- **Systems-code:** Pygame-vrij, programmeer tegen `core/protocols`, lever viewmodels uit `*_viewmodels.py`.
- **Presentation/Scenes:** consumeer alleen viewmodels/facades; input/loop-structuur volgen bestaande scene-patterns.
- **Data updates:** schema in `schema/`, content in `data/`; run `python -m tools.validate_data`; houd referenties (IDs) consistent.
- **Save/load:** gebruik `SaveableSystem`-patroon; breek save-schema niet zonder migratie/versiebeleid.
- **Per-layer roadmap fixes:** werk gefaseerd (laag/onderdeel per stap) en verifieer na elke stap met relevante tests/validatie.

## Runtime & commands
- Game run: `python -m tri_sarira_rpg.app.main`.
- Data check: `python -m tools.validate_data`.
- Tests: `pytest` of specifiek bestand (bv. `pytest tests/test_combat_system.py`).
- Formatter/linter: `black src tests tools` en `ruff check src tests tools`.
