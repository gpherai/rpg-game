"""OverworldScene - map rendering, player movement, overworld gameplay."""

from __future__ import annotations

import logging

import pygame

from tri_sarira_rpg.core.scene import Scene, SceneManager
from tri_sarira_rpg.systems.time import TimeSystem
from tri_sarira_rpg.systems.world import WorldSystem

logger = logging.getLogger(__name__)


class OverworldScene(Scene):
    """Overworld scene met map rendering en player movement."""

    def __init__(
        self, manager: SceneManager, world_system: WorldSystem, time_system: TimeSystem
    ) -> None:
        super().__init__(manager)
        self._world = world_system
        self._time = time_system

        # Get screen resolution dynamically
        screen = pygame.display.get_surface()
        if screen:
            self._screen_width, self._screen_height = screen.get_size()
        else:
            # Fallback to default resolution if no surface exists yet
            self._screen_width, self._screen_height = 1280, 720

        # Movement timing (tile-based)
        self._move_cooldown: float = 0.0
        self._move_delay: float = 0.15  # Seconds between moves

        # Camera (simple follow)
        self._camera_x: int = 0
        self._camera_y: int = 0

        # Fonts for HUD
        pygame.font.init()
        self._font = pygame.font.SysFont("monospace", 16)
        self._font_large = pygame.font.SysFont("monospace", 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Verwerk input events."""
        if event.type == pygame.KEYDOWN:
            # Interact key
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                self._world.interact()

    def update(self, dt: float) -> None:
        """Update overworld logic."""
        # Update time system
        self._time.update(dt)

        # Update move cooldown
        if self._move_cooldown > 0:
            self._move_cooldown -= dt

        # Handle movement input
        if self._move_cooldown <= 0:
            keys = pygame.key.get_pressed()

            dx, dy = 0, 0

            # WASD / Arrow keys
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy = -1
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy = 1
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -1
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = 1

            if dx != 0 or dy != 0:
                # Try to move
                moved = self._world.move_player(dx, dy)
                if moved:
                    self._move_cooldown = self._move_delay
                    # Advance time on movement
                    self._time.on_player_step()

        # Update camera to follow player
        self._update_camera()

    def render(self, surface: pygame.Surface) -> None:
        """Render de overworld."""
        # Clear screen
        surface.fill((20, 20, 30))  # Dark blue background

        # Render map
        self._render_map(surface)

        # Render player
        self._render_player(surface)

        # Render HUD
        self._render_hud(surface)

    def _update_camera(self) -> None:
        """Update camera om player te volgen."""
        if not self._world.player or not self._world.current_map:
            return

        player = self._world.player
        tiled_map = self._world.current_map

        # Center camera on player
        screen_center_x = self._screen_width // 2
        screen_center_y = self._screen_height // 2

        tile_size = tiled_map.tile_width

        # Calculate camera position (top-left corner in pixels)
        self._camera_x = (player.position.x * tile_size) - screen_center_x
        self._camera_y = (player.position.y * tile_size) - screen_center_y

        # Clamp camera to map bounds
        max_camera_x = (tiled_map.width * tile_size) - self._screen_width
        max_camera_y = (tiled_map.height * tile_size) - self._screen_height

        self._camera_x = max(0, min(self._camera_x, max(0, max_camera_x)))
        self._camera_y = max(0, min(self._camera_y, max(0, max_camera_y)))

    def _render_map(self, surface: pygame.Surface) -> None:
        """Render de Tiled map."""
        tiled_map = self._world.current_map
        if not tiled_map:
            # No map loaded, show placeholder
            text = self._font_large.render("No map loaded", True, (255, 255, 255))
            surface.blit(text, (400, 300))
            return

        tile_size = tiled_map.tile_width

        # Calculate visible tile range
        start_tile_x = max(0, self._camera_x // tile_size)
        start_tile_y = max(0, self._camera_y // tile_size)
        end_tile_x = min(tiled_map.width, (self._camera_x + self._screen_width) // tile_size + 1)
        end_tile_y = min(tiled_map.height, (self._camera_y + self._screen_height) // tile_size + 1)

        # Render tile layers (simplified placeholder rendering)
        # In a real implementation, we'd load tilesets and render actual tiles
        # For Step 3, we'll render colored rectangles based on collision

        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                screen_x = (x * tile_size) - self._camera_x
                screen_y = (y * tile_size) - self._camera_y

                # Check collision for color
                is_blocked = tiled_map.get_collision_at(x, y)

                if is_blocked:
                    # Blocked tile: dark gray
                    color = (60, 60, 60)
                else:
                    # Walkable tile: light green
                    color = (100, 150, 100)

                pygame.draw.rect(
                    surface, color, (screen_x, screen_y, tile_size, tile_size)
                )

                # Draw grid lines
                pygame.draw.rect(
                    surface,
                    (40, 40, 40),
                    (screen_x, screen_y, tile_size, tile_size),
                    1,
                )

        # Render portals (for debugging)
        for portal in tiled_map.get_portals():
            portal_x, portal_y = portal.get_tile_coords(tile_size)
            screen_x = (portal_x * tile_size) - self._camera_x
            screen_y = (portal_y * tile_size) - self._camera_y

            # Draw portal as yellow rectangle
            pygame.draw.rect(
                surface,
                (255, 255, 0),
                (screen_x, screen_y, tile_size, tile_size),
                3,
            )

        # Render chests (for debugging)
        for chest in tiled_map.get_chests():
            chest_x, chest_y = chest.get_tile_coords(tile_size)
            screen_x = (chest_x * tile_size) - self._camera_x
            screen_y = (chest_y * tile_size) - self._camera_y

            # Draw chest as brown rectangle
            pygame.draw.rect(
                surface,
                (150, 100, 50),
                (screen_x + 4, screen_y + 4, tile_size - 8, tile_size - 8),
            )

    def _render_player(self, surface: pygame.Surface) -> None:
        """Render de speler."""
        player = self._world.player
        if not player or not self._world.current_map:
            return

        tile_size = self._world.current_map.tile_width

        screen_x = (player.position.x * tile_size) - self._camera_x
        screen_y = (player.position.y * tile_size) - self._camera_y

        # Draw player as blue circle
        center_x = screen_x + tile_size // 2
        center_y = screen_y + tile_size // 2
        radius = tile_size // 3

        pygame.draw.circle(surface, (100, 150, 255), (center_x, center_y), radius)

        # Draw direction indicator
        facing_offset = {
            "N": (0, -radius),
            "S": (0, radius),
            "E": (radius, 0),
            "W": (-radius, 0),
        }
        dx, dy = facing_offset.get(player.facing, (0, 0))
        pygame.draw.circle(
            surface, (255, 255, 255), (center_x + dx, center_y + dy), radius // 3
        )

    def _render_hud(self, surface: pygame.Surface) -> None:
        """Render HUD met zone info en tijd."""
        # Draw semi-transparent background for HUD
        hud_bg = pygame.Surface((self._screen_width, 60), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 180))
        surface.blit(hud_bg, (0, 0))

        # Zone name
        zone_name = self._world.get_zone_name()
        zone_text = self._font_large.render(zone_name, True, (255, 255, 255))
        surface.blit(zone_text, (20, 15))

        # Time display
        time_display = self._time.get_time_display()
        time_text = self._font.render(time_display, True, (200, 200, 200))
        surface.blit(time_text, (20, 40))

        # Player position (debug info)
        if self._world.player:
            pos_text = self._font.render(
                f"Pos: ({self._world.player.position.x}, {self._world.player.position.y})",
                True,
                (150, 150, 150),
            )
            surface.blit(pos_text, (self._screen_width - 280, 40))

        # Controls hint
        controls_bg = pygame.Surface((300, 80), pygame.SRCALPHA)
        controls_bg.fill((0, 0, 0, 180))
        surface.blit(controls_bg, (self._screen_width - 300, self._screen_height - 80))

        controls_lines = [
            "Controls:",
            "WASD/Arrows: Move",
            "Space/E: Interact",
        ]
        for i, line in enumerate(controls_lines):
            text = self._font.render(line, True, (200, 200, 200))
            surface.blit(text, (self._screen_width - 290, self._screen_height - 75 + i * 20))


__all__ = ["OverworldScene"]
