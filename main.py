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
from src.bot import handlers

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

async def broadcast_to_channels(message: str, bot: Bot, news_lang: str = "en"):
    """Send news to channels with news_enabled and matching language."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Channel).where(Channel.news_enabled == True, Channel.news_language == news_lang)
        )
        channels = result.scalars().all()
    
    for channel in channels:
        try:
            await bot.send_message(chat_id=channel.channel_id, text=message, parse_mode="HTML")
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
    
    # Define Alert Callback (Universal Broadcaster)
    async def broadcast_message(message: str):
        # Broadcast to users
        await handlers.broadcast_alert(message, bot)
        # Broadcast to channels with news enabled (default English)
        await broadcast_to_channels(message, bot, "en")

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
    
    price_monitor.on_alert = broadcast_message

    # Register Routers
    dp.include_router(handlers.router)
    
    # Start Background Tasks
    price_task = asyncio.create_task(price_monitor.start_monitoring())
    rss_task = asyncio.create_task(rss_fetcher.start())
    channel_task = asyncio.create_task(channel_price_task(bot, price_monitor))
    
    try:
        logger.info("Bot is online. Polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        logger.info("Shutting down services...")
        rss_fetcher.stop()
        await price_monitor.stop()
        await chart_generator.close()
        
        rss_task.cancel()
        price_task.cancel()
        channel_task.cancel()
        
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")

