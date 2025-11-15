# Step 4: NPC & Party System – Review Document

**Date**: 2025-11-16
**Feature Branch**: `feature/f5-npc-and-party`
**Claude Branch**: `claude/f5-npc-and-party-01L7zbTT5gLxNKbsnXfKvHJN`
**Step**: Step 4 v0 – NPC & Party System (Foundation)

---

## 1. Samenvatting

Dit document beschrijft de implementatie van **Step 4: NPC & Party System (v0)**, een foundational versie van het party management systeem voor Tri-Śarīra RPG. De focus ligt op het creëren van een minimaal maar uitbreidbaar systeem dat companions kan tracken, de active party kan beheren, en visuele feedback biedt in de overworld.

**Kernfunctionaliteit**:
- NPC metadata management (`npc_meta.json`)
- Party system met active party (max 2) + reserve pool
- Visual follower rendering in overworld
- Debug controls voor party management
- Volledige integratie met bestaande systems

---

## 2. Scope

### 2.1 Wat IS geïmplementeerd

**Data Layer**:
- ✅ `data/npc_meta.json` – NPC metadata schema met companion flags
- ✅ DataRepository uitgebreid met NPC metadata loading
- ✅ Validatie voor npc_meta in `tools/validate_data.py`

**Systems Layer**:
- ✅ `systems/party.py` – Complete PartySystem implementatie
- ✅ PartyMember en PartyState dataclasses
- ✅ Party management methods (add, remove, move to reserve)
- ✅ Main character protection (non-removable)
- ✅ Party size limit enforcement (max 2 voor v0)

**Presentation Layer**:
- ✅ PartySystem integratie in `app/game.py`
- ✅ OverworldScene uitgebreid met party rendering
- ✅ Visual followers (groene cirkels, 1 tile achter player)
- ✅ Party info display in HUD (rechts boven)
- ✅ Debug key **J** voor Rajani toggle

**Testing & Tooling**:
- ✅ `test_party.py` – 3 unit tests (all passing)
- ✅ Integration met bestaande tests (portals, validation)
- ✅ Data validation tool updated

### 2.2 Wat is NIET geïmplementeerd (expliciet out-of-scope)

❌ **Quest system** – Geen recruitment quests
❌ **Dialogue system** – Geen NPC gesprekken
❌ **Battle scene integratie** – Party members niet actief in combat
❌ **Circle of Companions hub** – Geen dedicated party management UI
❌ **Save/load systeem** – Party state wordt niet persistent opgeslagen
❌ **NPC schedules** – NPCs hebben geen wereldpositie of beweging
❌ **Guest mechanics** – Guest-only flag bestaat maar wordt niet gebruikt
❌ **Phase transitions** – NPC phases (SEED/COMPANION/SETTLED) worden getracked maar niet gewijzigd

---

## 3. Architectuur & Design

### 3.1 Data Model

**`data/npc_meta.json`** schema:
```json
{
  "npcs": [
    {
      "npc_id": "npc_mc_adhira",           // Unique NPC identifier
      "actor_id": "mc_adhira",             // Links naar actors.json
      "tier": "S",                         // S/A/B/C/D tier
      "is_companion_candidate": false,     // Kan in party
      "is_main_character": true,           // Main character flag
      "companion_flags": {
        "recruited": true,                 // Al gerekruteerd
        "in_party": true,                  // In active party
        "in_reserve_pool": false,          // In reserve pool
        "phase": "COMPANION",              // SEED/COMPANION/SETTLED/EPILOGUE
        "guest_only": false                // Tijdelijk party member
      },
      "home_region_id": "r1_chandrapur_valley",
      "role_hint": "Body-frontliner / Spirit-novice"
    }
  ]
}
```

**Bestaande NPCs** (v0):
1. **Adhira** (MC): Tier S, altijd in active party, non-removable
2. **Rajani**: Tier A, companion candidate, initially not recruited

### 3.2 PartySystem Implementatie

**Dataclasses**:
```python
@dataclass
class PartyMember:
    npc_id: str
    actor_id: str
    is_main_character: bool = False
    is_guest: bool = False
    tier: str | None = None

@dataclass
class PartyState:
    active_party: list[PartyMember]       # Max 2 voor v0
    reserve_pool: list[PartyMember]       # Unlimited
    party_max_size: int = 2
```

