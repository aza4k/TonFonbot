from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.locales import get_text
from typing import List

def main_menu_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """
    Main Keyboard for TonFonBot interaction.
    """
    keyboard = [
        [
            InlineKeyboardButton(text=get_text("btn_price", lang), callback_data="cmd_price"),
            InlineKeyboardButton(text=get_text("btn_chart", lang), callback_data="cmd_chart")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_forecast", lang), callback_data="cmd_forecast")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_channels", lang), callback_data="cmd_channels")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_settings", lang), callback_data="cmd_settings"),
            InlineKeyboardButton(text=get_text("btn_about", lang), callback_data="info_about")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_to_main_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """
    Back button to return to the main menu.
    """
    keyboard = [
        [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="nav_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def settings_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """
    Settings menu.
    """
    keyboard = [
        [InlineKeyboardButton(text=get_text("btn_lang", lang), callback_data="set_lang")],
        [InlineKeyboardButton(text=get_text("btn_contact", lang), callback_data="set_contact")],
        [InlineKeyboardButton(text=get_text("btn_back_settings", lang), callback_data="nav_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cancel_kb(lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=get_text("btn_cancel", lang), callback_data="nav_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def language_selection_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """
    Language selection menu.
    """
    keyboard = [
        [InlineKeyboardButton(text=get_text("btn_lang_en", lang), callback_data="lang_en")],
        [InlineKeyboardButton(text=get_text("btn_lang_ru", lang), callback_data="lang_ru")],
        [InlineKeyboardButton(text=get_text("btn_lang_uz", lang), callback_data="lang_uz")],
        [InlineKeyboardButton(text=get_text("btn_back_settings", lang), callback_data="cmd_settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- Channel Management Keyboards ---

def channels_list_kb(channels: List, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Shows user's linked channels with add button.
    """
    keyboard = []
    for ch in channels:
        keyboard.append([
            InlineKeyboardButton(text=f"📢 @{ch.channel_username}", callback_data=f"ch_manage_{ch.id}")
        ])
    keyboard.append([InlineKeyboardButton(text=get_text("btn_add_channel", lang), callback_data="ch_add")])
    keyboard.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="nav_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def channel_manage_kb(channel, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Channel settings: toggle price/news, set intervals/lang, delete.
    """
    price_status = get_text("status_on", lang) if channel.price_enabled else get_text("status_off", lang)
    news_status = get_text("status_on", lang) if channel.news_enabled else get_text("status_off", lang)
    
    keyboard = [
        [InlineKeyboardButton(
            text=get_text("btn_toggle_price", lang, status=price_status), 
            callback_data=f"ch_price_{channel.id}"
        )],
    ]
    
    if channel.price_enabled:
        keyboard.append([InlineKeyboardButton(
            text=get_text("btn_price_interval", lang, interval=channel.price_interval),
            callback_data=f"ch_interval_{channel.id}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text=get_text("btn_toggle_news", lang, status=news_status),
        callback_data=f"ch_news_{channel.id}"
    )])
    
    if channel.news_enabled:
        lang_display = {"en": "🇬🇧 EN", "ru": "🇷🇺 RU", "uz": "🇺🇿 UZ"}.get(channel.news_language, channel.news_language)
        keyboard.append([InlineKeyboardButton(
            text=get_text("btn_news_lang", lang, language=lang_display),
            callback_data=f"ch_newslang_{channel.id}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text=get_text("btn_delete_channel", lang),
        callback_data=f"ch_delete_{channel.id}"
    )])
    keyboard.append([InlineKeyboardButton(text=get_text("btn_back", lang), callback_data="cmd_channels")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def price_interval_kb(channel_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Select price update interval.
    """
    keyboard = [
        [InlineKeyboardButton(text=get_text("btn_interval_1", lang), callback_data=f"ch_setint_{channel_id}_1")],
        [InlineKeyboardButton(text=get_text("btn_interval_5", lang), callback_data=f"ch_setint_{channel_id}_5")],
        [InlineKeyboardButton(text=get_text("btn_interval_10", lang), callback_data=f"ch_setint_{channel_id}_10")],
        [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=f"ch_manage_{channel_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def news_lang_kb(channel_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Select news language for channel.
    """
    keyboard = [
        [InlineKeyboardButton(text=get_text("btn_lang_en", lang), callback_data=f"ch_setnewslang_{channel_id}_en")],
        [InlineKeyboardButton(text=get_text("btn_lang_ru", lang), callback_data=f"ch_setnewslang_{channel_id}_ru")],
        [InlineKeyboardButton(text=get_text("btn_lang_uz", lang), callback_data=f"ch_setnewslang_{channel_id}_uz")],
        [InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=f"ch_manage_{channel_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

