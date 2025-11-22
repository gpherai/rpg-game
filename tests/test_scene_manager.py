"""Tests voor SceneStackManager en SceneManagerProtocol."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tri_sarira_rpg.core.scene import (
    Scene,
    SceneManager,
    SceneManagerProtocol,
    SceneStackManager,
)


# =============================================================================
# Dummy Scene voor testing
# =============================================================================


class DummyScene(Scene):
    """Minimale Scene implementatie voor testing."""

    def __init__(self, manager: SceneManagerProtocol, name: str = "dummy") -> None:
        super().__init__(manager)
        self.name = name
        self.update_called = False
        self.render_called = False
        self.event_handled = False

    def handle_event(self, event) -> None:
        self.event_handled = True

    def update(self, dt: float) -> None:
        self.update_called = True

    def render(self, surface) -> None:
        self.render_called = True


# =============================================================================
# SceneStackManager Tests
# =============================================================================


class TestSceneStackManager:
    """Tests voor SceneStackManager."""

    def test_initial_state_is_empty(self) -> None:
        """Manager begint met lege stack."""
        manager = SceneStackManager()

        assert manager.active_scene is None
        assert len(manager) == 0
        assert list(manager.iter_scenes()) == []

    def test_push_scene_adds_to_stack(self) -> None:
        """push_scene voegt scene toe bovenop stack."""
        manager = SceneStackManager()
        scene = DummyScene(manager, "first")

        manager.push_scene(scene)

        assert manager.active_scene is scene
        assert len(manager) == 1

    def test_push_multiple_scenes(self) -> None:
        """Meerdere push_scene calls stapelen scenes."""
        manager = SceneStackManager()
        scene1 = DummyScene(manager, "first")
        scene2 = DummyScene(manager, "second")

        manager.push_scene(scene1)
        manager.push_scene(scene2)

        assert manager.active_scene is scene2
        assert len(manager) == 2

    def test_pop_scene_removes_top(self) -> None:
        """pop_scene verwijdert bovenste scene."""
        manager = SceneStackManager()
        scene1 = DummyScene(manager, "first")
        scene2 = DummyScene(manager, "second")
        manager.push_scene(scene1)
        manager.push_scene(scene2)

        manager.pop_scene()

        assert manager.active_scene is scene1
        assert len(manager) == 1

    def test_pop_scene_empty_stack_is_safe(self) -> None:
        """pop_scene op lege stack doet niets (defensief)."""
        manager = SceneStackManager()

        manager.pop_scene()  # Mag geen exception geven

        assert manager.active_scene is None
        assert len(manager) == 0

    def test_switch_scene_replaces_top(self) -> None:
        """switch_scene vervangt bovenste scene."""
        manager = SceneStackManager()
        scene1 = DummyScene(manager, "first")
        scene2 = DummyScene(manager, "second")
        manager.push_scene(scene1)

        manager.switch_scene(scene2)

        assert manager.active_scene is scene2
        assert len(manager) == 1

    def test_switch_scene_on_empty_stack(self) -> None:
        """switch_scene op lege stack pusht scene."""
        manager = SceneStackManager()
        scene = DummyScene(manager, "only")

        manager.switch_scene(scene)

        assert manager.active_scene is scene
        assert len(manager) == 1

    def test_clear_and_set_replaces_entire_stack(self) -> None:
        """clear_and_set leegt stack en zet nieuwe scene."""
        manager = SceneStackManager()
        scene1 = DummyScene(manager, "first")
        scene2 = DummyScene(manager, "second")
        scene3 = DummyScene(manager, "new")
        manager.push_scene(scene1)
        manager.push_scene(scene2)

        manager.clear_and_set(scene3)

        assert manager.active_scene is scene3
        assert len(manager) == 1
        assert list(manager.iter_scenes()) == [scene3]

    def test_iter_scenes_returns_all_scenes(self) -> None:
        """iter_scenes geeft alle scenes in stack volgorde."""
        manager = SceneStackManager()
        scene1 = DummyScene(manager, "first")
        scene2 = DummyScene(manager, "second")
        scene3 = DummyScene(manager, "third")
        manager.push_scene(scene1)
        manager.push_scene(scene2)
        manager.push_scene(scene3)

        scenes = list(manager.iter_scenes())

        assert scenes == [scene1, scene2, scene3]

    @patch("pygame.event.Event")
    def test_handle_event_forwards_to_active_scene(self, mock_event) -> None:
        """handle_event stuurt event naar actieve scene."""
        manager = SceneStackManager()
        scene = DummyScene(manager)
        manager.push_scene(scene)

        manager.handle_event(mock_event)

        assert scene.event_handled is True

    def test_handle_event_empty_stack_is_safe(self) -> None:
        """handle_event op lege stack doet niets."""
        manager = SceneStackManager()

        manager.handle_event(MagicMock())  # Mag geen exception geven

    def test_update_forwards_to_active_scene(self) -> None:
        """update stuurt dt naar actieve scene."""
        manager = SceneStackManager()
        scene = DummyScene(manager)
        manager.push_scene(scene)

        manager.update(0.016)

        assert scene.update_called is True

    def test_update_empty_stack_is_safe(self) -> None:
        """update op lege stack doet niets."""
        manager = SceneStackManager()

        manager.update(0.016)  # Mag geen exception geven

    def test_render_forwards_to_active_scene(self) -> None:
        """render stuurt surface naar actieve scene."""
        manager = SceneStackManager()
        scene = DummyScene(manager)
        manager.push_scene(scene)

        manager.render(MagicMock())

        assert scene.render_called is True

    def test_render_empty_stack_is_safe(self) -> None:
        """render op lege stack doet niets."""
        manager = SceneStackManager()

        manager.render(MagicMock())  # Mag geen exception geven


# =============================================================================
# Protocol Compliance Tests
# =============================================================================


class TestSceneManagerProtocol:
    """Tests dat SceneStackManager het protocol implementeert."""

    def test_scene_stack_manager_is_protocol_compliant(self) -> None:
        """SceneStackManager voldoet aan SceneManagerProtocol."""
        manager = SceneStackManager()

        assert isinstance(manager, SceneManagerProtocol)

    def test_scene_manager_alias_is_scene_stack_manager(self) -> None:
        """SceneManager alias verwijst naar SceneStackManager."""
        assert SceneManager is SceneStackManager


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestSceneManagerIntegration:
    """Integration tests voor typische use cases."""

    def test_overlay_scene_workflow(self) -> None:
        """Test typische overlay workflow: push overlay, dan pop."""
        manager = SceneStackManager()
        main_scene = DummyScene(manager, "main")
        overlay = DummyScene(manager, "overlay")

        # Start met main scene
        manager.push_scene(main_scene)
        assert manager.active_scene is main_scene

        # Push overlay (bijv. pause menu)
        manager.push_scene(overlay)
        assert manager.active_scene is overlay
        assert len(manager) == 2

        # Pop overlay om terug te keren
        manager.pop_scene()
        assert manager.active_scene is main_scene
        assert len(manager) == 1

    def test_scene_switch_workflow(self) -> None:
        """Test typische scene switch: main menu → overworld."""
        manager = SceneStackManager()
        menu = DummyScene(manager, "menu")
        overworld = DummyScene(manager, "overworld")

        # Start met menu
        manager.push_scene(menu)

        # Switch naar overworld (vervangt menu)
        manager.switch_scene(overworld)
        assert manager.active_scene is overworld
        assert len(manager) == 1

    def test_return_to_main_menu_workflow(self) -> None:
        """Test volledige reset naar main menu."""
        manager = SceneStackManager()
        menu = DummyScene(manager, "menu")
        overworld = DummyScene(manager, "overworld")
        battle = DummyScene(manager, "battle")
        new_menu = DummyScene(manager, "new_menu")

        # Bouw stack op
        manager.push_scene(menu)
        manager.push_scene(overworld)
        manager.push_scene(battle)
        assert len(manager) == 3

        # Reset naar nieuw menu
        manager.clear_and_set(new_menu)
        assert manager.active_scene is new_menu
        assert len(manager) == 1
