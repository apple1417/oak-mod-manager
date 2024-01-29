from mods_base.mod_list import base_mod

from .hud_message import show_hud_message

__all__: tuple[str, ...] = ("__author__", "__version__", "__version_info__", "show_hud_message")

__version_info__: tuple[int, int] = (1, 1)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"
__author__: str = "bl-sdk"


base_mod.components.append(base_mod.ComponentInfo("UI Utils", __version__))
