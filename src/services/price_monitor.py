import asyncio
from typing import Optional, Callable, Awaitable
import ccxt.async_support as ccxt
from loguru import logger

class PriceMonitor:
    def __init__(self, symbol: str = 'TON/USDT', poll_interval: int = 60, alert_threshold: float = 0.01):
        """
        :param symbol: Trading pair to monitor (e.g., 'TON/USDT')
        :param poll_interval: Seconds between checks
        :param alert_threshold: Percentage change to trigger alert (0.01 = 1%)
        """
        self.symbol = symbol
        self.poll_interval = poll_interval
        self.alert_threshold = alert_threshold
        self.last_price: Optional[float] = None
        self.exchange = ccxt.bybit()
        self.running = False
        
        # Optional callback for alerts (async function)
        self.on_alert: Optional[Callable[[str], Awaitable[None]]] = None

    async def fetch_price(self) -> Optional[float]:
        try:
            ticker = await self.exchange.fetch_ticker(self.symbol)
            return ticker.get('last')
        except Exception as e:
            logger.error(f"Error fetching price for {self.symbol}: {e}")
            return None

    async def start_monitoring(self):
        self.running = True
        logger.info(f"Started price monitoring for {self.symbol} on Bybit.")
        
        # Initialize last_price
        self.last_price = await self.fetch_price()
        
        while self.running:
            await asyncio.sleep(self.poll_interval)
            
            current_price = await self.fetch_price()
            if current_price is None:
                continue
                
            if self.last_price:
                pct_change = (current_price - self.last_price) / self.last_price
                
                if abs(pct_change) > self.alert_threshold:
                    direction = "UP" if pct_change > 0 else "DOWN"
                    message = (
                        f"🚨 HIGH VOLATILITY ALERT: {self.symbol} {direction} "
                        f"{abs(pct_change):.2%} (Prior: {self.last_price}, Curr: {current_price})"
                    )
                    logger.warning(message)
                    
                    if self.on_alert:
                        try:
                            await self.on_alert(message)
                        except Exception as e:
                            logger.error(f"Error in alert callback: {e}")
            
            # Update last_price
            self.last_price = current_price

    async def stop(self):
        self.running = False
        await self.exchange.close()
        logger.info(f"Stopped price monitoring for {self.symbol}.")
