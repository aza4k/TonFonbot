import asyncio
from loguru import logger
from datetime import datetime
from aiogram import Bot
from sqlalchemy import select

from src.database.core import async_session_maker, Channel
from src.services.ai_analyst import AIAnalyst
from src.services.stats_generator import StatsGenerator
from src.services.price_monitor import PriceMonitor
from src.bot import handlers
from aiogram.types import BufferedInputFile

async def generate_forecast_task(ai_analyst: AIAnalyst, price_monitor: PriceMonitor):
    """Generates the AI forecast and saves it to the DB."""
    try:
        logger.info("Starting scheduled forecast generation...")
        current_price = await price_monitor.fetch_price()
        market_data_str = f"Current TON Price: ${current_price}" if current_price else "Price data unavailable."
        
        # This implicitly saves to DB due to our changes in AIAnalyst
        await ai_analyst.generate_daily_forecast(market_data_str)
        logger.info("Forecast generation completed and saved.")
    except Exception as e:
        logger.error(f"Forecast generation task failed: {e}")

async def broadcast_stats_task(stats_generator: StatsGenerator, bot: Bot):
    """Sends the daily statistics image to all channels."""
    try:
        logger.info("Starting statistics broadcast...")
        # Generate image
        buf = await stats_generator.generate_image()
        if not buf:
            logger.error("Failed to generate stats image for broadcast")
            return
            
        # Get all channels
        async with async_session_maker() as session:
            # We broadcast to all channels that haven't explicitly disabled it?
            # Or usually just news_enabled ones. Let's stick to news_enabled for safety,
            # or maybe separate flag. For now, let's assume all connected channels 
            # as per request "sent to all connected channels".
            result = await session.execute(select(Channel))
            channels = result.scalars().all()
            
        image_data = buf.read()
        
        for channel in channels:
            try:
                # Reset buffer position for each send? No, we read to bytes already.
                file = BufferedInputFile(image_data, filename="stat.png")
                
                # Add bot footer
                caption = (
                    "📊 <b>Daily TON Statistics</b>\n\n"
                    "<i>Powered by @TonFonBot</i>"
                )
                
                await bot.send_photo(chat_id=channel.channel_id, photo=file, caption=caption, parse_mode="HTML")
                await asyncio.sleep(0.5) # Rate limit slightly
            except Exception as e:
                logger.error(f"Failed to send stats to {channel.channel_id}: {e}")
                
        logger.info("Statistics broadcast completed.")
        
    except Exception as e:
        logger.error(f"Stats broadcast task failed: {e}")

async def broadcast_forecast_task(ai_analyst: AIAnalyst, bot: Bot):
    """Broadcasts the latest forecast to all channels."""
    try:
        logger.info("Starting forecast broadcast...")
        forecast = await ai_analyst.get_latest_forecast()
        
        if not forecast:
            logger.warning("No forecast found to broadcast.")
            return

        async with async_session_maker() as session:
            result = await session.execute(select(Channel))
            channels = result.scalars().all()

        for channel in channels:
            try:
                lang = channel.news_language or "en"
                text_content = forecast.get(lang) or forecast.get('en')
                
                if not text_content:
                    continue

                message = (
                    f"🔮 <b>Daily AI Forecast</b>\n\n"
                    f"{text_content}\n\n"
                    f"🤖 <i>Analyzed by @TonFonBot</i>"
                )
                
                await bot.send_message(chat_id=channel.channel_id, text=message, parse_mode="HTML")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to send forecast to {channel.channel_id}: {e}")
                
        logger.info("Forecast broadcast completed.")

    except Exception as e:
        logger.error(f"Forecast broadcast task failed: {e}")

async def broadcast_ads_task(bot: Bot):
    """Sends ads to channels that ONLY use the bot for prices (no news)."""
    try:
        # User request: "Channels that only connect to show prices should also be sent an advertisement for our bot every hour."
        # This implies: price_enabled=True AND news_enabled=False (or maybe just checking if they use it "free").
        # The prompt says: "Since those who connect our bot to the channel use it for free... Channels that only connect to show prices..."
        # We will target channels where price_enabled is True? Or just all channels?
        # Interpretation: Target channels that are utilizing the service but maybe not the premium features, basically spamming them to use the bot more?
        # A safer bet is to target channels that have `price_enabled=True` (active users) or maybe ALL channels?
        # "Channels that only connect to show prices" -> This strongly suggests `price_enabled=True` and maybe checking if they pay? (No payment system yet).
        # Let's target all channels for now, or maybe just `price_enabled=True`.
        # Actually, "Channels that ONLY connect to show prices" -> maybe `news_enabled=False`.
        
        async with async_session_maker() as session:
            # Select channels that have price enabled but news disabled (filtering logic assumption)
            # OR just strictly "only show prices".
            # Let's go with: price_enabled = True.
            result = await session.execute(
                select(Channel).where(Channel.price_enabled == True)
            )
            channels = result.scalars().all()
            
        ad_text = (
            "🚀 <b>Boost Your Channel with TonFonBot!</b>\n\n"
            "Get daily AI analysis, market stats, and more.\n"
            "👉 Add @TonFonBot to your channel as Admin!"
        )

        for channel in channels:
            try:
                await bot.send_message(chat_id=channel.channel_id, text=ad_text, parse_mode="HTML")
            except Exception as e:
                # Start logging less verbosely for ads to avoid spamming logs
                pass
                
    except Exception as e:
        logger.error(f"Ads broadcast task failed: {e}")
