"""
TokenScanner Service - Analyzes TON Jetton tokens for security risks.
Uses TonAPI for blockchain data and rule-based scoring.
"""

import aiohttp
from loguru import logger
from typing import Optional
from src.config import config


class TokenScanner:
    """Scans and analyzes TON Jetton tokens for security risks."""
    
    BASE_URL = "https://tonapi.io/v2"
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            headers = {"Accept": "application/json"}
            # Add API key if configured
            if hasattr(config, 'TONAPI_KEY') and config.TONAPI_KEY:
                headers["Authorization"] = f"Bearer {config.TONAPI_KEY.get_secret_value()}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def scan_token(self, address: str) -> Optional[dict]:
        """
        Fetch token data from TonAPI.
        
        Args:
            address: TON Jetton address (EQ... or UQ...)
            
        Returns:
            Dict with token data or None if not found
        """
        session = await self._get_session()
        
        try:
            # Fetch jetton metadata
            async with session.get(f"{self.BASE_URL}/jettons/{address}") as resp:
                if resp.status == 404:
                    return None
                if resp.status != 200:
                    logger.error(f"TonAPI error {resp.status}: {await resp.text()}")
                    return None
                jetton_data = await resp.json()
            
            # Fetch holders
            async with session.get(f"{self.BASE_URL}/jettons/{address}/holders?limit=10") as resp:
                if resp.status == 200:
                    holders_data = await resp.json()
                else:
                    holders_data = {"addresses": []}
            
            # Extract metadata
            metadata = jetton_data.get("metadata", {})
            
            # Calculate total supply in proper units
            total_supply_raw = int(jetton_data.get("total_supply", "0"))
            decimals = int(metadata.get("decimals", 9))
            total_supply = total_supply_raw / (10 ** decimals)
            
            # Extract holder info
            holders = holders_data.get("addresses", [])
            top_holders = []
            
            for holder in holders[:5]:
                balance_raw = int(holder.get("balance", "0"))
                balance = balance_raw / (10 ** decimals)
                percentage = (balance / total_supply * 100) if total_supply > 0 else 0
                
                owner = holder.get("owner", {})
                owner_address = owner.get("address", "Unknown")
                owner_name = owner.get("name", None)
                
                top_holders.append({
                    "address": owner_address,
                    "name": owner_name,
                    "balance": balance,
                    "percentage": round(percentage, 2)
                })
            
            return {
                "name": metadata.get("name", "Unknown"),
                "symbol": metadata.get("symbol", "???"),
                "decimals": decimals,
                "description": metadata.get("description", ""),
                "image": metadata.get("image", ""),
                "total_supply": total_supply,
                "admin_address": jetton_data.get("admin", {}).get("address"),
                "mintable": jetton_data.get("mintable", False),
                "verified": jetton_data.get("verification") == "whitelist",
                "holders_count": jetton_data.get("holders_count", 0),
                "top_holders": top_holders,
                "address": address
            }
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching token {address}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scanning token {address}: {e}")
            return None
    
    def analyze_security(self, token_data: dict) -> dict:
        """
        Perform rule-based security analysis on token data.
        
        Args:
            token_data: Token data from scan_token()
            
        Returns:
            Dict with security analysis results
        """
        score = 10  # Start with perfect score
        findings = []
        
        # Check admin rights (HIGH RISK)
        if token_data.get("admin_address"):
            score -= 3
            findings.append({
                "severity": "🔴 HIGH",
                "text": "Admin rights NOT revoked - can mint tokens or change code"
            })
        
        # Check mintable status
        if token_data.get("mintable"):
            if not token_data.get("admin_address"):
                # Mintable but no admin - still notable
                score -= 1
                findings.append({
                    "severity": "🟡 MEDIUM",
                    "text": "Token is mintable (supply can increase)"
                })
        
        # Check verification status
        if not token_data.get("verified"):
            score -= 2
            findings.append({
                "severity": "🟡 MEDIUM", 
                "text": "Token is NOT verified on TON blockchain"
            })
        else:
            findings.append({
                "severity": "🟢 SAFE",
                "text": "Token is officially verified ✓"
            })
        
        # Check holder concentration
        top_holders = token_data.get("top_holders", [])
        
        if top_holders:
            # Top 1 holder concentration
            top1_pct = top_holders[0].get("percentage", 0) if top_holders else 0
            if top1_pct > 50:
                score -= 3
                findings.append({
                    "severity": "🔴 HIGH",
                    "text": f"Top holder owns {top1_pct:.1f}% of supply (WHALE RISK)"
                })
            elif top1_pct > 20:
                score -= 1
                findings.append({
                    "severity": "🟡 MEDIUM",
                    "text": f"Top holder owns {top1_pct:.1f}% of supply"
                })
            
            # Top 5 concentration
            top5_pct = sum(h.get("percentage", 0) for h in top_holders[:5])
            if top5_pct > 80:
                score -= 2
                findings.append({
                    "severity": "🔴 HIGH",
                    "text": f"Top 5 holders own {top5_pct:.1f}% (HIGH centralization)"
                })
            elif top5_pct > 50:
                score -= 1
                findings.append({
                    "severity": "🟡 MEDIUM",
                    "text": f"Top 5 holders own {top5_pct:.1f}% of supply"
                })
        
        # Ensure score stays in bounds
        score = max(0, min(10, score))
        
        # Determine risk level
        if score >= 8:
            risk_level = "🟢 LOW"
            recommendation = "Relatively safe, standard precautions apply"
        elif score >= 5:
            risk_level = "🟡 MEDIUM"
            recommendation = "Proceed with caution, DYOR"
        else:
            risk_level = "🔴 CRITICAL"
            recommendation = "High risk detected, consider avoiding"
        
        return {
            "score": score,
            "max_score": 10,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "findings": findings,
            "token_info": {
                "name": token_data.get("name"),
                "symbol": token_data.get("symbol"),
                "verified": token_data.get("verified"),
                "holders_count": token_data.get("holders_count"),
                "total_supply": token_data.get("total_supply")
            }
        }
    
    def format_audit_report(self, analysis: dict, lang: str = "en") -> str:
        """
        Format the security analysis as a user-friendly message.
        
        Args:
            analysis: Security analysis from analyze_security()
            lang: Language code for localization
            
        Returns:
            Formatted HTML message string
        """
        token_info = analysis.get("token_info", {})
        
        # Format supply with commas
        total_supply = token_info.get("total_supply", 0)
        if total_supply >= 1_000_000_000:
            supply_str = f"{total_supply/1_000_000_000:.2f}B"
        elif total_supply >= 1_000_000:
            supply_str = f"{total_supply/1_000_000:.2f}M"
        elif total_supply >= 1_000:
            supply_str = f"{total_supply/1_000:.2f}K"
        else:
            supply_str = f"{total_supply:.2f}"
        
        # Build findings text
        findings_text = "\n".join([
            f"  • {f['severity']}: {f['text']}" 
            for f in analysis.get("findings", [])
        ])
        
        # Headers by language
        headers = {
            "en": "🔍 TOKEN SECURITY AUDIT",
            "ru": "🔍 АУДИТ БЕЗОПАСНОСТИ ТОКЕНА",
            "uz": "🔍 TOKEN XAVFSIZLIK AUDITI"
        }
        
        labels = {
            "en": {
                "score": "Security Score",
                "risk": "Risk Level", 
                "findings": "Key Findings",
                "recommendation": "Recommendation",
                "supply": "Total Supply",
                "holders": "Holders"
            },
            "ru": {
                "score": "Оценка безопасности",
                "risk": "Уровень риска",
                "findings": "Ключевые выводы",
                "recommendation": "Рекомендация",
                "supply": "Общий выпуск",
                "holders": "Держатели"
            },
            "uz": {
                "score": "Xavfsizlik bahosi",
                "risk": "Xavf darajasi",
                "findings": "Asosiy topilmalar", 
                "recommendation": "Tavsiya",
                "supply": "Jami ta'minot",
                "holders": "Egalar"
            }
        }
        
        l = labels.get(lang, labels["en"])
        header = headers.get(lang, headers["en"])
        
        verified_badge = "✅" if token_info.get("verified") else "❌"
        
        report = (
            f"<b>{header}</b>\n\n"
            f"<b>{token_info.get('name', 'Unknown')}</b> ({token_info.get('symbol', '???')}) {verified_badge}\n\n"
            f"🛡️ <b>{l['score']}:</b> {analysis['score']}/{analysis['max_score']}\n"
            f"⚠️ <b>{l['risk']}:</b> {analysis['risk_level']}\n\n"
            f"📊 <b>{l['findings']}:</b>\n{findings_text}\n\n"
            f"💡 <b>{l['recommendation']}:</b> {analysis['recommendation']}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📈 {l['supply']}: <code>{supply_str}</code>\n"
            f"👥 {l['holders']}: <code>{token_info.get('holders_count', 0):,}</code>"
        )
        
        return report
