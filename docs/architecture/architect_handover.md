1. Wat er nu in feite AF is (artefacten)

1. Visie & scope

1.1 Game Overview / Vision One-Pager
→ Wat voor game Tri-Śarīra RPG is, gevoel, scope (lange SP-RPG, ~100h main, spiritualiteit als kern).

1.2 Core Baseline
→ Kernpijlers: Tri-Śarīra, open world-zones, turn-based combat, companions, kalender & festivals, post-game & trilogie.

1.3 Feature Roadmap / Milestones
→ Roadmap van vertical slice → full R1 → rest wereld → post-game → deel 2/3.

2. Wereld & verhaal

2.1 World & Regions Overview
→ Structuur van de wereld (R1 Chandrapur etc.), zonesoorten (town/route/shrine/dungeon).

2.2 Kalender & Festivals Spec
→ Dag/nacht, seizoenen, vaste evenementen, hoe festivals de wereld beïnvloeden.

2.3 NPC Cast & Fasen
→ Belangrijke NPC’s, hun levensbogen (ontmoeting → companion → vestigen).

2.4 Quest Taxonomy & Voorbeeldlijst
→ Soorten quests (main, companion, karma, ritual, etc.) + concrete voorbeelden.

3. Systems (gameplay)

3.1 Combat & Stats Spec
→ Stats, Tri-domeinen, damage-logica, skills, status, enemy-rollen.

3.2 Time, World & Overworld Spec
→ Zones, movement, encounters, portals, dag/nacht & seizoensinvloed op wereld.

3.3 NPC & Party System Spec
→ Party-structuur, companions, Circle of Companions, missables-regels.

3.4 Quests & Dialogue System Spec
→ Queststate, objectives, flags, dialogue-graphs, conditions/effects.

3.5 Progression & Leveling Spec
→ XP-curves, level-ups, skill unlocks, Tri-profielen.

3.6 Items, Gear & Economy Spec
→ Itemtypes, gear, shops, currency, droprates/loot-tables.

3.7 Post-game & NG+ Spec
→ Post-game challenges, festivals, avatar summons, NG+ logica.

3.8 Save & Trilogy Continuity Spec
→ Save-structuur, wat per run blijft, wat naar deel 2/3 meegaat (Trilogy export profile).

4. Data & schema’s

4.1 JSON-schema’s per type (conceptueel)
→ Welke soorten schema’s we hebben (actors, enemies, items, skills, quests, dialogue, npc_schedules, events, shops, loot_tables, chests, zones, savegame).

4.2 Voorbeeld-data per type
→ Concrete *_example.json files (MC Adhira, Rajani, forest enemies, eerste shrine-quest, dialogue, chests, shops, savegame-slice).

