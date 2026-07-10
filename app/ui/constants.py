ICON = 'img/favicon.ico'
FONT = 'Segoe UI'
APP_NAME = 'AutomaticExcelFill'

THEME_SIDEBAR = '#18181b'
THEME_BG = '#111113'
THEME_CARD = '#1c1c1f'
THEME_CARD_BORDER = '#2e2e33'
THEME_ACCENT = '#6366f1'
THEME_ACCENT_HOVER = '#4f46e5'
THEME_ACCENT_SECONDARY = '#818cf8'
THEME_NAV_ACTIVE = '#27272a'
THEME_TEXT_SECONDARY = '#9ca3af'
THEME_PROGRESS_BG = '#1e1b4b'
THEME_ICON = '#a5b4fc'
THEME_NAV_TEXT_ACCENT = '#c7d2fe'
THEME_GRADIENT_HOVER = '#4338ca'
THEME_TABLE_ROW_A = '#1a1a1d'
THEME_TABLE_ROW_B = '#111113'
THEME_CANVAS_BG = '#28282d'
THEME_ERROR_TEXT = '#f87171'
BTN_RED = '#b91c1c'
BTN_HOVER_RED = '#7f1d1d'

DEFAULT_WIDTH = 1100
DEFAULT_HEIGHT = 700
SIDEBAR_WIDTH = 220


def apply_theme_colors(**colors: str) -> None:
    global THEME_SIDEBAR, THEME_BG, THEME_CARD, THEME_CARD_BORDER
    global THEME_ACCENT, THEME_ACCENT_HOVER, THEME_ACCENT_SECONDARY
    global THEME_NAV_ACTIVE, THEME_TEXT_SECONDARY, THEME_PROGRESS_BG
    global THEME_ICON, THEME_NAV_TEXT_ACCENT, THEME_GRADIENT_HOVER
    global THEME_TABLE_ROW_A, THEME_TABLE_ROW_B, THEME_CANVAS_BG, THEME_ERROR_TEXT
    global BTN_RED, BTN_HOVER_RED

    THEME_SIDEBAR = colors['sidebar']
    THEME_BG = colors['bg']
    THEME_CARD = colors['card']
    THEME_CARD_BORDER = colors['card_border']
    THEME_ACCENT = colors['accent']
    THEME_ACCENT_HOVER = colors['accent_hover']
    THEME_ACCENT_SECONDARY = colors['accent_secondary']
    THEME_NAV_ACTIVE = colors['nav_active']
    THEME_TEXT_SECONDARY = colors['text_secondary']
    THEME_PROGRESS_BG = colors['progress_bg']
    BTN_RED = colors['destructive']
    BTN_HOVER_RED = colors['destructive_hover']
    THEME_ICON = colors['icon']
    THEME_NAV_TEXT_ACCENT = colors['nav_text_accent']
    THEME_GRADIENT_HOVER = colors['gradient_hover']
    THEME_TABLE_ROW_A = colors['table_row_a']
    THEME_TABLE_ROW_B = colors['table_row_b']
    THEME_CANVAS_BG = colors['canvas_bg']
    THEME_ERROR_TEXT = colors['error_text']
