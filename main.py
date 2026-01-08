import asyncio
import sys
import time
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from sqlalchemy import select, update

from src.config import config
from src.database.core import init_db, async_session_maker, Channel
from src.services.memory_service import MemoryService
from src.services.ai_analyst import AIAnalyst
from src.services.price_monitor import PriceMonitor
from src.services.chart_generator import ChartGenerator
from src.services.rss_fetcher import RSSFetcher
from src.services.token_scanner import TokenScanner
from src.services.stats_generator import StatsGenerator
from src.bot import handlers
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.tasks import generate_forecast_task, broadcast_stats_task, broadcast_forecast_task, broadcast_ads_task

async def channel_price_task(bot: Bot, price_monitor: PriceMonitor):
    """Background task to send price updates to channels at their configured intervals."""
    while True:
        try:
            current_time = int(time.time())
            
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Channel).where(Channel.price_enabled == True)
                )
                channels = result.scalars().all()
            
            for channel in channels:
                interval_seconds = channel.price_interval * 60
                if current_time - channel.last_price_sent >= interval_seconds:
                    price = await price_monitor.fetch_price()
                    if price:
                        message = f"💎 <b>TON/USDT</b>: <code>${price:.4f}</code>"
                        try:
                            await bot.send_message(chat_id=channel.channel_id, text=message, parse_mode="HTML")
                            
                            # Update last_price_sent
                            async with async_session_maker() as session:
                                await session.execute(
                                    update(Channel).where(Channel.id == channel.id).values(last_price_sent=current_time)
                                )
                                await session.commit()
                        except Exception as e:
                            logger.error(f"Failed to send price to channel {channel.channel_id}: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Channel price task error: {e}")
            await asyncio.sleep(60)

async def broadcast_to_channels(analysis_data: dict, news_info: dict, bot: Bot):
    """Send news to channels using their configured language."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Channel).where(Channel.news_enabled == True)
        )
        channels = result.scalars().all()
    
    # Cache formatted messages
    messages = {
        "en": handlers.format_news_message(analysis_data, news_info, "en"),
        "ru": handlers.format_news_message(analysis_data, news_info, "ru"),
        "uz": handlers.format_news_message(analysis_data, news_info, "uz")
    }
    
    for channel in channels:
        try:
            lang = channel.news_language or "en"
            text = messages.get(lang, messages["en"])
            await bot.send_message(chat_id=channel.channel_id, text=text, parse_mode="HTML", disable_web_page_preview=False)
        except Exception as e:
            logger.error(f"Failed to send news to channel {channel.channel_id}: {e}")

async def main():
    # Configure Loguru
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.info("Starting TON Sentinel AI...")

    # Initialize Bot and Dispatcher
    if config.PROXY_URL:
        session = AiohttpSession(proxy=config.PROXY_URL)
        bot = Bot(token=config.BOT_TOKEN.get_secret_value(), session=session)
    else:
        bot = Bot(token=config.BOT_TOKEN.get_secret_value())

    dp = Dispatcher()
    
    # Initialize Database
    await init_db()
    
    # Initialize Services
    memory_service = MemoryService()
    ai_analyst = AIAnalyst(memory_service=memory_service)
    price_monitor = PriceMonitor(symbol='TON/USDT')
    chart_generator = ChartGenerator(symbol='TON/USDT')
    token_scanner = TokenScanner()
    stats_generator = StatsGenerator()
    
    # Define Alert Callback (Universal Broadcaster)
    async def broadcast_message(analysis_data: dict, news_info: dict):
        # Broadcast to users
        await handlers.broadcast_news_alert(analysis_data, news_info, bot)
        # Broadcast to channels
        await broadcast_to_channels(analysis_data, news_info, bot)


    # Initialize RSS Fetcher with AI and Broadcaster
    # Interval set to 600s (10 min)
    rss_fetcher = RSSFetcher(
        memory_service=memory_service,
        ai_analyst=ai_analyst,
        broadcast_callback=broadcast_message,
        interval=600 
    )
    
    # Inject dependencies into handlers
    handlers.price_monitor = price_monitor
    handlers.chart_generator = chart_generator
    handlers.ai_analyst = ai_analyst
    handlers.token_scanner = token_scanner
    handlers.stats_generator = stats_generator
    
    price_monitor.on_alert = broadcast_message

    # Register Routers
    dp.include_router(handlers.router)
    
    # Start Background Tasks
    price_task = asyncio.create_task(price_monitor.start_monitoring())
    rss_task = asyncio.create_task(rss_fetcher.start())
    channel_task = asyncio.create_task(channel_price_task(bot, price_monitor))
    
    # Initialize Scheduler
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent") # Explicitly set UZB time
    
    # 1. Generate Forecast: Twice a day (e.g., 08:30 and 20:30) to be ready for broadcast
    # Broadcast is at 9:01, so generation should happen before. 
    # User said: "execute it twice a day... 12-hour interval". Let's do 08:50 and 20:50.
    scheduler.add_job(generate_forecast_task, 'cron', hour=8, minute=50, args=[ai_analyst, price_monitor])
    scheduler.add_job(generate_forecast_task, 'cron', hour=20, minute=50, args=[ai_analyst, price_monitor])
    
    # 2. Statistics Broadcast: Once a day at 9:00 UZB
    scheduler.add_job(broadcast_stats_task, 'cron', hour=9, minute=0, args=[stats_generator, bot])
    
    # 3. Forecast Broadcast: Once a day at 9:01 UZB
    scheduler.add_job(broadcast_forecast_task, 'cron', hour=9, minute=1, args=[ai_analyst, bot])
    
    # 4. Ads for Price Channels: Every hour
    scheduler.add_job(broadcast_ads_task, 'interval', hours=1, args=[bot])
    
    scheduler.start()
    
    try:
        logger.info("Bot is online. Polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        logger.info("Shutting down services...")
        if 'scheduler' in locals():
            scheduler.shutdown()
        rss_fetcher.stop()
        await price_monitor.stop()
        await chart_generator.close()
        await token_scanner.close()
        await stats_generator.close()
        
        rss_task.cancel()
        price_task.cancel()
        channel_task.cancel()
        
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")

