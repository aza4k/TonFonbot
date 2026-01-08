import json
from openai import OpenAI
from loguru import logger
from src.config import config
from src.services.memory_service import MemoryService

class AIAnalyst:
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY.get_secret_value()
        )
        self.model_name = "tngtech/deepseek-r1t2-chimera:free"

    async def analyze_news(self, text: str) -> dict:
        """
        Analyzes news text to generate summaries in EN, RU, and UZ.
        Returns: {
            'sentiment': 'Bullish', 
            'entities': ['TON', 'Telegram'], 
            'dates': [],
            'short_descriptions': {'en': '...', 'ru': '...', 'uz': '...'}
        }
        """
        system_prompt = (
            "You are an expert crypto analyst specializing in the TON ecosystem. "
            "Analyze the input news. Extract key entities, sentiment (Bullish/Bearish/Neutral), "
            "and identify any specific dates mentioned. "
            "Provide an 'engaging' 1-2 sentence short description for each of the following languages: English, Russian, and Uzbek. "
            "Return the result as a raw valid JSON string with these EXACT keys: "
            "'entities' (list), 'sentiment' (string), 'dates' (list), "
            "'short_descriptions' (object with keys 'en', 'ru', 'uz'). "
            "Do not include markdown formatting or ANY other text, just the raw JSON."
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"News Content:\n{text}"}
                ]
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            analysis_dict = json.loads(content)
            
            # Extract descriptions
            short_descs = analysis_dict.get('short_descriptions', {})
            en_desc = short_descs.get('en', '')
            
            # Store in memory for RAG (using English version as primary for retrieval)
            metadata = {
                "type": "news_analysis",
                "sentiment": analysis_dict.get("sentiment", "Neutral"),
                "entities": ", ".join(analysis_dict.get("entities", [])),
                "dates": ", ".join(analysis_dict.get("dates", [])),
                "desc_en": en_desc,
                "desc_ru": short_descs.get('ru', ''),
                "desc_uz": short_descs.get('uz', '')
            }
            
            memory_content = f"News: {text}\nShort Analysis (EN): {en_desc}"
            await self.memory_service.add_memory(text=memory_content, metadata=metadata)
            
            return analysis_dict

        except Exception as e:
            logger.error(f"Error in analyze_news: {e}")
            return {
                "entities": [],
                "sentiment": "Neutral",
                "dates": [],
                "short_descriptions": {"en": "", "ru": "", "uz": ""}
            }

    async def generate_daily_forecast(self, market_data: str) -> dict:
        """
        Generates a daily forecast in EN, RU, and UZ.
        Returns: {'en': '...', 'ru': '...', 'uz': '...'}
        """
        try:
            # 1. Retrieve relevant context
            query = "Upcoming events for TON"
            rag_results = await self.memory_service.query_memory(query, n_results=5)
            
            memories = []
            if rag_results and 'documents' in rag_results:
                for doc_list in rag_results['documents']:
                    memories.extend(doc_list)
            
            context_str = "\n".join(memories) if memories else "No specific upcoming events found in memory."

            # 2. Prompt OpenRouter for triple language output
            prompt = (
                f"Context (Known Events/News):\n{context_str}\n\n"
                f"Current Market Data:\n{market_data}\n\n"
                "Based on the context and data, predict the TON market trend for today. "
                "Provide a detailed, logical forecast for each of these languages: English, Russian, and Uzbek. "
                "Return the result as a raw JSON object with keys: 'en', 'ru', 'uz'. "
                "Do not include markdown or extra text. Just the raw JSON."
            )

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a crypto market forecaster."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up potential markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content)
        
        except Exception as e:
            logger.error(f"Error in generate_daily_forecast: {e}")
            return {"en": "Unable to generate forecast.", "ru": "Не удалось создать прогноз.", "uz": "Prognoz yaratib bo'lmadi."}
