import os
from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import BufferedInputFile, FSInputFile, InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy import select, update
from loguru import logger
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

import re

# Services
from src.database.core import async_session_maker, User, Channel
from src.services.price_monitor import PriceMonitor
from src.services.chart_generator import ChartGenerator
from src.services.ai_analyst import AIAnalyst
from src.services.token_scanner import TokenScanner
from src.services.stats_generator import StatsGenerator
from src.bot.keyboards import (
    main_menu_kb, back_to_main_kb, settings_kb, cancel_kb, language_selection_kb,
    channels_list_kb, channel_manage_kb, price_interval_kb, news_lang_kb
)
from aiogram.fsm.context import FSMContext
from src.bot.states import ContactAdminStates, AddChannelStates, TokenAuditStates
from src.config import config
from src.locales import get_text


router = Router()

# Dependency Injection placeholders
price_monitor: PriceMonitor = None
chart_generator: ChartGenerator = None
ai_analyst: AIAnalyst = None
token_scanner: TokenScanner = None
stats_generator: StatsGenerator = None

# TON Address regex pattern (EQ... or UQ...)
TON_ADDRESS_PATTERN = re.compile(r'^[EU]Q[A-Za-z0-9_-]{46}$')

# --- Helpers ---
async def get_or_create_user(telegram_id: int) -> User:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

async def get_user_lang(telegram_id: int) -> str:
    """Get user's preferred language code."""
    async with async_session_maker() as session:
        result = await session.execute(select(User.language_code).where(User.telegram_id == telegram_id))
        lang = result.scalar_one_or_none()
        return lang if lang else "en"

async def set_user_lang(telegram_id: int, lang_code: str):
    """Update user's preferred language."""
    async with async_session_maker() as session:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(language_code=lang_code)
        )
        await session.commit()

async def send_welcome(target: types.Message | types.CallbackQuery, lang: str = "en"):
    """Unified welcome message sender."""
    text = f"<b>{get_text('welcome_title', lang)}</b>\n\n{get_text('welcome_body', lang)}"
    
    logo_path = "assets/logo1.gif"
    has_logo = os.path.exists(logo_path)
    
    if isinstance(target, types.Message):
        if has_logo:
            animation = FSInputFile(logo_path)
            await target.answer_animation(animation, caption=text, reply_markup=main_menu_kb(lang), parse_mode="HTML")
        else:
            await target.answer(text, reply_markup=main_menu_kb(lang), parse_mode="HTML")
            
    elif isinstance(target, types.CallbackQuery):
        if target.message.animation:
            await target.message.edit_caption(caption=text, reply_markup=main_menu_kb(lang), parse_mode="HTML")
        else:
            if has_logo:
                await target.message.delete()
                animation = FSInputFile(logo_path)
                await target.message.answer_animation(animation, caption=text, reply_markup=main_menu_kb(lang), parse_mode="HTML")
            else:
                await target.message.edit_text(text, reply_markup=main_menu_kb(lang), parse_mode="HTML")

# --- Commands ---

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await get_or_create_user(message.from_user.id)
    lang = await get_user_lang(message.from_user.id)
    await send_welcome(message, lang)

# --- Callbacks ---