**Key Methods**:
- `get_active_party()` → lijst van PartyMember in active party
- `get_reserve_pool()` → lijst van PartyMember in reserve
- `add_to_reserve_pool(npc_id, actor_id, ...)` → recruit een companion
- `add_to_active_party(npc_id)` → verplaats van reserve naar active (met size check)
- `move_to_reserve(npc_id)` → verplaats van active naar reserve (MC protected)
- `is_in_party(npc_id)` / `is_in_reserve(npc_id)` → status checks

**Initialisatie**:
PartySystem initialiseert van `npc_meta.json`:
- NPCs met `recruited: true, in_party: true` → active_party
- NPCs met `recruited: true, in_reserve_pool: true` → reserve_pool
- NPCs met `recruited: false` → worden overgeslagen (nog niet in game)
- Fallback: als geen MC gevonden, wordt default MC toegevoegd

### 3.3 Visual Rendering

**Follower Rendering** (`overworld.py:_render_followers`):
- Followers worden gerendered als **groene cirkels** (player = blauw)
- Positie: **1 tile achter de player** (gebaseerd op facing direction)
- Multi-follower support: followers vormen een chain
- Rendering order: followers eerst, dan player (zodat player bovenop staat)

**HUD Updates**:
- **Party info** (rechts boven): Toont "Party (1/2):" met lijst van members
- Member display: "Adhira (MC)", "Rajani"
- **Controls** (rechts onder): Toegevoegd "J: Toggle Rajani (debug)"

**Debug Controls**:
- **J key**: Toggle Rajani in/out of party
  - Als niet gerekruteerd: recruit + add to party
  - Als in reserve: add to party (als ruimte)
  - Als in party: move to reserve
  - Logs debug messages naar console

---

## 4. Testing

### 4.1 Unit Tests (`test_party.py`)

**Test 1: Initial party has main character only**
- ✅ Verified: PartySystem initialiseert met alleen MC
- ✅ Verified: MC is `is_main_character = True`

**Test 2: Add companion respects party limit**
- ✅ Verified: Kan Rajani toevoegen als party < max_size
- ✅ Verified: Kan 3e member NIET toevoegen als party vol is
- ✅ Verified: Party max_size = 2 wordt gerespecteerd

**Test 3: Move companion to reserve pool**
- ✅ Verified: Kan companion verplaatsen naar reserve
- ✅ Verified: MC kan NIET verplaatst worden naar reserve
- ✅ Verified: Party state correct na move

**Resultaat**: 3/3 tests passed ✅

### 4.2 Integration Tests

**Data Validation** (`tools/validate_data.py`):
- ✅ `npc_meta.json` structuur validated
- ✅ Required keys gecontroleerd (npc_id, actor_id, tier, flags)
- ✅ NPC summary output correct (2 NPCs: Adhira MC, Rajani not recruited)

**Portal Tests** (`test_portals.py`):
- ✅ Alle bestaande portal tests blijven passing
- ✅ Geen regressies in WorldSystem door PartySystem toevoeging

### 4.3 Manual Testing (aanbevolen)

**Gameplay Flow**:
1. Start game → Adhira zichtbaar als blauwe cirkel
2. Press **J** → Rajani recruited + verschijnt als groene cirkel achter Adhira
3. HUD toont "Party (2/2): Adhira (MC), Rajani"
4. Walk around → Rajani volgt 1 tile achter
5. Press **J** again → Rajani verwijderd, HUD toont "Party (1/2): Adhira (MC)"
6. Portal transition → Party state blijft behouden

---

## 5. Code Quality

### 5.1 Sterke Punten

✅ **Clean separation of concerns**: Data/Systems/Presentation layers goed gescheiden
✅ **Type hints**: Volledige type annotaties in alle nieuwe code
✅ **Dataclasses**: Gebruik van modern Python patterns
✅ **Defensive programming**: MC protection, party size limits, bounds checking
✅ **Logging**: Debug messages voor alle party state changes
✅ **Documentation**: Docstrings voor alle publieke methods
✅ **Testing**: Unit tests + integration tests
✅ **Backwards compatible**: Geen breaking changes in bestaande code

