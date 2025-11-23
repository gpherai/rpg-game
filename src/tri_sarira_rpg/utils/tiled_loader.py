"""Tiled TMX map loader volgens 4.3 Tiled Conventions & Map Metadata Spec."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TileLayer:
    """Een tile layer uit Tiled (Ground, Objects, Collision, etc.)."""

    name: str
    width: int
    height: int
    data: list[list[int]]  # 2D array: data[y][x] = tile_gid
    visible: bool = True
    opacity: float = 1.0


@dataclass
class TiledObject:
    """Een object uit een object layer (spawn, portal, chest, event, etc.)."""

    id: int
    name: str
    type: str  # "PlayerSpawn", "Portal", "Chest", "EventTrigger", etc.
    x: int  # Pixel coords from Tiled
    y: int  # Pixel coords from Tiled
    width: int = 0
    height: int = 0
    properties: dict[str, Any] = field(default_factory=dict)

    def get_tile_coords(self, tile_size: int = 32) -> tuple[int, int]:
        """Convert pixel coords naar tile coords."""
        return (self.x // tile_size, self.y // tile_size)


@dataclass
class ObjectLayer:
    """Een object layer uit Tiled (Spawns, Portals, Chests, Events, etc.)."""

    name: str
    objects: list[TiledObject] = field(default_factory=list)
    visible: bool = True


@dataclass
class TiledMap:
    """Een volledige Tiled map (.tmx file)."""

    width: int  # Map width in tiles
    height: int  # Map height in tiles
    tile_width: int  # Tile size in pixels (should be 32)
    tile_height: int  # Tile size in pixels (should be 32)
    properties: dict[str, Any] = field(default_factory=dict)
    tile_layers: dict[str, TileLayer] = field(default_factory=dict)
    object_layers: dict[str, ObjectLayer] = field(default_factory=dict)

    def get_collision_at(self, tile_x: int, tile_y: int) -> bool:
        """Check of een tile geblokkeerd is volgens de Collision layer."""
        if "Collision" not in self.tile_layers:
            return False

        collision_layer = self.tile_layers["Collision"]

        if not (0 <= tile_y < collision_layer.height and 0 <= tile_x < collision_layer.width):
            return True  # Out of bounds = blocked

        tile_gid = collision_layer.data[tile_y][tile_x]
        return tile_gid != 0  # Any tile = blocking

    def get_spawns(self) -> list[TiledObject]:
        """Haal alle PlayerSpawn objecten op."""
        if "Spawns" not in self.object_layers:
            return []
        return [obj for obj in self.object_layers["Spawns"].objects if obj.type == "PlayerSpawn"]

    def get_default_spawn(self) -> TiledObject | None:
        """Haal de default PlayerSpawn op."""
        spawns = self.get_spawns()
        for spawn in spawns:
            if spawn.properties.get("is_default", False):
                return spawn
        # Fallback: eerste spawn
        return spawns[0] if spawns else None

    def get_spawn_by_id(self, spawn_id: str) -> TiledObject | None:
        """Zoek een PlayerSpawn op basis van spawn_id."""
        spawns = self.get_spawns()
        for spawn in spawns:
            if spawn.properties.get("spawn_id") == spawn_id:
                return spawn
        return None

    def get_portals(self) -> list[TiledObject]:
        """Haal alle Portal objecten op."""
        if "Portals" not in self.object_layers:
            return []
        return [obj for obj in self.object_layers["Portals"].objects if obj.type == "Portal"]

    def get_chests(self) -> list[TiledObject]:
        """Haal alle Chest objecten op."""
        if "Chests" not in self.object_layers:
            return []
        return [obj for obj in self.object_layers["Chests"].objects if obj.type == "Chest"]

    def get_events(self) -> list[TiledObject]:
        """Haal alle EventTrigger objecten op."""
        if "Events" not in self.object_layers:
            return []
        return [obj for obj in self.object_layers["Events"].objects if obj.type == "EventTrigger"]


class TiledLoader:
    """Laadt Tiled .tmx files."""

    def __init__(self, maps_dir: Path | None = None) -> None:
        self._maps_dir = maps_dir or Path("maps")

    def load_map(self, zone_id: str) -> TiledMap:
        """Laad een Tiled map voor een zone_id.

        Parameters
        ----------
        zone_id : str
            Zone ID, bijv. "z_r1_chandrapur_town"

        Returns
        -------
        TiledMap
            De geladen map

        Raises
        ------
        FileNotFoundError
            Als de .tmx file niet bestaat
        ValueError
            Als de TMX parsing faalt
        """
        tmx_path = self._maps_dir / f"{zone_id}.tmx"

        if not tmx_path.exists():
            raise FileNotFoundError(f"Tiled map not found: {tmx_path}")

        logger.info(f"Loading Tiled map: {tmx_path}")

        try:
            tree = ET.parse(tmx_path)
            root = tree.getroot()

            # Parse map properties
            width = int(root.get("width", "0"))
            height = int(root.get("height", "0"))
            tile_width = int(root.get("tilewidth", "32"))
            tile_height = int(root.get("tileheight", "32"))

            if tile_width != 32 or tile_height != 32:
                logger.warning(
                    f"Map {zone_id} has non-standard tile size: {tile_width}x{tile_height}"
                )

            tiled_map = TiledMap(
                width=width,
                height=height,
                tile_width=tile_width,
                tile_height=tile_height,
            )

            # Parse map-level custom properties
            properties_elem = root.find("properties")
            if properties_elem is not None:
                tiled_map.properties = self._parse_properties(
                    properties_elem, context=f"map:{zone_id}"
                )

            # Parse tile layers
            for layer_elem in root.findall("layer"):
                layer = self._parse_tile_layer(layer_elem, width, height)
                tiled_map.tile_layers[layer.name] = layer

            # Parse object layers
            for objectgroup_elem in root.findall("objectgroup"):
                object_layer = self._parse_object_layer(objectgroup_elem)
                tiled_map.object_layers[object_layer.name] = object_layer

            logger.info(
                f"✓ Loaded map {zone_id}: {width}x{height} tiles, "
                f"{len(tiled_map.tile_layers)} tile layers, "
                f"{len(tiled_map.object_layers)} object layers"
            )

            return tiled_map

        except ET.ParseError as e:
            raise ValueError(f"Invalid TMX file {tmx_path}: {e}") from e
        except Exception as e:
            logger.error(f"Error loading Tiled map {tmx_path}: {e}")
            raise

    def _parse_properties(
        self, properties_elem: ET.Element, context: str = ""
    ) -> dict[str, Any]:
        """Parse custom properties uit een <properties> element.

        Parameters
        ----------
        properties_elem : ET.Element
            Het <properties> XML element.
        context : str
            Extra context voor logging (bijv. object naam/id of layer naam).
        """
        props = {}
        ctx_prefix = f"[{context}] " if context else ""

        for prop_elem in properties_elem.findall("property"):
            name = prop_elem.get("name", "")
            value = prop_elem.get("value", "")
            prop_type = prop_elem.get("type", "string")

            # Type conversie
            if prop_type == "int":
                try:
                    props[name] = int(value)
                except ValueError:
                    logger.warning(
                        "%sInvalid int property '%s' with value '%s', using 0",
                        ctx_prefix, name, value
                    )
                    props[name] = 0
            elif prop_type == "float":
                try:
                    props[name] = float(value)
                except ValueError:
                    logger.warning(
                        "%sInvalid float property '%s' with value '%s', using 0.0",
                        ctx_prefix, name, value
                    )
                    props[name] = 0.0
            elif prop_type == "bool":
                props[name] = value.lower() == "true"
            else:
                props[name] = value

        return props

    def _parse_tile_layer(
        self, layer_elem: ET.Element, map_width: int, map_height: int
    ) -> TileLayer:
        """Parse een tile layer (<layer> element)."""
        name = layer_elem.get("name", "Unknown")
        visible = layer_elem.get("visible", "1") == "1"
        opacity = float(layer_elem.get("opacity", "1"))

        # Parse tile data
        data_elem = layer_elem.find("data")
        if data_elem is None:
            raise ValueError(f"Layer {name} has no <data> element")

        encoding = data_elem.get("encoding", "")
        if encoding != "csv":
            raise ValueError(
                f"Layer {name} uses unsupported encoding '{encoding}'. "
                "Only CSV encoding is supported."
            )

        # Parse CSV data
        csv_text = data_elem.text or ""
        csv_values = [int(v.strip()) for v in csv_text.strip().split(",") if v.strip()]

        # Convert 1D list to 2D array
        data_2d: list[list[int]] = []
        for y in range(map_height):
            row = []
            for x in range(map_width):
                idx = y * map_width + x
                if idx < len(csv_values):
                    row.append(csv_values[idx])
                else:
                    row.append(0)
            data_2d.append(row)

        return TileLayer(
            name=name,
            width=map_width,
            height=map_height,
            data=data_2d,
            visible=visible,
            opacity=opacity,
        )

    def _parse_object_layer(self, objectgroup_elem: ET.Element) -> ObjectLayer:
        """Parse een object layer (<objectgroup> element)."""
        name = objectgroup_elem.get("name", "Unknown")
        visible = objectgroup_elem.get("visible", "1") == "1"

        objects = []
        for obj_elem in objectgroup_elem.findall("object"):
            obj_id = int(obj_elem.get("id", "0"))
            obj_name = obj_elem.get("name", "")
            obj_type = obj_elem.get("type", "")
            x = int(float(obj_elem.get("x", "0")))
            y = int(float(obj_elem.get("y", "0")))
            width = int(float(obj_elem.get("width", "0")))
            height = int(float(obj_elem.get("height", "0")))

            # Parse object properties
            properties = {}
            properties_elem = obj_elem.find("properties")
            if properties_elem is not None:
                obj_context = f"{obj_type}:{obj_name}" if obj_name else f"{obj_type}:id={obj_id}"
                properties = self._parse_properties(properties_elem, context=obj_context)

            tiled_obj = TiledObject(
                id=obj_id,
                name=obj_name,
                type=obj_type,
                x=x,
                y=y,
                width=width,
                height=height,
                properties=properties,
            )
            objects.append(tiled_obj)

        return ObjectLayer(name=name, objects=objects, visible=visible)


__all__ = ["TiledMap", "TileLayer", "TiledObject", "ObjectLayer", "TiledLoader"]
