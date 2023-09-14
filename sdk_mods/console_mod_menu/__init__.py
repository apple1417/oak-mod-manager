import argparse

from mods_base import Game, Library, build_mod, command

from .menu_loop import start_interactive_menu

__all__: list[str] = [
    "__version__",
    "__version_info__",
]

__version_info__: tuple[int, int] = (1, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"


@command("mods", description="Opens the console mod menu.")
def mods_command(_: argparse.Namespace) -> None:
    start_interactive_menu()


mods_command.add_argument("-v", "--version", action="version", version=__version__)

build_mod(
    cls=Library,
    name="Console Mod Menu",
    author="bl-sdk",
    description="Adds a console-based mod menu. Type 'mods' to get started.",
    supported_games=Game.BL3,
    keybinds=[],
    options=[],
    hooks=[],
    commands=[mods_command],
    on_enable=lambda: print("Console Mod Menu loaded. Type 'mods' to get started."),
)