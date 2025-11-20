"""TimeSystem - dag/nacht cyclus, seizoenen, tijd management."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TimeBand(Enum):
    """Tijd van de dag volgens 2.2 Kalender & Festivals Spec."""

    DAWN = "DAWN"  # ~5:00-7:00
    DAY = "DAY"  # ~7:00-17:00
    DUSK = "DUSK"  # ~17:00-19:00
    NIGHT = "NIGHT"  # ~19:00-5:00


@dataclass
class TimeState:
    """Tijd state volgens 3.2 Time, World & Overworld Spec."""

    day_index: int = 0  # Aantal dagen sinds game start
    time_of_day: int = 420  # Minuten sinds middernacht (0-1439), start 7:00
    season_index: int = 0  # 0-3: Vasanta/Grīṣma/Śarada/Hemanta
    year_index: int = 0  # Voor later

    def get_time_band(self) -> TimeBand:
        """Bepaal de huidige time band."""
        if 300 <= self.time_of_day < 420:  # 5:00-7:00
            return TimeBand.DAWN
        elif 420 <= self.time_of_day < 1020:  # 7:00-17:00
            return TimeBand.DAY
        elif 1020 <= self.time_of_day < 1140:  # 17:00-19:00
            return TimeBand.DUSK
        else:  # 19:00-5:00
            return TimeBand.NIGHT

    def get_hour_minute(self) -> tuple[int, int]:
        """Geef uur en minuut terug."""
        hour = self.time_of_day // 60
        minute = self.time_of_day % 60
        return (hour, minute)

    def format_time(self) -> str:
        """Format tijd als string."""
        hour, minute = self.get_hour_minute()
        return f"{hour:02d}:{minute:02d}"


class TimeSystem:
    """Beheert de tijd en dag/nacht cyclus."""

    def __init__(self) -> None:
        self._state = TimeState()
        self._last_time_band: TimeBand = self._state.get_time_band()

        # Configuratie
        self._minutes_per_step: int = 1  # Hoeveel minuten per player movement
        self._minutes_per_tick: float = 0.5  # Hoeveel minuten per game tick (dt)

    def update(self, dt: float) -> None:
        """Update tijd met delta time.

        Voor Step 3 gebruiken we een simpele tick-based tijd.
        Later kan dit gekoppeld worden aan overworld movement.
        """
        # Voor nu: tijd loopt automatisch (zoals een echte klok)
        # In een echte implementatie zou dit alleen bij movement gebeuren
        minutes_to_add = self._minutes_per_tick * (dt * 60)  # Snelheid: dt * 60
        self.advance_time(int(minutes_to_add))

    def advance_time(self, minutes: int) -> None:
        """Verhoog de tijd met een aantal minuten."""
        if minutes <= 0:
            return

        self._state.time_of_day += minutes

        # Check for day rollover
        while self._state.time_of_day >= 1440:  # 24 hours
            self._state.time_of_day -= 1440
            self._state.day_index += 1
            logger.info(
                f"New day: Day {self._state.day_index + 1} " f"(Season {self._state.season_index})"
            )

        # Check for time band change
        current_band = self._state.get_time_band()
        if current_band != self._last_time_band:
            logger.info(
                f"TimeSystem: switched to {current_band.value} "
                f"(time: {self._state.format_time()})"
            )
            self._last_time_band = current_band

    def on_player_step(self) -> None:
        """Roep aan bij elke player movement step."""
        self.advance_time(self._minutes_per_step)

    @property
    def state(self) -> TimeState:
        """Huidige tijd state."""
        return self._state

    @property
    def time_band(self) -> TimeBand:
        """Huidige time band."""
        return self._state.get_time_band()

    def get_time_display(self) -> str:
        """Geef een display string voor de tijd."""
        return (
            f"Day {self._state.day_index + 1}, "
            f"{self._state.format_time()} ({self.time_band.value})"
        )

    def get_save_state(self) -> dict[str, int]:
        """Get serializable time state for saving.

        Returns
        -------
        dict[str, int]
            Time state as dict
        """
        return {
            "day_index": self._state.day_index,
            "time_of_day": self._state.time_of_day,
            "season_index": self._state.season_index,
            "year_index": self._state.year_index,
        }

    def restore_from_save(self, state_dict: dict[str, int]) -> None:
        """Restore time state from save data.

        Parameters
        ----------
        state_dict : dict[str, int]
            Time state dict from save file
        """
        self._state.day_index = state_dict.get("day_index", 0)
        self._state.time_of_day = state_dict.get("time_of_day", 420)
        self._state.season_index = state_dict.get("season_index", 0)
        self._state.year_index = state_dict.get("year_index", 0)

        # Update last time band
        self._last_time_band = self._state.get_time_band()

        logger.info(
            f"Time restored: Day {self._state.day_index + 1}, "
            f"{self._state.format_time()} ({self.time_band.value})"
        )


__all__ = ["TimeSystem", "TimeState", "TimeBand"]
