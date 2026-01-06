import io
import pandas as pd
import mplfinance as mpf
import ccxt.async_support as ccxt
from loguru import logger
from typing import Optional

class ChartGenerator:
    def __init__(self, symbol: str = 'TON/USDT', timeframe: str = '1h'):
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange = ccxt.bybit()

    async def fetch_ohlcv(self, limit: int = 24) -> Optional[pd.DataFrame]:
        """
        Fetches OHLCV data and returns a DataFrame.
        """
        try:
            # parsing timeframe to milliseconds might be needed if not standard, 
            # but ccxt usually handles string timeframes well.
            ohlcv = await self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
            
            if not ohlcv:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {self.symbol}: {e}")
            return None
        finally:
            # We don't close the exchange here if we want to reuse the instance, 
            # but for a stateless generator call, we might want to manage lifecycle differently.
            # For now, let's just close it to be safe or assuming short-lived usage.
            # If this class is long-lived, we should keep it open.
            # Given requirement is just "Fetch... Use...", let's keep connection management simple.
            pass

    async def generate_chart(self) -> Optional[io.BytesIO]:
        """
        Generates a candlestick chart and returns it as a BytesIO object.
        """
        try:
            df = await self.fetch_ohlcv()
            if df is None or df.empty:
                logger.warning("No data available to generate chart.")
                return None

            # Create an in-memory buffer
            buf = io.BytesIO()

            # Style configuration
            # 'binance' style is a good approximation of standard dark crypto charts
            # or we can define a custom style.
            s = mpf.make_mpf_style(base_mpf_style='nightclouds', rc={'figure.facecolor': '#0d1117'})

            mpf.plot(
                df,
                type='candle',
                style=s,
                title=f"{self.symbol} - Last 24 Hours",
                ylabel='Price (USDT)',
                volume=True,
                savefig=dict(fname=buf, dpi=300, bbox_inches='tight', transparent=False)
            )
            
            buf.seek(0)
            return buf
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return None
    
    async def close(self):
        await self.exchange.close()