@router.callback_query(F.data == "nav_main")
async def nav_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await get_user_lang(callback.from_user.id)
    await send_welcome(callback, lang)
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data == "cmd_price")
async def cb_price(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    
    if not price_monitor:
        await callback.answer(get_text("service_unavailable", lang), show_alert=True)
        return
        
    price = await price_monitor.fetch_price()
    if price:
        text = get_text("price_live", lang).replace("{price:.4f}", f"{price:.4f}")
    else:
        text = get_text("price_error", lang)
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=back_to_main_kb(lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=back_to_main_kb(lang), parse_mode="HTML")
        
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data == "cmd_chart")
async def cb_chart(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    
    if not chart_generator:
        await callback.answer(get_text("chart_unavailable", lang), show_alert=True)
        return
        
    await callback.answer(get_text("chart_generating", lang))

    buf = await chart_generator.generate_chart()
    if buf:
        chart_file = BufferedInputFile(buf.read(), filename="chart.png")
        media = types.InputMediaPhoto(media=chart_file, caption=get_text("chart_title", lang), parse_mode="HTML")
        
        try:
            await callback.message.edit_media(media=media, reply_markup=back_to_main_kb(lang))
        except Exception:
            await callback.message.delete()
            await callback.message.answer_photo(chart_file, caption=get_text("chart_title", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
    else:
        error_msg = get_text("chart_error", lang)
        if callback.message.photo or callback.message.animation:
            await callback.message.edit_caption(caption=error_msg, reply_markup=back_to_main_kb(lang))
        else:
            await callback.message.edit_text(error_msg, reply_markup=back_to_main_kb(lang))

@router.callback_query(F.data == "cmd_stats")
async def cb_stats(callback: types.CallbackQuery):
    """Generate and send market statistics image."""
    lang = await get_user_lang(callback.from_user.id)
    
    if not stats_generator:
        await callback.answer(get_text("stats_unavailable", lang), show_alert=True)
        return
    
    await callback.answer(get_text("stats_generating", lang))
    
    buf = await stats_generator.generate_image()
    if buf:
        stats_file = BufferedInputFile(buf.read(), filename="stat.png")
        media = types.InputMediaPhoto(media=stats_file, caption=get_text("stats_title", lang), parse_mode="HTML")
        
        try:
            await callback.message.edit_media(media=media, reply_markup=back_to_main_kb(lang))
        except Exception:
            await callback.message.delete()
            await callback.message.answer_photo(stats_file, caption=get_text("stats_title", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
    else:
        error_msg = get_text("stats_error", lang)
        if callback.message.photo or callback.message.animation:
            await callback.message.edit_caption(caption=error_msg, reply_markup=back_to_main_kb(lang))
        else:
            await callback.message.edit_text(error_msg, reply_markup=back_to_main_kb(lang))

@router.callback_query(F.data == "cmd_forecast")
async def cb_forecast(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    await callback.answer(get_text("forecast_loading", lang))
    
    if not ai_analyst or not price_monitor:
        msg = get_text("forecast_error", lang)
        if callback.message.photo or callback.message.animation:
            await callback.message.edit_caption(caption=msg, reply_markup=back_to_main_kb(lang))
        else:
            await callback.message.edit_text(msg, reply_markup=back_to_main_kb(lang))
        return

    try:
        # Try to get cached forecast first
        forecast_dict = await ai_analyst.get_latest_forecast()
        
        if not forecast_dict:
            # Fallback to generation if missing
            current_price = await price_monitor.fetch_price()
            market_data_str = f"Current TON Price: ${current_price}" if current_price else "Price data unavailable."
            forecast_dict = await ai_analyst.generate_daily_forecast(market_data_str)
            
        forecast = forecast_dict.get(lang, forecast_dict.get('en', 'No forecast available.'))
        forecast += "\n\n🤖 <i>Analyzed by @TonFonBot</i>"
        
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        forecast = get_text("forecast_unavailable", lang)
    
    response = f"{get_text('forecast_title', lang)}\n\n{forecast}"

    
    if callback.message.photo or callback.message.animation:
        if len(response) > 1000:
            response = response[:1000] + "..."
        await callback.message.edit_caption(caption=response, reply_markup=back_to_main_kb(lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(response, reply_markup=back_to_main_kb(lang), parse_mode="HTML")

@router.callback_query(F.data == "cmd_audit")
async def cb_audit(callback: types.CallbackQuery, state: FSMContext):
    """Handle Check Token button - prompt user for address."""
    lang = await get_user_lang(callback.from_user.id)
    text = get_text("audit_prompt", lang)
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=cancel_kb(lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=cancel_kb(lang), parse_mode="HTML")
    
    await state.set_state(TokenAuditStates.waiting_for_address)
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.message(TokenAuditStates.waiting_for_address)
async def handle_audit_address(message: types.Message, state: FSMContext):
    """Process token address submitted via Check Token button."""
    lang = await get_user_lang(message.from_user.id)
    text = message.text.strip()
    
    # Validate address format
    if not TON_ADDRESS_PATTERN.match(text):
        await message.answer(get_text("audit_invalid", lang), reply_markup=cancel_kb(lang), parse_mode="HTML")
        return
    
    await state.clear()
    
    if not token_scanner:
        await message.answer(get_text("audit_unavailable", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
        return
    
    status_msg = await message.answer(get_text("audit_scanning", lang), parse_mode="HTML")
    
    try:
        token_data = await token_scanner.scan_token(text)
        
        if not token_data:
            await status_msg.edit_text(get_text("audit_not_found", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
            return
        
        analysis = token_scanner.analyze_security(token_data)
        report = token_scanner.format_audit_report(analysis, lang)
        await status_msg.edit_text(report, reply_markup=back_to_main_kb(lang), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Token audit error: {e}")
        await status_msg.edit_text(get_text("audit_error", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")

@router.callback_query(F.data == "cmd_settings")
async def cb_settings(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    text = f"{get_text('settings_title', lang)}\n\n{get_text('settings_body', lang)}"
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=settings_kb(lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=settings_kb(lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data == "set_lang")
async def cb_set_lang(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    text = f"{get_text('lang_select_title', lang)}\n\n{get_text('lang_select_body', lang)}"
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=language_selection_kb(lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=language_selection_kb(lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data.startswith("lang_"))
async def cb_lang_selected(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]  # lang_en -> en
    await set_user_lang(callback.from_user.id, new_lang)
    
    # Show confirmation
    text = get_text("lang_changed", new_lang)
    await callback.answer(text, show_alert=True)
    
    # Refresh to settings with new language
    settings_text = f"{get_text('settings_title', new_lang)}\n\n{get_text('settings_body', new_lang)}"
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=settings_text, reply_markup=settings_kb(new_lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(settings_text, reply_markup=settings_kb(new_lang), parse_mode="HTML")

@router.callback_query(F.data == "set_contact")
async def cb_contact(callback: types.CallbackQuery, state: FSMContext):
    lang = await get_user_lang(callback.from_user.id)
    text = f"{get_text('contact_title', lang)}\n\n{get_text('contact_body', lang)}"
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=cancel_kb(lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=cancel_kb(lang), parse_mode="HTML")
    
    await state.set_state(ContactAdminStates.waiting_for_message)
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.message(ContactAdminStates.waiting_for_message)
async def handle_admin_message(message: types.Message, state: FSMContext, bot: Bot = None):
    lang = await get_user_lang(message.from_user.id)
    bot_instance = message.bot or bot
    
    user_info = f"User: {message.from_user.full_name} (@{message.from_user.username}) [ID:{message.from_user.id}]"
    text_to_admin = f"📨 <b>New Message from User</b>\n{user_info}\n\n{message.text}"
    
    count = 0
    if config.ADMIN_IDS:
        for admin_id in config.ADMIN_IDS:
            try:
                await bot_instance.send_message(chat_id=admin_id, text=text_to_admin, parse_mode="HTML")
                count += 1
            except Exception as e:
                logger.error(f"Failed to send to admin {admin_id}: {e}")
    
    await state.clear()
    await message.answer(get_text("contact_sent", lang, count=count), reply_markup=back_to_main_kb(lang), parse_mode="HTML")

@router.callback_query(F.data == "info_about")
async def cb_about(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    text = f"{get_text('instruction_title', lang)}\n\n{get_text('instruction_body', lang)}"
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=back_to_main_kb(lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=back_to_main_kb(lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

# ===================== CHANNEL MANAGEMENT =====================

@router.callback_query(F.data == "cmd_channels")
async def cb_channels(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Channel).where(Channel.owner_telegram_id == callback.from_user.id)
        )
        channels = result.scalars().all()
    
    if channels:
        text = f"{get_text('channels_title', lang)}\n\n{get_text('channels_list', lang)}"
    else:
        text = f"{get_text('channels_title', lang)}\n\n{get_text('channels_empty', lang)}"
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=channels_list_kb(channels, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=channels_list_kb(channels, lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data == "ch_add")
async def cb_add_channel(callback: types.CallbackQuery, state: FSMContext):
    lang = await get_user_lang(callback.from_user.id)
    text = get_text("add_channel_prompt", lang)
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=cancel_kb(lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=cancel_kb(lang), parse_mode="HTML")
    
    await state.set_state(AddChannelStates.waiting_for_username)
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.message(AddChannelStates.waiting_for_username)
async def handle_channel_username(message: types.Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    username = message.text.strip().replace("@", "").replace("https://t.me/", "")
    
    status_msg = await message.answer(get_text("channel_verifying", lang))
    
    try:
        # Get channel info
        chat = await message.bot.get_chat(f"@{username}")
        
        # Check if bot is admin
        bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            await status_msg.edit_text(get_text("channel_bot_not_admin", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
            await state.clear()
            return
        
        # Check if user is admin
        try:
            user_member = await message.bot.get_chat_member(chat.id, message.from_user.id)
            if user_member.status not in ["administrator", "creator"]:
                await status_msg.edit_text(get_text("channel_not_admin", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
                await state.clear()
                return
        except Exception:
            await status_msg.edit_text(get_text("channel_not_admin", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
            await state.clear()
            return
        
        # Check if already added
        async with async_session_maker() as session:
            existing = await session.execute(
                select(Channel).where(Channel.channel_id == chat.id)
            )
            if existing.scalar_one_or_none():
                await status_msg.edit_text(get_text("channel_already_added", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
                await state.clear()
                return
            
            # Add channel
            new_channel = Channel(
                channel_id=chat.id,
                channel_username=username,
                owner_telegram_id=message.from_user.id
            )
            session.add(new_channel)
            await session.commit()
        
        await status_msg.edit_text(
            get_text("channel_added", lang, name=f"@{username}"),
            reply_markup=back_to_main_kb(lang),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Channel add error: {e}")
        await status_msg.edit_text(get_text("channel_not_found", lang), reply_markup=back_to_main_kb(lang), parse_mode="HTML")
    
    await state.clear()

@router.callback_query(F.data.startswith("ch_manage_"))
async def cb_manage_channel(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    channel_id = int(callback.data.split("_")[2])
    
    async with async_session_maker() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
    
    if not channel:
        await callback.answer("Channel not found", show_alert=True)
        return
    
    text = get_text("channel_manage_title", lang, name=f"@{channel.channel_username}")
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data.startswith("ch_price_"))
async def cb_toggle_price(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    channel_id = int(callback.data.split("_")[2])
    
    async with async_session_maker() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            await session.execute(
                update(Channel).where(Channel.id == channel_id).values(price_enabled=not channel.price_enabled)
            )
            await session.commit()
            # Refresh
            result = await session.execute(select(Channel).where(Channel.id == channel_id))
            channel = result.scalar_one_or_none()
    
    text = get_text("channel_manage_title", lang, name=f"@{channel.channel_username}")
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data.startswith("ch_interval_"))
async def cb_price_interval(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    channel_id = int(callback.data.split("_")[2])
    
    text = f"{get_text('price_interval_title', lang)}\n\n{get_text('price_interval_body', lang)}"
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=price_interval_kb(channel_id, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=price_interval_kb(channel_id, lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data.startswith("ch_setint_"))
async def cb_set_interval(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    parts = callback.data.split("_")
    channel_id = int(parts[2])
    interval = int(parts[3])
    
    async with async_session_maker() as session:
        await session.execute(
            update(Channel).where(Channel.id == channel_id).values(price_interval=interval)
        )
        await session.commit()
    
    await callback.answer(get_text("interval_set", lang, interval=interval), show_alert=True)
    
    # Refresh manage view
    async with async_session_maker() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
    
    text = get_text("channel_manage_title", lang, name=f"@{channel.channel_username}")
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("ch_news_"))
async def cb_toggle_news(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    channel_id = int(callback.data.split("_")[2])
    
    async with async_session_maker() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            await session.execute(
                update(Channel).where(Channel.id == channel_id).values(news_enabled=not channel.news_enabled)
            )
            await session.commit()
            result = await session.execute(select(Channel).where(Channel.id == channel_id))
            channel = result.scalar_one_or_none()
    
    text = get_text("channel_manage_title", lang, name=f"@{channel.channel_username}")
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data.startswith("ch_newslang_"))
async def cb_news_lang_menu(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    channel_id = int(callback.data.split("_")[2])
    
    text = f"{get_text('news_lang_title', lang)}\n\n{get_text('news_lang_body', lang)}"
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=news_lang_kb(channel_id, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=news_lang_kb(channel_id, lang), parse_mode="HTML")
    with suppress(TelegramBadRequest):
        await callback.answer()

@router.callback_query(F.data.startswith("ch_setnewslang_"))
async def cb_set_news_lang(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    parts = callback.data.split("_")
    channel_id = int(parts[2])
    news_lang = parts[3]
    
    async with async_session_maker() as session:
        await session.execute(
            update(Channel).where(Channel.id == channel_id).values(news_language=news_lang)
        )
        await session.commit()
    
    lang_display = {"en": "English", "ru": "Русский", "uz": "O'zbekcha"}.get(news_lang, news_lang)
    await callback.answer(get_text("news_lang_set", lang, language=lang_display), show_alert=True)
    
    async with async_session_maker() as session:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()
    
    text = get_text("channel_manage_title", lang, name=f"@{channel.channel_username}")
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=channel_manage_kb(channel, lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("ch_delete_"))
async def cb_delete_channel(callback: types.CallbackQuery):
    lang = await get_user_lang(callback.from_user.id)
    channel_id = int(callback.data.split("_")[2])
    
    async with async_session_maker() as session:
        await session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        from sqlalchemy import delete
        await session.execute(delete(Channel).where(Channel.id == channel_id))
        await session.commit()
    
    await callback.answer(get_text("channel_deleted", lang), show_alert=True)
    
    # Refresh channels list
    async with async_session_maker() as session:
        result = await session.execute(
            select(Channel).where(Channel.owner_telegram_id == callback.from_user.id)
        )
        channels = result.scalars().all()
    
    if channels:
        text = f"{get_text('channels_title', lang)}\n\n{get_text('channels_list', lang)}"
    else:
        text = f"{get_text('channels_title', lang)}\n\n{get_text('channels_empty', lang)}"
    
    if callback.message.photo or callback.message.animation:
        await callback.message.edit_caption(caption=text, reply_markup=channels_list_kb(channels, lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=channels_list_kb(channels, lang), parse_mode="HTML")

# --- Fallback & Text Handlers ---
@router.message(Command("analyze"))
async def cmd_analyze(message: types.Message, command: CommandObject):
    lang = await get_user_lang(message.from_user.id)
    
    if not command.args:
        await message.answer(get_text("analyze_usage", lang), parse_mode="HTML")
        return
        
    status_msg = await message.answer(get_text("analyze_loading", lang), reply_markup=back_to_main_kb(lang))
    if not ai_analyst:
        return
    
    result = await ai_analyst.analyze_news(command.args)
    
    # Format the result with triple-language summaries
    short_descs = result.get('short_descriptions', {})
    
    response = (
        f"{get_text('analyze_result_title', lang)}\n"
        f"📊 <b>Sentiment:</b> {result.get('sentiment', 'Unknown')}\n"
        f"🏷 <b>Focus:</b> {', '.join(result.get('entities', []))}\n\n"
        f"🇬🇧 <b>EN:</b> {short_descs.get('en', 'N/A')}\n\n"
        f"🇷🇺 <b>RU:</b> {short_descs.get('ru', 'N/A')}\n\n"
        f"🇺🇿 <b>UZ:</b> {short_descs.get('uz', 'N/A')}\n\n"
        f"✅ <i>{get_text('analyze_stored', lang)}</i>"
    )
    
    await status_msg.edit_text(response, reply_markup=back_to_main_kb(lang), parse_mode="HTML")


async def get_user_lang(telegram_id: int) -> str:
    """Helper to get user's language preference."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        return user.language_code if user else "en"

def format_news_message(analysis_data: dict, news_info: dict, lang: str = "en") -> str:
    """
    Standardizes news alert formatting for a given language.
    analysis_data: {'sentiment':..., 'entities':..., 'short_descriptions': {'en':..., 'ru':..., 'uz':...}}
    news_info: {'title':..., 'link':...}
    """
    title = news_info.get('title', 'TON News')
    link = news_info.get('link', '#')
    
    # Get localized short description
    short_descriptions = analysis_data.get('short_descriptions', {})
    short_desc = short_descriptions.get(lang) or analysis_data.get('short_description') or ""
    
    # Sentiment emoji
    sentiment = analysis_data.get('sentiment', 'Neutral')
    sent_emoji = "😐"
    if "bullish" in sentiment.lower(): sent_emoji = "🚀"
    elif "bearish" in sentiment.lower(): sent_emoji = "🐻"
    
    # Format entities as hashtags
    raw_entities = analysis_data.get('entities', [])
    if isinstance(raw_entities, str):
        raw_entities = [e.strip() for e in raw_entities.split(',')]
    
    hashtags = [f"#{e.replace(' ', '')}" for e in raw_entities]
    tags_str = " ".join(hashtags)
    
    # Localized headers
    headers = {
        "en": "🚨 <b>TON Ecosystem Alert</b>",
        "ru": "🚨 <b>Оповещение экосистемы TON</b>",
        "uz": "🚨 <b>TON Ekotizimi Ogohlantirishi</b>"
    }
    header = headers.get(lang, headers["en"])
    
    label_sentiment = {
        "en": "Sentiment",
        "ru": "Настроение",
        "uz": "Kayfiyat"
    }.get(lang, "Sentiment")
    
    label_focus = {
        "en": "Focus",
        "ru": "Фокус",
        "uz": "Fokus"
    }.get(lang, "Focus")
    
    message = (
        f"{header}\n\n"
        f"📰 <a href='{link}'>{title}</a>\n\n"
        f"<i>{short_desc}</i>\n\n"
        f"{sent_emoji} <b>{label_sentiment}:</b> {sentiment}\n"
        f"🏷 <b>{label_focus}:</b> {tags_str}\n"
    )
    return message

async def broadcast_news_alert(analysis_data: dict, news_info: dict, bot):
    """Sends a localized news message to all active users."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()
        
        # Cache formatted messages for the 3 languages
        messages = {
            "en": format_news_message(analysis_data, news_info, "en"),
            "ru": format_news_message(analysis_data, news_info, "ru"),
            "uz": format_news_message(analysis_data, news_info, "uz")
        }
        
        for user in users:
            try:
                lang = user.language_code or "en"
                text = messages.get(lang, messages["en"])
                await bot.send_message(chat_id=user.telegram_id, text=text, parse_mode="HTML", disable_web_page_preview=False)
            except Exception as e:
                logger.error(f"Failed to send news alert to {user.telegram_id}: {e}")


# ===================== INLINE MODE =====================

TON_LOGO_URL = "https://cryptologos.cc/logos/toncoin-ton-logo.png"

@router.inline_query()
async def inline_query_handler(query: types.InlineQuery):
    """Handle inline queries - show TON price on empty query."""
    text = query.query.strip()
    
    results = []
    
    if len(text) == 0:
        # Empty query - show TON price
        if price_monitor:
            price = await price_monitor.fetch_price()
            if price:
                # Format the result
                title = "💎 TON Price"
                description = f"${price:.4f}"
                
                message_content = InputTextMessageContent(
                    message_text=f"💎 <b>TON/USDT</b>\n\n"
                                 f"Price: <code>${price:.4f}</code>\n\n"
                                 f"<i>Powered by TonFonBot</i>",
                    parse_mode="HTML"
                )
                
                results.append(
                    InlineQueryResultArticle(
                        id="ton_price",
                        title=title,
                        description=description,
                        input_message_content=message_content,
                        thumbnail_url=TON_LOGO_URL
                    )
                )
    else:
        # Non-empty query - can add search logic here for other coins
        # For now, still show TON if query matches
        if "ton" in text.lower():
            if price_monitor:
                price = await price_monitor.fetch_price()
                if price:
                    message_content = InputTextMessageContent(
                        message_text=f"💎 <b>TON/USDT</b>\n\n"
                                     f"Price: <code>${price:.4f}</code>\n\n"
                                     f"<i>Powered by TonFonBot</i>",
                        parse_mode="HTML"
                    )
                    
                    results.append(
                        InlineQueryResultArticle(
                            id="ton_price_search",
                            title="💎 TON Price",
                            description=f"${price:.4f}",
                            input_message_content=message_content,
                            thumbnail_url=TON_LOGO_URL
                        )
                    )
    
    await query.answer(results, cache_time=5)


# ===================== TOKEN SCANNER =====================

@router.message(F.text)
async def handle_ton_address(message: types.Message, state: FSMContext):
    """
    Detect TON addresses and perform security audit.
    This handler runs last (catchall for text messages).
    """
    # Skip if in FSM state
    current_state = await state.get_state()
    if current_state:
        return
    
    text = message.text.strip()
    
    # Check if it matches TON address pattern
    if not TON_ADDRESS_PATTERN.match(text):
        return  # Not a TON address, ignore
    
    lang = await get_user_lang(message.from_user.id)
    
    # Check service availability
    if not token_scanner:
        await message.answer(get_text("audit_unavailable", lang), parse_mode="HTML")
        return
    
    # Send scanning message
    status_msg = await message.answer(get_text("audit_scanning", lang), parse_mode="HTML")
    
    try:
        # Fetch token data
        token_data = await token_scanner.scan_token(text)
        
        if not token_data:
            await status_msg.edit_text(get_text("audit_not_found", lang), parse_mode="HTML")
            return
        
        # Analyze security
        analysis = token_scanner.analyze_security(token_data)
        
        # Format and send report
        report = token_scanner.format_audit_report(analysis, lang)
        await status_msg.edit_text(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Token audit error: {e}")
        await status_msg.edit_text(get_text("audit_error", lang), parse_mode="HTML")
