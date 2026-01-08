"""
StatsGenerator Service - Generates stat.png images with live market data.
Uses Pillow for image rendering and public APIs for data (no keys required).
"""

import io
import math
import aiohttp
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from loguru import logger
from typing import Optional, List, Tuple
import ccxt.async_support as ccxt


class StatsGenerator:
    """Generates statistics images for TON and related cryptocurrencies."""
    
    # Image dimensions
    WIDTH = 800
    HEIGHT = 420
    
    # Colors
    BG_COLOR = (10, 10, 15)  # Very dark background
    TEXT_WHITE = (255, 255, 255)
    TEXT_GRAY = (160, 170, 190)
    GREEN = (46, 213, 115)
    RED = (255, 71, 87)
    ORANGE = (255, 165, 2)
    YELLOW = (225, 177, 44)
    TON_BLUE = (0, 136, 204)
    
    # Asset paths
    ASSETS_DIR = os.path.join(os.getcwd(), 'assets', 'icons')
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._exchange = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _get_exchange(self):
        if self._exchange is None:
            self._exchange = ccxt.bybit()
        return self._exchange
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
        if self._exchange:
            await self._exchange.close()
    
    async def fetch_market_data(self) -> dict:
        """Fetch all required market data from public APIs."""
        session = await self._get_session()
        exchange = await self._get_exchange()
        
        data = {
            "ton_price": 0.0,
            "ton_change_24h": 0.0,
            "ton_change_7d": 0.0,
            "ton_change_30d": 0.0,
            "btc_change_24h": 0.0,
            "eth_change_24h": 0.0,
            "sol_change_24h": 0.0,
            "fear_greed": 50,
            "fear_greed_text": "Neutral",
            "price_history": []
        }
        
        try:
            ticker = await exchange.fetch_ticker('TON/USDT')
            data["ton_price"] = ticker.get('last', 0)
            data["ton_change_24h"] = ticker.get('percentage', 0) or 0
            
            ohlcv = await exchange.fetch_ohlcv('TON/USDT', '1d', limit=50) # More data for smoother curve
            if ohlcv:
                data["price_history"] = [candle[4] for candle in ohlcv[-50:]]
                
                if len(ohlcv) >= 7:
                    price_7d_ago = ohlcv[-7][4]
                    data["ton_change_7d"] = ((data["ton_price"] - price_7d_ago) / price_7d_ago) * 100
                
                if len(ohlcv) >= 30:
                    price_30d_ago = ohlcv[0][4]
                    data["ton_change_30d"] = ((data["ton_price"] - price_30d_ago) / price_30d_ago) * 100
        except Exception as e:
            logger.error(f"Error fetching TON data: {e}")
        
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": "bitcoin,ethereum,solana", "vs_currencies": "usd", "include_24hr_change": "true"}
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    cg_data = await resp.json()
                    data["btc_change_24h"] = cg_data.get("bitcoin", {}).get("usd_24h_change", 0) or 0
                    data["eth_change_24h"] = cg_data.get("ethereum", {}).get("usd_24h_change", 0) or 0
                    data["sol_change_24h"] = cg_data.get("solana", {}).get("usd_24h_change", 0) or 0
        except Exception as e:
            logger.error(f"Error fetching comparison data: {e}")
        
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            async with session.get(url) as resp:
                if resp.status == 200:
                    fng_data = await resp.json()
                    if fng_data.get("data"):
                        data["fear_greed"] = int(fng_data["data"][0].get("value", 50))
                        data["fear_greed_text"] = fng_data["data"][0].get("value_classification", "Neutral")
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")
        
        return data
    
    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        font_paths = [
            "/usr/share/fonts/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
        return ImageFont.load_default()
    
    def _load_icon(self, name: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        try:
            path = os.path.join(self.ASSETS_DIR, f"{name}.png")
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                return img.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            logger.warning(f"Failed to load icon {name}: {e}")
        return None
    
    def _create_background(self) -> Image.Image:
        """Create a deep, rich gradient background."""
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        
        # 1. Main Blue Glow (Left)
        # Create a large radial gradient manually by drawing concentric circles
        center_x, center_y = 150, 100
        max_radius = 500
        for r in range(max_radius, 0, -2):
            alpha = int((1 - (r / max_radius)) * 50) # Max alpha 40
            color = (0, 100, 200) # Deep Blue
            # Draw semi-transparent circle
            # We need a temporary layer for alpha blending
            overlay = Image.new('RGBA', img.size, (0,0,0,0))
            d = ImageDraw.Draw(overlay)
            d.ellipse((center_x - r, center_y - r, center_x + r, center_y + r), fill=(*color, alpha))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            
        # 2. Secondary Purple Glow (Bottom Right)
        center_x, center_y = 700, 350
        max_radius = 400
        for r in range(max_radius, 0, -10): # Bigger steps for speed
            alpha = int((1 - (r / max_radius)) * 30)
            color = (80, 0, 150) # Deep Purple
            overlay = Image.new('RGBA', img.size, (0,0,0,0))
            d = ImageDraw.Draw(overlay)
            d.ellipse((center_x - r, center_y - r, center_x + r, center_y + r), fill=(*color, alpha))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            
        return img.convert('RGBA')

    def _draw_glass_card(self, img: Image.Image, xy: Tuple):
        """Draw ultra-smooth glass morphism card."""
        x1, y1, x2, y2 = xy
        width = x2 - x1
        height = y2 - y1
        radius = 24
        
        # 1. Card Base (Semi-transparent black/blue)
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        d = ImageDraw.Draw(overlay)
        d.rounded_rectangle(xy, radius=radius, fill=(30, 35, 50, 160)) # More opaque
        img.alpha_composite(overlay)
        
        # 2. Top/Left Highlight (White sheen)
        highlight = Image.new('RGBA', img.size, (0,0,0,0))
        d_high = ImageDraw.Draw(highlight)
        # Gradient border hack: Draw slightly larger white rect behind, then mask? 
        # Simpler: just stroke top and left lines
        d_high.line([(x1+radius, y1), (x2-radius, y1)], fill=(255, 255, 255, 40), width=1)
        d_high.line([(x1, y1+radius), (x1, y2-radius)], fill=(255, 255, 255, 40), width=1)
        d_high.arc((x1, y1, x1+radius*2, y1+radius*2), 180, 270, fill=(255, 255, 255, 40), width=1)
        img.alpha_composite(highlight)
        
        # 3. Inner Glow (Subtle)
        glow = Image.new('RGBA', img.size, (0,0,0,0))
        d_glow = ImageDraw.Draw(glow)
        d_glow.rounded_rectangle((x1+1, y1+1, x2-1, y2-1), radius=radius-1, outline=(255, 255, 255, 10))
        img.alpha_composite(glow)

    def _draw_gauge(self, img: Image.Image, center: Tuple[int, int], radius: int, value: int):
        cx, cy = center
        draw = ImageDraw.Draw(img)
        thickness = 8
        
        # Background Arc (Dark Gray)
        start_angle = 140
        end_angle = 400
        
        # Draw dotted background
        for angle in range(start_angle, end_angle, 4):
            rad = math.radians(angle)
            x1 = cx + (radius - thickness) * math.cos(rad)
            y1 = cy + (radius - thickness) * math.sin(rad)
            x2 = cx + radius * math.cos(rad)
            y2 = cy + radius * math.sin(rad)
            draw.line([(x1, y1), (x2, y2)], fill=(60, 70, 90), width=2)
            
        # Active Arc (Gradient Color)
        val_angle = start_angle + (value / 100) * (end_angle - start_angle)
        
        for angle in range(start_angle, int(val_angle), 1):
            rad = math.radians(angle)
            
            # Gradient
            progress = (angle - start_angle) / (end_angle - start_angle)
            if progress < 0.25: color = self.RED
            elif progress < 0.5: color = self.ORANGE
            elif progress < 0.75: color = self.YELLOW
            else: color = self.GREEN
            
            # Draw smooth arc segment
            # We use polygon to fill the segment for smoother look than lines
            # Outer points
            ox1 = cx + radius * math.cos(rad)
            oy1 = cy + radius * math.sin(rad)
            ox2 = cx + radius * math.cos(math.radians(angle+1.5))
            oy2 = cy + radius * math.sin(math.radians(angle+1.5))
            
            # Inner points
            ix1 = cx + (radius - thickness) * math.cos(rad)
            iy1 = cy + (radius - thickness) * math.sin(rad)
            ix2 = cx + (radius - thickness) * math.cos(math.radians(angle+1.5))
            iy2 = cy + (radius - thickness) * math.sin(math.radians(angle+1.5))
            
            draw.polygon([(ox1, oy1), (ox2, oy2), (ix2, iy2), (ix1, iy1)], fill=color)

        # Needle (Simple clean triangle)
        needle_angle = val_angle
        rad = math.radians(needle_angle)
        
        # Tip
        tip_x = cx + (radius - 15) * math.cos(rad)
        tip_y = cy + (radius - 15) * math.sin(rad)
        
        # Base
        base_w = 4
        base_rad_l = math.radians(needle_angle - 90)
        base_rad_r = math.radians(needle_angle + 90)
        
        bl_x = cx + base_w * math.cos(base_rad_l)
        bl_y = cy + base_w * math.sin(base_rad_l)
        br_x = cx + base_w * math.cos(base_rad_r)
        br_y = cy + base_w * math.sin(base_rad_r)
        
        draw.polygon([(tip_x, tip_y), (br_x, br_y), (bl_x, bl_y)], fill=self.TEXT_WHITE)
        draw.ellipse((cx-3, cy-3, cx+3, cy+3), fill=self.TEXT_WHITE)

    def _format_change(self, value: float) -> Tuple[str, Tuple]:
        if value >= 0:
            return f"+{value:.1f}%", self.GREEN
        else:
            return f"{value:.1f}%", self.RED

    async def generate_image(self) -> Optional[io.BytesIO]:
        try:
            data = await self.fetch_market_data()
            
            # 1. New Background rendering
            img = self._create_background()
            draw = ImageDraw.Draw(img)
            
            # Fonts
            font_title = self._get_font(11, bold=True)
            font_price = self._get_font(42, bold=True)
            font_label = self._get_font(10)
            font_value = self._get_font(13, bold=True)
            font_gauge_num = self._get_font(32, bold=True)
            font_gauge_label = self._get_font(14, bold=True)
            font_coin = self._get_font(16, bold=True)
            font_coin_change = self._get_font(15, bold=True)
            
            # Shared layout
            card_w = 370
            card_h = 175
            gap = 20
            margin = 20
            
            # ================= CARD 1 =================
            c1_xy = (margin, margin, margin+card_w, margin+card_h)
            self._draw_glass_card(img, c1_xy)
            
            # Content
            draw.text((margin+25, margin+20), "TONCOIN PRICE & CHANGES", fill=self.TEXT_GRAY, font=font_title)
            
            ton_icon = self._load_icon("ton", (54, 54))
            if ton_icon: img.alpha_composite(ton_icon, (margin+25, margin+55))
            
            draw.text((margin+90, margin+55), f"${data['ton_price']:.2f}", fill=self.TEXT_WHITE, font=font_price)
            
            # Detailed changes
            lbls = ["DAILY", "WEEKLY", "MONTHLY"]
            vals = [data["ton_change_24h"], data["ton_change_7d"], data["ton_change_30d"]]
            for i, (l, v) in enumerate(zip(lbls, vals)):
                x = margin + 30 + i * 110
                y = margin + 125
                draw.text((x, y), l, fill=self.TEXT_GRAY, font=font_label)
                txt, col = self._format_change(v)
                draw.text((x, y+16), txt, fill=col, font=font_value)

            # ================= CARD 2 =================
            c2_x, c2_y = margin+card_w+gap, margin
            self._draw_glass_card(img, (c2_x, c2_y, c2_x+card_w, c2_y+card_h))
            
            draw.text((c2_x+130, c2_y+20), "FEAR & GREED INDEX", fill=self.TEXT_GRAY, font=font_title)
            
            gauge_cx = c2_x + card_w // 2
            gauge_cy = c2_y + 100
            self._draw_gauge(img, (gauge_cx, gauge_cy), 55, data["fear_greed"])
            
            # Text inside
            v_txt = str(data["fear_greed"])
            bw, bh = draw.textbbox((0,0), v_txt, font=font_gauge_num)[2:]
            draw.text((gauge_cx - bw/2, gauge_cy - 10), v_txt, fill=self.TEXT_WHITE, font=font_gauge_num)
            
            l_txt = data["fear_greed_text"].upper()
            bw, bh = draw.textbbox((0,0), l_txt, font=font_gauge_label)[2:]
            
            if data["fear_greed"] < 25: c = self.RED
            elif data["fear_greed"] < 45: c = self.ORANGE
            elif data["fear_greed"] < 55: c = self.YELLOW
            else: c = self.GREEN
            
            draw.text((gauge_cx - bw/2, gauge_cy + 25), l_txt, fill=c, font=font_gauge_label)

            # ================= CARD 3 (Chart) =================
            c3_y = margin + card_h + gap
            self._draw_glass_card(img, (margin, c3_y, margin+card_w, c3_y+card_h))
            
            draw.text((margin+25, c3_y+20), "DAILY PRICE CHART", fill=self.TEXT_GRAY, font=font_title)
            
            # Simple smooth line
            prices = data["price_history"]
            if prices and len(prices) > 1:
                gx1, gy1, gx2, gy2 = margin+20, c3_y+50, margin+card_w-20, c3_y+card_h-20
                min_p, max_p = min(prices), max(prices)
                rng = max_p - min_p or 1
                
                # Gradient fill under line
                overlay = Image.new('RGBA', img.size, (0,0,0,0))
                od = ImageDraw.Draw(overlay)
                
                pts = []
                for i, p in enumerate(prices):
                    x = gx1 + (i / (len(prices)-1)) * (gx2 - gx1)
                    y = gy2 - ((p - min_p) / rng) * (gy2 - gy1)
                    pts.append((x, y))
                
                # Fill
                fill_pts = pts + [(gx2, gy2), (gx1, gy2)]
                od.polygon(fill_pts, fill=(46, 213, 115, 30)) # Transparent green
                img.alpha_composite(overlay)
                
                # Line
                draw.line(pts, fill=self.GREEN, width=2)
                
            # ================= CARD 4 (Compare) =================
            c4_x, c4_y = margin+card_w+gap, margin+card_h+gap
            self._draw_glass_card(img, (c4_x, c4_y, c4_x+card_w, c4_y+card_h))
            
            draw.text((c4_x+25, c4_y+20), "COMPARE TO", fill=self.TEXT_GRAY, font=font_title)
            
            coins = [("BTC", data["btc_change_24h"], "btc"), ("ETH", data["eth_change_24h"], "eth"), ("SOL", data["sol_change_24h"], "sol")]
            for i, (nm, val, icon) in enumerate(coins):
                y = c4_y + 55 + i * 38
                ic = self._load_icon(icon, (26, 26))
                if ic: img.alpha_composite(ic, (c4_x+30, y))
                
                draw.text((c4_x+70, y+2), nm, fill=self.TEXT_WHITE, font=font_coin)
                txt, col = self._format_change(val)
                draw.text((c4_x+280, y+2), txt, fill=col, font=font_coin_change)
            
            out = io.BytesIO()
            img.convert("RGB").save(out, "PNG")
            out.seek(0)
            return out
            
        except Exception as e:
            logger.error(f"Generate error: {e}")
            return None