### 5.2 Known Limitations

⚠️ **Follower positioning**: Simpel 1-tile-behind model, geen smooth following
⚠️ **No collision check**: Followers kunnen op blocked tiles staan
⚠️ **No persistence**: Party state reset bij game restart
⚠️ **Hardcoded Rajani**: Debug key werkt alleen voor Rajani
⚠️ **No battle integration**: Party members hebben geen effect op combat
⚠️ **Visual placeholders**: Groene cirkels ipv echte sprites

### 5.3 Technische Schuld

Geen kritische technische schuld geïntroduceerd. Alle limitations zijn inherent aan v0 scope en worden in toekomstige steps opgelost.

---

## 6. Files Changed

### 6.1 New Files

| File | Lines | Purpose |
|------|-------|---------|
| `data/npc_meta.json` | 38 | NPC metadata schema |
| `test_party.py` | 215 | Unit tests voor PartySystem |
| `docs/reviews/2025-11-16_npc-and-party_step4.md` | (this file) | Review document |

### 6.2 Modified Files

| File | Changes | Summary |
|------|---------|---------|
| `src/tri_sarira_rpg/systems/party.py` | 280 lines (was 30 line skeleton) | Complete PartySystem implementatie |
| `src/tri_sarira_rpg/data_access/repository.py` | +60 lines | NPC metadata methods + validation |
| `src/tri_sarira_rpg/app/game.py` | +9 lines | PartySystem instantiation |
| `src/tri_sarira_rpg/presentation/overworld.py` | +90 lines | Follower rendering + debug controls + HUD |
| `tools/validate_data.py` | +14 lines | NPC metadata summary |

**Total**: ~700 new/changed lines of code

---

## 7. Future Work

### 7.1 Short-term (Step 5-6)

1. **Follower collision avoidance**: Followers respect collision layer
2. **Smooth following**: Position queue voor natuurlijker volgen
3. **Multiple companions**: Upgrade party_max_size naar 4
4. **Sprite rendering**: Echte character sprites ipv gekleurde cirkels

### 7.2 Mid-term (Step 7-10)

5. **Recruitment quests**: Integration met quest system
6. **Dialogue system**: NPC gesprekken voor recruitment
7. **Circle of Companions**: Dedicated party management UI
8. **Save/load**: Persistent party state

### 7.3 Long-term (Step 11+)

9. **Battle integration**: Party members vechten mee
10. **Guest mechanics**: Tijdelijke party members (story events)
11. **Phase transitions**: Seed → Companion → Settled → Epilogue
12. **NPC schedules**: Wereld posities + beweging

---

## 8. Conclusie

**Status**: ✅ **Step 4 v0 Complete**

De foundational implementation van het NPC & Party System is succesvol afgerond. Alle scope requirements zijn geïmplementeerd, alle tests passen, en er zijn geen kritische issues.

**Belangrijkste Achievement**:
Een minimaal maar uitbreidbaar party management systeem dat:
- Clean architectuur volgt (data/systems/presentation)
- Volledig getest is (unit + integration tests)
- Visuele feedback biedt (follower rendering + HUD)
- Klaar is voor toekomstige uitbreidingen (quest/dialogue/battle/save systems)

**Aanbeveling**: Ready for merge naar `main` branch na code review.

---

## 9. Appendix: Testing Checklist

Voor reviewers en testers:

- [ ] Run `python test_party.py` → 3/3 tests passing
- [ ] Run `python tools/validate_data.py` → All validation passing
- [ ] Run `python test_portals.py` → All portal tests passing
- [ ] Start game: `python -m tri_sarira_rpg.app.main`
- [ ] Verify HUD shows "Party (1/2): Adhira (MC)"
- [ ] Press J → Rajani appears, HUD shows "Party (2/2)"
- [ ] Walk around → Rajani follows behind player
- [ ] Press J again → Rajani disappears
- [ ] Travel through portals → Party state maintained
- [ ] Check logs → Debug messages for party changes

**All checks passing** = Ready for merge ✅
