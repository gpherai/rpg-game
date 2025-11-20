"""Unit tests voor PartySystem (Step 4: NPC & Party)."""

from tri_sarira_rpg.systems.party import PartySystem


def test_initial_party_has_main_character_only():
    """Test dat een nieuw PartySystem alleen de main character bevat."""
    print("\n=== Test 1: Initial party has main character only ===")

    # Create minimal npc_meta with only MC
    npc_meta = {
        "npcs": [
            {
                "npc_id": "npc_mc_adhira",
                "actor_id": "mc_adhira",
                "tier": "S",
                "is_companion_candidate": False,
                "is_main_character": True,
                "companion_flags": {
                    "recruited": True,
                    "in_party": True,
                    "in_reserve_pool": False,
                    "phase": "COMPANION",
                    "guest_only": False,
                },
            }
        ]
    }

    party = PartySystem(npc_meta=npc_meta)
    active_party = party.get_active_party()

    # Verify
    assert len(active_party) == 1, f"Expected 1 member, got {len(active_party)}"
    assert active_party[0].is_main_character, "First member should be main character"
    assert active_party[0].npc_id == "npc_mc_adhira", "Main character should be Adhira"

    print(f"✓ Active party has {len(active_party)} member: {active_party[0].actor_id}")
    print("✓ Main character is correctly initialized")


def test_add_companion_respects_party_limit():
    """Test dat het toevoegen van companions de party_max_size respecteert."""
    print("\n=== Test 2: Add companion respects party limit ===")

    # Create npc_meta with MC + recruited companion in reserve
    npc_meta = {
        "npcs": [
            {
                "npc_id": "npc_mc_adhira",
                "actor_id": "mc_adhira",
                "tier": "S",
                "is_companion_candidate": False,
                "is_main_character": True,
                "companion_flags": {
                    "recruited": True,
                    "in_party": True,
                    "in_reserve_pool": False,
                    "phase": "COMPANION",
                    "guest_only": False,
                },
            },
            {
                "npc_id": "npc_comp_rajani",
                "actor_id": "comp_rajani",
                "tier": "A",
                "is_companion_candidate": True,
                "is_main_character": False,
                "companion_flags": {
                    "recruited": True,
                    "in_party": False,
                    "in_reserve_pool": True,
                    "phase": "COMPANION",
                    "guest_only": False,
                },
            },
        ]
    }

    party = PartySystem(npc_meta=npc_meta)

    # Initial state: MC only
    assert len(party.get_active_party()) == 1, "Should start with 1 member"
    assert len(party.get_reserve_pool()) == 1, "Should have 1 in reserve"
    assert party.party_max_size == 2, "Party max size should be 2"

    print(
        f"✓ Initial: {len(party.get_active_party())} active, {len(party.get_reserve_pool())} reserve"
    )

    # Add Rajani to active party (should succeed)
    success = party.add_to_active_party("npc_comp_rajani")
    assert success, "Should be able to add Rajani when party has room"
    assert len(party.get_active_party()) == 2, "Active party should now have 2 members"
    assert len(party.get_reserve_pool()) == 0, "Reserve should be empty"

    print(
        f"✓ After adding Rajani: {len(party.get_active_party())} active, {len(party.get_reserve_pool())} reserve"
    )

    # Try to add a third member (should fail - party is full)
    party.add_to_reserve_pool("npc_comp_third", "comp_third", tier="A")
    success = party.add_to_active_party("npc_comp_third")
    assert not success, "Should not be able to add third member when party is full"
    assert len(party.get_active_party()) == 2, "Active party should still have 2 members"
    assert len(party.get_reserve_pool()) == 1, "Third member should remain in reserve"

    print(
        f"✓ After trying to add third: {len(party.get_active_party())} active, {len(party.get_reserve_pool())} reserve"
    )
    print("✓ Party limit correctly enforced")


def test_move_companion_to_reserve_pool():
    """Test dat companions verplaatst kunnen worden naar reserve pool."""
    print("\n=== Test 3: Move companion to reserve pool ===")

    # Create npc_meta with MC + companion both in active party
    npc_meta = {
        "npcs": [
            {
                "npc_id": "npc_mc_adhira",
                "actor_id": "mc_adhira",
                "tier": "S",
                "is_companion_candidate": False,
                "is_main_character": True,
                "companion_flags": {
                    "recruited": True,
                    "in_party": True,
                    "in_reserve_pool": False,
                    "phase": "COMPANION",
                    "guest_only": False,
                },
            },
            {
                "npc_id": "npc_comp_rajani",
                "actor_id": "comp_rajani",
                "tier": "A",
                "is_companion_candidate": True,
                "is_main_character": False,
                "companion_flags": {
                    "recruited": True,
                    "in_party": True,
                    "in_reserve_pool": False,
                    "phase": "COMPANION",
                    "guest_only": False,
                },
            },
        ]
    }

    party = PartySystem(npc_meta=npc_meta)

    # Initial state: both in active party
    assert len(party.get_active_party()) == 2, "Should start with 2 members"
    assert len(party.get_reserve_pool()) == 0, "Reserve should be empty"

    print(
        f"✓ Initial: {len(party.get_active_party())} active, {len(party.get_reserve_pool())} reserve"
    )

    # Move Rajani to reserve
    success = party.move_to_reserve("npc_comp_rajani")
    assert success, "Should be able to move Rajani to reserve"
    assert len(party.get_active_party()) == 1, "Active party should have 1 member"
    assert len(party.get_reserve_pool()) == 1, "Reserve should have 1 member"
    assert party.get_active_party()[0].is_main_character, "Only MC should remain in active party"

    print(
        f"✓ After moving Rajani: {len(party.get_active_party())} active, {len(party.get_reserve_pool())} reserve"
    )

    # Try to move MC to reserve (should fail)
    success = party.move_to_reserve("npc_mc_adhira")
    assert not success, "Should not be able to move main character to reserve"
    assert len(party.get_active_party()) == 1, "MC should still be in active party"

    print("✓ Main character cannot be removed from party")
    print("✓ Companion successfully moved to reserve pool")


def run_all_tests():
    """Run alle PartySystem tests."""
    print("=" * 60)
    print("Testing PartySystem (Step 4: NPC & Party)")
    print("=" * 60)

    tests = [
        test_initial_party_has_main_character_only,
        test_add_companion_respects_party_limit,
        test_move_companion_to_reserve_pool,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
