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

    async def analyze_news(self, text: str, lang: str = "en") -> dict:
        """
        Analyzes news text to extract key info and stores it in memory.
        """
        lang_name = {"en": "English", "ru": "Russian", "uz": "Uzbek"}.get(lang, "English")
        system_prompt = (
            f"You are an expert crypto analyst specializing in the TON ecosystem. "
            f"Analyze the input news. Extract key entities, sentiment (Bullish/Bearish/Neutral), "
            f"and identify any specific dates mentioned. "
            f"Also provide a 'short_description': a 1-2 sentence engaging summary of why this is important for a trader/investor. "
            f"Return the result as a valid JSON string with keys: 'entities', 'sentiment', 'dates', 'short_description'. "
            f"Do not include markdown formatting like ```json ... ```, just the raw JSON. "
            f"Respond in {lang_name}."
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"News:\n{text}"}
                ]
            )
            
            analysis_json = response.choices[0].message.content.strip()
            # Clean up potential markdown code blocks if the model ignores instruction
            if analysis_json.startswith("```json"):
                analysis_json = analysis_json[7:]
            if analysis_json.endswith("```"):
                analysis_json = analysis_json[:-3]
            
            analysis_dict = json.loads(analysis_json)
            
            # Store in memory
            metadata = {
                "type": "news_analysis",
                "sentiment": analysis_dict.get("sentiment", "Neutral"),
                # Flatten lists for metadata compatibility if needed, or store as string
                "entities": ", ".join(analysis_dict.get("entities", [])),
                "dates": ", ".join(analysis_dict.get("dates", []))
            }
            
            # We store the original text combined with the analysis summary for better retrieval context
            # Fallback to empty string if short_description is missing, but check for old 'summary' key just in case
            summary_text = analysis_dict.get('short_description') or analysis_dict.get('summary', '')
            memory_content = f"News: {text}\nAnalysis: {summary_text}"
            
            await self.memory_service.add_memory(text=memory_content, metadata=metadata)
            
            return analysis_dict

        except Exception as e:
            logger.error(f"Error in analyze_news: {e}")
            return {}

    async def generate_daily_forecast(self, market_data: str, lang: str = "en") -> str:
        """
        Generates a daily forecast using RAG (Upcoming events) and current market data.
        """
        lang_name = {"en": "English", "ru": "Russian", "uz": "Uzbek"}.get(lang, "English")
        try:
            # 1. Retrieve relevant context
            query = "Upcoming events for TON"
            rag_results = await self.memory_service.query_memory(query, n_results=5)
            
            # Extract documents from results
            memories = []
            if rag_results and 'documents' in rag_results:
                for doc_list in rag_results['documents']:
                    memories.extend(doc_list)
            
            context_str = "\n".join(memories) if memories else "No specific upcoming events found in memory."

            # 2. Prompt OpenRouter
            prompt = (
                f"Context (Known Events/News):\n{context_str}\n\n"
                f"Current Market Data:\n{market_data}\n\n"
                "Based on the historical context, upcoming events, and current market data, "
                f"predict the market trend for the day for TON. Be specific and logical. Respond in {lang_name}."
            )

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a crypto market forecaster."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error in generate_daily_forecast: {e}")
            return "Unable to generate forecast due to an error."
