# TH1 – Data Stubs (Step 5 baseline)

Doel: alle eerder lege JSON-bestanden vullen met minimaal geldige data en lichte shape-checks toevoegen zodat loaders/validators niet meer crashen.

## Aangepaste data-bestanden
- `data/dialogue.json`: 1 simpele NPC-dialoog (`dlg_r1_elder_shrine_intro`) met quest-start.
- `data/quests.json`: 1 main quest (`q_r1_shrine_intro`) met TALK → REACH_ZONE → DEFEAT_ENEMY_GROUP stages en beloningen.
- `data/shops.json`: `shop_r1_town_general` met basic items (`item_small_herb`, `item_stamina_tonic`).
- `data/loot_tables.json`: `lt_r1_forest_route` met kleine droprates voor herbs/tonic.
- `data/chests.json`: twee kisten (route + shrine) met items en een flag-conditie.
- `data/npc_schedules.json`: eenvoudige day/night-routes voor elder en Rajani.
- `data/events.json`: één zone-enter event voor de shrine intro.

## Validation
- `tools/validate_data.py` uitgebreid met lichte structural checks voor de nieuwe JSON’s (bestaat bestand, parse OK, bevat verwacht top-level key).

## Beperkingen
- Data blijft minimaal (1–2 entries per type), nog geen volledige quest/dialogue/AI-content.
- Geen koppeling naar gameplay-systemen toegevoegd; alleen data en validatie-shape.
- Packaging-issues en andere bekende blockers (pyproject packages, ontbrekende package-data) zijn buiten scope van deze slice.
