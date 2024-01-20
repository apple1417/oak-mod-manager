from collections.abc import Iterable
from dataclasses import dataclass, field

from mods_base import (
    JSON,
    BaseOption,
    BoolOption,
    ButtonOption,
    DropdownOption,
    GroupedOption,
    KeybindOption,
    Mod,
    NestedOption,
    SliderOption,
    SpinnerOption,
    ValueOption,
)
from unrealsdk import logging

from console_mod_menu.draw import draw
from console_mod_menu.option_formatting import draw_option_header, get_option_value_str

from . import (
    AbstractScreen,
    draw_stack_header,
    draw_standard_commands,
    handle_standard_command_input,
    push_screen,
)
from .keybind import KeybindOptionScreen
from .option import BoolOptionScreen, ButtonOptionScreen, ChoiceOptionScreen, SliderOptionScreen


@dataclass
class OptionListScreen(AbstractScreen):
    mod: Mod

    drawn_options: list[BaseOption] = field(default_factory=list, init=False)

    def draw_options_list(
        self,
        options: Iterable[BaseOption],
        stack: list[GroupedOption],
    ) -> None:
        """
        Recursively draws a set of options.

        Args:
            options: An iterable of the options to draw.
            stack: The stack of `GroupedOption`s which led to the current list.
        """
        indent = len(stack)

        for option in options:
            if option.is_hidden:
                continue

            if not isinstance(option, GroupedOption):
                self.drawn_options.append(option)

            drawn_idx = len(self.drawn_options)

            match option:
                case GroupedOption() if option in stack:
                    logging.dev_warning(f"Found recursive options group, not drawing: {option}")
                case GroupedOption():
                    draw(f"{option.display_name}:", indent=indent)

                    stack.append(option)
                    self.draw_options_list(option.children, stack)
                    stack.pop()

                case ValueOption():
                    j_option: ValueOption[JSON] = option

                    draw(
                        f"[{drawn_idx}] {option.display_name} ({get_option_value_str(j_option)})",
                        indent=indent,
                    )

                case ButtonOption() | NestedOption():
                    draw(f"[{drawn_idx}] {option.display_name}", indent=indent)

                case _:
                    logging.dev_warning(f"Encountered unknown option type {type(option)}")

    def handle_option_input(self, line: str) -> bool:
        """
        Handles an input made to the options list.

        Args:
            line: The line the user submitted, with whitespace stripped.
        Returns:
            True if able to parse the line, false otherwise.
        """
        option: BaseOption
        try:
            option = self.drawn_options[int(line) - 1]
        except (ValueError, IndexError):
            return False

        match option:
            case BoolOption():
                push_screen(BoolOptionScreen(self.mod, option))
            case ButtonOption():
                push_screen(ButtonOptionScreen(self.mod, option))
            case DropdownOption() | SpinnerOption():
                push_screen(ChoiceOptionScreen(self.mod, option))
            case NestedOption():
                push_screen(NestedOptionScreen(self.mod, option))
            case SliderOption():
                push_screen(SliderOptionScreen(self.mod, option))
            case KeybindOption():
                push_screen(KeybindOptionScreen(self.mod, option))
            case _:
                logging.dev_warning(f"Encountered unknown option type {type(option)}")
        return True


@dataclass
class ModScreen(OptionListScreen):
    name: str = field(init=False)

    def __post_init__(self) -> None:
        self.name = self.mod.name

    def draw(self) -> None:  # noqa: D102
        draw_stack_header()

        self.drawn_options = []
        self.draw_options_list(self.mod.iter_display_options(), [])

        draw_standard_commands()

    def handle_input(self, line: str) -> bool:  # noqa: D102
        if handle_standard_command_input(line):
            return True

        return self.handle_option_input(line)


@dataclass
class NestedOptionScreen(OptionListScreen):
    name: str = field(init=False)
    option: NestedOption

    def __post_init__(self) -> None:
        self.name = self.option.display_name

    def draw(self) -> None:  # noqa: D102
        draw_option_header(self.option)

        self.drawn_options = []
        self.draw_options_list(self.option.children, [])

        draw_standard_commands()

    def handle_input(self, line: str) -> bool:  # noqa: D102
        if handle_standard_command_input(line):
            return True

        return self.handle_option_input(line)
