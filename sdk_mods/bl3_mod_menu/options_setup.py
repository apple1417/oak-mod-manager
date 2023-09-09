import functools
from collections.abc import Sequence

from mods_base import (
    BaseOption,
    BoolOption,
    ButtonOption,
    DropdownOption,
    GroupedOption,
    KeybindOption,
    Mod,
    SliderOption,
    SpinnerOption,
)
from unrealsdk import logging
from unrealsdk.unreal import UObject

from .keybinds import add_keybind_option
from .native.options_setup import (
    add_bool_spinner,
    add_button,
    add_dropdown,
    add_slider,
    add_spinner,
    add_title,
)
from .native.options_transition import open_custom_options, refresh_options

# The mod we're currently displaying, or None if not in a custom options menu
open_mod: Mod | None = None

# The options which we drew last time we updated one of our options menus
last_drawn_options: list[BaseOption] = []


def on_options_close() -> None:
    """Callback to be run when the options menu is closed."""
    global open_mod
    open_mod = None


def is_options_menu_open() -> bool:
    """
    Checks if a custom options menu is open.

    Returns:
        True if the options menu is open.
    """
    return open_mod is not None


def draw_options(
    self: UObject,
    options: Sequence[BaseOption],
    group_stack: list[GroupedOption],
) -> None:
    """
    Recursively draws a set of options.

    Args:
        self: The options menu being drawn.
        options: A list of the options to draw.
        group_stack: The stack of `GroupedOption`s which led to this list being drawn.
    """
    for idx, option in enumerate(options):
        if option.is_hidden:
            continue

        # Grouped options are a little more complex, it handles this manually
        if not isinstance(option, GroupedOption):
            last_drawn_options.append(option)

        match option:
            case ButtonOption():
                add_button(self, option.name, option.description_title, option.description)

            case BoolOption():
                add_bool_spinner(
                    self,
                    option.name,
                    option.value,
                    option.true_text,
                    option.false_text,
                    option.description_title,
                    option.description,
                )

            case DropdownOption():
                add_dropdown(
                    self,
                    option.name,
                    option.choices.index(option.value),
                    option.choices,
                    option.description_title,
                    option.description,
                )

            case SliderOption():
                add_slider(
                    self,
                    option.name,
                    option.value,
                    option.min_value,
                    option.max_value,
                    option.step,
                    option.is_integer,
                    option.description_title,
                    option.description,
                )

            case SpinnerOption():
                add_spinner(
                    self,
                    option.name,
                    option.choices.index(option.value),
                    option.choices,
                    option.wrap_enabled,
                    option.description_title,
                    option.description,
                )

            case KeybindOption():
                add_keybind_option(self, option)

            case GroupedOption() if option in group_stack:
                logging.dev_warning(f"Found recursive options group, not drawing: {option}")
            case GroupedOption():
                group_stack.append(option)

                # If the first entry of the group is another group, don't draw a title, let the
                # nested call do it, so the first title is the most nested
                # If we're empty, or a different type, draw our own header
                if len(option.children) == 0 or not isinstance(option.children[0], GroupedOption):
                    add_title(self, " - ".join(g.name for g in group_stack))
                    last_drawn_options.append(option)

                draw_options(self, option.children, group_stack)

                group_stack.pop()

                # If we have more options left in this group, and we're not immediately followed by
                # another group, re-draw the base header
                if idx != len(options) - 1 and not isinstance(options[idx + 1], GroupedOption):
                    # This will print an empty string if we're on the last stack - which is about
                    # the best we can do, we still want a gap
                    add_title(self, " - ".join(g.name for g in group_stack))
                    last_drawn_options.append(option)

            case _:
                logging.dev_warning(f"Encountered unknown option type {type(option)}")


def setup_options_for_mod(mod: Mod, self: UObject) -> None:
    """
    Sets up the options menu for a given mod.

    Intended to be passed to one of the option transition functions behind a functools.partial.

    Args:
        mod: The mod to setup options for.
        self: The options menu being drawn.
    """
    global open_mod, last_drawn_options
    last_drawn_options.clear()
    open_mod = mod

    draw_options(self, tuple(mod.iter_display_options()), [])


def open_options_menu(main_menu: UObject, mod: Mod) -> None:
    """
    Opens the options menu for a particular mod.

    Args:
        main_menu: The main menu to open under.
        mod: The mod to open the options for.
    """
    open_custom_options(main_menu, mod.name, functools.partial(setup_options_for_mod, mod))


def refresh_options_menu(options_menu: UObject, preserve_scroll: bool = True) -> None:
    """
    Refreshes the currently open options menu.

    Args:
        options_menu: The current options menu.
        preserve_scroll: If true, preserves the current scroll position.
    """
    if open_mod is None:
        raise RuntimeError("Tried to refresh a mod options screen without having an associated mod")

    refresh_options(
        options_menu,
        functools.partial(setup_options_for_mod, open_mod),
        preserve_scroll,
    )