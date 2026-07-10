"""Tema ttk alinhado ao preset ArtemiS."""

from tkinter import ttk

from app.ui.constants import (
    FONT,
    THEME_ACCENT,
    THEME_BG,
    THEME_CARD,
    THEME_CARD_BORDER,
    THEME_NAV_ACTIVE,
    THEME_TEXT_SECONDARY,
)

ARTEMIS_TREEVIEW_STYLE = 'ArtemiS.Treeview'
ARTEMIS_SCROLLBAR_V_STYLE = 'ArtemiS.Vertical.TScrollbar'

_CONFIGURED_ROOTS: set[int] = set()


def _configure_treeview_style(style: ttk.Style, style_name: str) -> None:
    heading_style = f'{style_name}.Heading'
    style.configure(
        style_name,
        background=THEME_BG,
        foreground=THEME_TEXT_SECONDARY,
        fieldbackground=THEME_BG,
        bordercolor=THEME_CARD_BORDER,
        lightcolor=THEME_CARD_BORDER,
        darkcolor=THEME_CARD_BORDER,
        rowheight=26,
        font=(FONT, 10),
    )
    style.map(
        style_name,
        background=[('selected', THEME_ACCENT)],
        foreground=[('selected', 'white')],
    )
    style.configure(
        heading_style,
        background=THEME_CARD,
        foreground='white',
        relief='flat',
        borderwidth=0,
        font=(FONT, 10, 'bold'),
    )
    style.map(heading_style, background=[('active', THEME_NAV_ACTIVE)])


def _configure_scrollbar_style(style: ttk.Style, style_name: str) -> None:
    style.configure(
        style_name,
        background=THEME_CARD_BORDER,
        troughcolor=THEME_BG,
        bordercolor=THEME_BG,
        darkcolor=THEME_BG,
        lightcolor=THEME_BG,
        arrowcolor=THEME_TEXT_SECONDARY,
        relief='flat',
        gripcount=0,
    )
    style.map(
        style_name,
        background=[('active', THEME_ACCENT), ('!active', THEME_CARD_BORDER)],
        arrowcolor=[('active', 'white'), ('!active', THEME_TEXT_SECONDARY)],
    )


def apply_artemis_ttk_theme(tk_root) -> None:
    root_id = id(tk_root)
    if root_id in _CONFIGURED_ROOTS:
        return
    try:
        style = ttk.Style(tk_root)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        for name in (ARTEMIS_TREEVIEW_STYLE, 'Treeview'):
            _configure_treeview_style(style, name)
        _configure_scrollbar_style(style, ARTEMIS_SCROLLBAR_V_STYLE)
        _CONFIGURED_ROOTS.add(root_id)
    except Exception:
        pass