4.3 Tiled Conventions & Map Metadata Spec
→ Hoe maps/*.tmx zijn opgebouwd: layers, object-layers, map-properties, portals, events, encounter regions, chests, shrine-markers.

5. Tech & code

5.1 Tech Overview
→ Stack (Python + Pygame, data-driven JSON/Tiled), hoofdlagen, welke systems er zijn, wat vertical slice technisch nodig heeft.

5.2 Code Architectuur-overzicht (light)
→ Modules en hun rollen (app, core, systems, data_access, presentation, utils), flows (start → overworld, NPC → quest, overworld → battle → terug, save/load).

5.3 Folder- & Module-structuur
→ Concrete projectboom (src/tri_sarira_rpg/..., data/, schema/, maps/, assets/, tools/, tests/, scripts/).

5.4 Coding Guidelines
→ PEP8/black/ruff, type hints, scheiding systems vs scenes, logging, tests, hoe AI-code zich moet gedragen.

5.5 Run- & Build-instructies
→ Hoe de repo lokaal draait in WSL, venv, python -m tri_sarira_rpg.app.main, tools.validate_data, pytest, basic build/distributie.

Daarnaast heb je al eerdere basisdocs zoals:

Core Game Vision,

Solution Outline,

Scenes & State Flow,

Systems Overview – Global Systems,

Vertical Slice Specificatie,

Tri-Śarīra System Spec,

de geconsolideerde core (tri_sarira_rpg_consolidated_core_v_0 / agreed baseline).

Die vormen de “oude kern” waar de nieuwe 1.x–5.x netjes bovenop liggen.

2. Bronnen van waarheid (voor Codex/Claude)

Als je 3 zinnen wilt meegeven:

Canon: Houd je aan 1.2 Core Baseline, 3.x Systems-specs, 4.3 Tiled Conventions, 5.1–5.5 en de folderstructuur in 5.3.
Data is leidend: Alle content (actors, enemies, items, quests, dialogue, zones, events, shops, loot) komt uit data/*.json + maps/*.tmx.
Architectuur is stabiel: Geen nieuwe toplevel-mappen of radicaal andere architectuur zonder expliciet akkoord.

3. Hoe alles samenhangt (kort)

Je kunt het zo zien:

Visie & wereld (1.x–2.x)
→ definieert wat voor game en welke wereld.

Systems-specs (3.x)
→ zetten alle mechanieken om in concrete regels: stats, combat, tijd, quests, NPC’s, progression, items, save, trilogy.

Data & maps (4.x)
→ leggen die regels vast in JSON + Tiled (schema’s, voorbeelddata, mapconventies).

Tech & code (5.x)
→ beschrijft hoe de codebase eruitziet, hoe systems/Scenes/data samenkomen, en hoe je het runt/test/bouwt.

AI-devs moeten dus:
eerst de 5.x + 3.x + 4.3 begrijpen,
dan de code en data bouwen,
daarna de wereld vullen met content (meer data/maps).

4. Aanbevolen bouwvolgorde voor AI-devs

Je kunt dit bijna 1-op-1 als stappenplan geven.

Stap 0 – Leesrichting

Lees 5.1 Tech Overview → globaal begrip van stack & lagen.

Lees 5.2 Architectuur + 5.3 Folder-structuur → waar komt welke code.

Scan 3.1–3.8 voor systems-gedrag.

Scan 4.3 Tiled Conventions + 4.2 Voorbeeld-data → hoe data & maps eruit zien.

Check 5.4 Coding Guidelines + 5.5 Run & Build.

Daarna pas code schrijven.

Stap 1 – Skeleton neerzetten

Maak de projectstructuur exact zoals in 5.3 (mappen + lege modules).

Voeg minimale pyproject.toml toe met pygame, pytest, ruff, mypy.

Implementeer app/game.py + app/main.py:

Game-klasse, Pygame init, main-loop, SceneManager-plumbing.

Implementeer core.config, core.scene, core.resources, core.logging_setup (minimalistisch maar werkend).

Doel:
python -m tri_sarira_rpg.app.main moet een lege window / simple testscene tonen.

Stap 2 – Data-laag & voorbeelddata

Implementeer data_access.loader + data_access.repository:

Functies om JSON uit data/ te lezen.

Eenvoudige DataRepository met get_actor, get_enemy, get_quest, get_dialogue, etc.

Zet de data/examples/*.json om naar echte data/*.json voor de vertical slice:

MC Adhira, Rajani, forest enemies, shrine-quest, eerste dialogues, shops, loot_tables, chests, zones.

Schrijf tools/validate_data.py volgens 4.x/5.1/5.3:

schema-checks, ID-ref checks.

Doel:
python -m tools.validate_data draait succesvol, en DataRepository kan voorbeelddata lezen.

Stap 3 – World & overworld

Implementeer systems.world in lijn met 3.2 en 4.3:

Tiled-map laden (maps/z_r1_chandrapur_town.tmx, z_r1_forest_route.tmx, z_r1_shrine_clearing.tmx).

Collision, portals, event-triggers, chests.

Implementeer presentation.overworld:

OverworldScene die map tekent, player beweegt, interacties doorstuurt naar WorldSystem.

Knoop Time/dag-nacht heel light vast aan de overworld (TimeSystem stub die alvast dag/nacht kent).

Doel:
Je kunt rondlopen in Chandrapur/route/shrine, portals gebruiken, chests openen.

Stap 4 – Combat & enemies

Implementeer systems.party (MC + 1 companion, stats uit actors.json).

Implementeer systems.combat volgens 3.1 + 3.5:

Turn-order, skills, damage, victory/defeat-result.

Implementeer presentation.battle:

Eenvoudige battle UI (HP-balken, skillmenu).

Zorg dat WorldSystem encounters kan triggerren op de route (EncounterRegions).

Doel:
Random/fixed encounter op de route start battle, werkt af, keert terug naar overworld met XP/loot.

Stap 5 – Dialogue & quests

Implementeer systems.dialogue in lijn met 3.4:

Nodes, choices, conditions, effectrefs.

Implementeer presentation.ui.dialogue_box + hook in overworld:

Interactie met NPC → dialogue UI, keuzes, terug naar overworld.

Implementeer systems.quests:

Quest-log, quest-state-machine, triggers vanuit events/dialogue/battle.

Doel:
Eerste main quest (q_r1_001_shrine_intro) start bij elder, stuurt je naar shrine, update state na gevecht.

Stap 6 – Items, shops, save

Implementeer systems.items + systems.economy volgens 3.6:

Inventory, consumables, equipment light.

Shop UI in Chandrapur.

Implementeer systems.save + savegame-structuur (3.8):

Ten minste: zone, player-pos, party, quests, flags, inventory, geld, opened chests.

Manuele save op inn/shrine; load via MainMenuScene.

Doel:
Vertical slice is speelbaar met save/load, basic gear & shops.

Stap 7 – Polijsten & extra

TimeSystem uitbreiden (dag/nacht echt merkbaar in encounters/NPC’s).

Festivals eerste kleine placeholder-event (op basis van 2.2).

Companion-fasen (2.3 / 3.3) zichtbaar maken (seed → companion → settled).

Begin aan hooks voor post-game/NG+ (3.7) en trilogy-export (3.8) als lege structuren.