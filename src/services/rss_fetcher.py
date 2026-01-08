import asyncio
import feedparser
from typing import List, Set, Callable, Awaitable, Any
from datetime import datetime
from loguru import logger
from src.services.memory_service import MemoryService
from src.services.ai_analyst import AIAnalyst

class RSSFetcher:
    def __init__(self, memory_service: MemoryService, ai_analyst: AIAnalyst = None, broadcast_callback: Callable[[dict, dict], Awaitable[Any]] = None, interval: int = 600):
        self.memory_service = memory_service
        self.ai_analyst = ai_analyst
        self.broadcast_callback = broadcast_callback
        self.interval = interval
        self.running = False
        self.processed_links: Set[str] = set()
        self.first_run = True
        
        # Sources
        self.feeds = [
            "https://news.google.com/rss/search?q=TON+Blockchain+OR+Toncoin&hl=en-US&gl=US&ceid=US:en",
            "https://cointelegraph.com/rss/tag/ton",
            "https://www.coindesk.com/arc/outboundfeeds/rss/"
        ]
        
        # Filter Keywords
        self.keywords = ['TON', 'Toncoin', 'Pavel Durov', 'Notcoin']

    async def fetch_feeds(self):
        """
        Iterates through feeds, filters, dedupes, saves news, AND broadcasts.
        """
        logger.info("📡 Fetching RSS feeds...")
        
        for feed_url in self.feeds:
            try:
                # parsing is synchronous, might block event loop slightly. 
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    link = entry.get('link')
                    title = entry.get('title', '')
                    summary = entry.get('summary', '') or entry.get('description', '')
                    
                    # 0. Date Filter (Skip news older than 24h)
                    try:
                        published_struct = entry.get('published_parsed') or entry.get('updated_parsed')
                        if published_struct:
                            # Convert struct_time to datetime
                            pub_date = datetime(*published_struct[:6])
                            # Simple check: If news is > 24h old, skip
                            if (datetime.now() - pub_date).total_seconds() > 86400: # 1 day
                                # Debug log only occasionally or if verbose? 
                                # logger.debug(f"Skipping old news: {title} ({pub_date})")
                                continue
                    except Exception:
                        # If date parsing fails, strictly speaking we might want to skip or keep.
                        # For now, let's keep it but depend on deduplication.
                        pass
                    
                    # 1. Check link cache
                    if link in self.processed_links:
                        continue
                    
                    # 2. Start-up Ignore Logic
                    if self.first_run:
                        self.processed_links.add(link)
                        continue

                    # 3. Keyword Filter
                    content_to_check = f"{title} {summary}"
                    if not any(kw.lower() in content_to_check.lower() for kw in self.keywords):
                        continue
                        
                    # 4. Vector Similarity Check (Deduplication)
                    is_duplicate = await self.memory_service.check_similarity(title)
                    if is_duplicate:
                        logger.info(f"Skipping duplicate news: {title}")
                        self.processed_links.add(link)
                        continue
                    
                    # --- NEW LOGIC: Analyze & Broadcast ---
                    
                    logger.info(f"⚡ Processing New Unique News: {title}")
                    
                    # A. Call AI Analyst (Analyzing + Saving to Memory is handled here)
                    if self.ai_analyst:
                        analysis_text = f"Title: {title}\nSummary: {summary}\nLink: {link}"
                        result = await self.ai_analyst.analyze_news(analysis_text)
                        
                        # Add to processed to avoid re-processing
                        self.processed_links.add(link)
                        
                        # B. Broadcast
                        if self.broadcast_callback:
                             # We now send the structured result and news info
                             news_info = {
                                 "title": title,
                                 "link": link
                             }
                             await self.broadcast_callback(result, news_info)
                             logger.success(f"Broadcast triggered for: {title}")


                    else:
                        # Fallback if no AI analyst (should not happen in this config)
                        self.processed_links.add(link)

            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {e}")
        
        # After iterating all feeds once, first run is complete
        if self.first_run:
            self.first_run = False
            logger.info("✅ Initial feed sync complete. Listening for NEW events now.")

    async def start(self):
        self.running = True
        logger.info("RSS Fetcher Service Started.")
        
        while self.running:
            await self.fetch_feeds()
            await asyncio.sleep(self.interval)

    def stop(self):
        self.running = False
        logger.info("RSS Fetcher Service Stopped.")
