"""Applicatie-entrypoint."""

from __future__ import annotations

from tri_sarira_rpg.app.game import Game
from tri_sarira_rpg.core.logging_setup import configure_logging


def main() -> None:
    """Start de game met een eenvoudige bootstrap."""

    configure_logging()
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
