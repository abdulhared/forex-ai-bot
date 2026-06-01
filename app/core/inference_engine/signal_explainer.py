# app/core/inference_engine/signal_explainer.py

from typing import List, Dict
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class SignalExplainer:
    """
    Explains why the bot took a trade.
    Takes the same features list and signal dict that signal_generator.py produces
    and returns a human readable breakdown for Telegram alerts.
    """
    
    def __init__(self):
        """Initialize signal explainer with no external dependencies."""
        self.logger = setup_logger()
    
    def explain(self, features: List[float], signal: Dict) -> Dict:
        """
        Generate explanation for a trading signal.
        
        Args:
            features: 20-element list of floats (same order as vector_assembler.py)
            signal: Dict from signal_generator.py containing:
                - pair, action, confidence, stop_loss, take_profit
                - risk_reward, lot_size, model_version, timestamp
                
        Returns:
            Dict with explanation details including confluence score and reasons
        """
        # Extract feature values using positions from vector_assembler.py
        # FEATURE_ORDER = [
        #     "rsi", "macd", "macd_signal",
        #     "ema9", "ema21", "ema50", "ema200",
        #     "atr", "bb_upper", "bb_mid", "bb_lower",
        #     "body_ratio", "upper_wick_ratio", "lower_wick_ratio",
        #     "support", "resistance",
        #     "sydney", "tokyo", "london", "new_york"
        # ]
        
        # Index mapping based on vector_assembler.py
        RSI_IDX = 0
        MACD_IDX = 1
        MACD_SIGNAL_IDX = 2
        EMA9_IDX = 3
        EMA21_IDX = 4
        EMA50_IDX = 5
        EMA200_IDX = 6
        ATR_IDX = 7
        BB_UPPER_IDX = 8
        BB_MID_IDX = 9
        BB_LOWER_IDX = 10
        BODY_RATIO_IDX = 11
        UPPER_WICK_IDX = 12
        LOWER_WICK_IDX = 13
        SUPPORT_IDX = 14
        RESISTANCE_IDX = 15
        SYDNEY_IDX = 16
        TOKYO_IDX = 17
        LONDON_IDX = 18
        NEW_YORK_IDX = 19
        
        # Extract values (handle potential index errors)
        try:
            rsi = features[RSI_IDX]
            macd = features[MACD_IDX]
            macd_signal = features[MACD_SIGNAL_IDX]
            ema9 = features[EMA9_IDX]
            ema21 = features[EMA21_IDX]
            ema50 = features[EMA50_IDX]
            ema200 = features[EMA200_IDX]
            atr = features[ATR_IDX]
            bb_upper = features[BB_UPPER_IDX]
            bb_mid = features[BB_MID_IDX]
            bb_lower = features[BB_LOWER_IDX]
            body_ratio = features[BODY_RATIO_IDX]
            upper_wick = features[UPPER_WICK_IDX]
            lower_wick = features[LOWER_WICK_IDX]
            support = features[SUPPORT_IDX]
            resistance = features[RESISTANCE_IDX]
            sydney = features[SYDNEY_IDX]
            tokyo = features[TOKYO_IDX]
            london = features[LONDON_IDX]
            new_york = features[NEW_YORK_IDX]
        except IndexError as e:
            self.logger.bind(category=LogCategory.ERROR.value).error(
                f"Feature index error: {e}. Features length: {len(features)}"
            )
            raise
        
        reasons = []
        
        # Factor 1: Trend Direction (EMA alignment)
        trend_score = 0
        trend_factors = []
        
        if signal["action"] == "BUY":
            # For BUY: EMA9 > EMA21 > EMA50 indicates uptrend
            if ema9 > ema21:
                trend_score += 1
                trend_factors.append("EMA9 above EMA21")
            if ema21 > ema50:
                trend_score += 1
                trend_factors.append("EMA21 above EMA50")
            if ema50 > ema200:
                trend_score += 1
                trend_factors.append("EMA50 above EMA200")
            # Price vs EMA200 (major trend)
            if ema9 > ema200:
                trend_score += 1
                trend_factors.append("Price above long-term EMA200")
        else:  # SELL
            # For SELL: EMA9 < EMA21 < EMA50 indicates downtrend
            if ema9 < ema21:
                trend_score += 1
                trend_factors.append("EMA9 below EMA21")
            if ema21 < ema50:
                trend_score += 1
                trend_factors.append("EMA21 below EMA50")
            if ema50 < ema200:
                trend_score += 1
                trend_factors.append("EMA50 below EMA200")
            if ema9 < ema200:
                trend_score += 1
                trend_factors.append("Price below long-term EMA200")
        
        # Normalize trend_score to 0-5
        trend_score_normalized = min(5, trend_score)
        if trend_factors:
            reasons.append({
                "factor": "Trend Direction",
                "score": trend_score_normalized,
                "details": ", ".join(trend_factors[:2])  # Keep message concise
            })
        else:
            reasons.append({
                "factor": "Trend Direction",
                "score": 2,
                "details": "Mixed or neutral EMA alignment"
            })
        
        # Factor 2: Momentum (RSI and MACD)
        momentum_score = 0
        momentum_details = []
        
        if signal["action"] == "BUY":
            # RSI: above 50 but not overbought (>70)
            if 50 <= rsi <= 70:
                momentum_score += 3
                momentum_details.append(f"RSI {rsi:.1f} (bullish momentum)")
            elif rsi > 70:
                momentum_score += 1
                momentum_details.append(f"RSI {rsi:.1f} (overbought - cautious)")
            elif rsi < 30:
                momentum_score += 0
                momentum_details.append(f"RSI {rsi:.1f} (oversold - contrarian)")
            else:
                momentum_score += 2
                momentum_details.append(f"RSI {rsi:.1f} (neutral)")
            
            # MACD: histogram positive (MACD > signal)
            if macd > macd_signal:
                momentum_score += 2
                momentum_details.append("MACD bullish (above signal)")
            else:
                momentum_score += 0
                momentum_details.append("MACD bearish (below signal)")
        else:  # SELL
            # RSI: below 50 but not oversold (<30)
            if 30 <= rsi <= 50:
                momentum_score += 3
                momentum_details.append(f"RSI {rsi:.1f} (bearish momentum)")
            elif rsi < 30:
                momentum_score += 1
                momentum_details.append(f"RSI {rsi:.1f} (oversold - cautious)")
            elif rsi > 70:
                momentum_score += 0
                momentum_details.append(f"RSI {rsi:.1f} (overbought - contrarian)")
            else:
                momentum_score += 2
                momentum_details.append(f"RSI {rsi:.1f} (neutral)")
            
            # MACD: histogram negative (MACD < signal)
            if macd < macd_signal:
                momentum_score += 2
                momentum_details.append("MACD bearish (below signal)")
            else:
                momentum_score += 0
                momentum_details.append("MACD bullish (above signal)")
        
        momentum_score_normalized = min(5, momentum_score)
        reasons.append({
            "factor": "Momentum",
            "score": momentum_score_normalized,
            "details": "; ".join(momentum_details[:2])
        })
        
        # Factor 3: Volatility (ATR and Bollinger Bands)
        volatility_score = 0
        volatility_details = []
        
        # Higher ATR means more volatility - good for trading
        if atr > 0.001:  # High volatility (e.g., >10 pips for EUR/USD)
            volatility_score += 3
            volatility_details.append(f"ATR {atr:.5f} (high volatility)")
        elif atr > 0.0005:
            volatility_score += 2
            volatility_details.append(f"ATR {atr:.5f} (moderate volatility)")
        else:
            volatility_score += 1
            volatility_details.append(f"ATR {atr:.5f} (low volatility)")
        
        # Bollinger Band position
        if signal["action"] == "BUY":
            if ema9 <= bb_mid:
                volatility_score += 1
                volatility_details.append("Price below BB middle (mean reversion potential)")
            if ema9 <= bb_lower:
                volatility_score += 1
                volatility_details.append("Price near BB lower (oversold bounce potential)")
        else:  # SELL
            if ema9 >= bb_mid:
                volatility_score += 1
                volatility_details.append("Price above BB middle (mean reversion potential)")
            if ema9 >= bb_upper:
                volatility_score += 1
                volatility_details.append("Price near BB upper (overbought pullback potential)")
        
        volatility_score_normalized = min(5, volatility_score)
        reasons.append({
            "factor": "Volatility",
            "score": volatility_score_normalized,
            "details": "; ".join(volatility_details[:2])
        })
        
        # Factor 4: Market Structure (Support/Resistance)
        structure_score = 0
        structure_details = []
        
        if signal["action"] == "BUY":
            if support > 0.5:  # Normalised support strength
                structure_score += 3
                structure_details.append(f"Strong support level (score: {support:.2f})")
            elif support > 0.2:
                structure_score += 2
                structure_details.append(f"Moderate support (score: {support:.2f})")
            else:
                structure_score += 1
                structure_details.append("Weak or no nearby support")
            
            # Candlestick pattern (bullish)
            if body_ratio > 0.6 and lower_wick > upper_wick:
                structure_score += 1
                structure_details.append("Bullish candlestick pattern")
        else:  # SELL
            if resistance > 0.5:
                structure_score += 3
                structure_details.append(f"Strong resistance level (score: {resistance:.2f})")
            elif resistance > 0.2:
                structure_score += 2
                structure_details.append(f"Moderate resistance (score: {resistance:.2f})")
            else:
                structure_score += 1
                structure_details.append("Weak or no nearby resistance")
            
            # Candlestick pattern (bearish)
            if body_ratio > 0.6 and upper_wick > lower_wick:
                structure_score += 1
                structure_details.append("Bearish candlestick pattern")
        
        structure_score_normalized = min(5, structure_score)
        reasons.append({
            "factor": "Market Structure",
            "score": structure_score_normalized,
            "details": "; ".join(structure_details[:2])
        })
        
        # Factor 5: Session Context (Market hours)
        session_score = 0
        session_details = []
        
        # Determine active sessions
        active_sessions = []
        if london > 0.5:
            active_sessions.append("London")
            session_score += 3
        if new_york > 0.5:
            active_sessions.append("New York")
            session_score += 3
        if tokyo > 0.5:
            active_sessions.append("Tokyo")
            session_score += 1
        if sydney > 0.5:
            active_sessions.append("Sydney")
            session_score += 1
        
        if active_sessions:
            session_details.append(f"Active sessions: {', '.join(active_sessions)}")
            if "London" in active_sessions or "New York" in active_sessions:
                session_details.append("High liquidity period")
        else:
            session_details.append("Low activity period (off-hours)")
            session_score = 1
        
        session_score_normalized = min(5, session_score)
        reasons.append({
            "factor": "Session Context",
            "score": session_score_normalized,
            "details": "; ".join(session_details)
        })
        
        # Calculate overall confluence score (average of factor scores)
        total_score = (trend_score_normalized + momentum_score_normalized + 
                      volatility_score_normalized + structure_score_normalized + 
                      session_score_normalized)
        confluence_score = total_score / 5  # 0-5 scale
        
        # Determine recommendation
        recommendation = "TAKE TRADE" if confluence_score >= 3.5 else "SKIP"
        
        # Build explanation dict
        explanation = {
            "pair": signal["pair"],
            "action": signal["action"],
            "confidence": signal["confidence"],
            "confluence_score": round(confluence_score, 2),
            "risk_reward": signal.get("risk_reward", 0),
            "reasons": reasons,
            "recommendation": recommendation,
            "timestamp": signal["timestamp"],
            "model_version": signal.get("model_version", "unknown")
        }
        
        self.logger.bind(category=LogCategory.SYSTEM.value).debug(
            f"Signal explanation generated for {signal['pair']}: "
            f"confluence={confluence_score:.2f}, {recommendation}"
        )
        
        return explanation
    
    def format_for_telegram(self, explanation: Dict) -> str:
        """
        Format explanation dict as a Telegram message string.
        
        Args:
            explanation: Dict from explain() method containing:
                - pair, action, confidence, confluence_score
                - risk_reward, reasons, recommendation, timestamp
                
        Returns:
            Formatted string for Telegram message
        """
        # Header with emoji based on action
        if explanation["action"] == "BUY":
            action_emoji = "🟢 BUY"
        elif explanation["action"] == "SELL":
            action_emoji = "🔴 SELL"
        else:
            action_emoji = "⚪ HOLD"
        
        # Recommendation emoji
        if explanation["recommendation"] == "TAKE TRADE":
            rec_emoji = "✅"
        else:
            rec_emoji = "⏸️"
        
        # Build message
        message_lines = [
            f"📊 **TRADE SIGNAL EXPLANATION**",
            f"",
            f"**{explanation['pair']}** | {action_emoji}",
            f"",
            f"📈 **Confidence:** {explanation['confidence']:.2%}",
            f"⭐ **Confluence Score:** {explanation['confluence_score']:.1f}/5.0",
            f"📐 **Risk/Reward:** {explanation['risk_reward']:.2f}",
            f"{rec_emoji} **Recommendation:** {explanation['recommendation']}",
            f"",
            f"🔍 **Factor Breakdown:**"
        ]
        
        # Add each factor with score bar
        for factor_data in explanation["reasons"]:
            factor = factor_data["factor"]
            score = factor_data["score"]
            details = factor_data.get("details", "")
            
            # Create visual score bar (5 characters max)
            score_bar = "█" * score + "░" * (5 - score)
            
            message_lines.append(f"  • **{factor}:** {score_bar} ({score}/5)")
            if details:
                message_lines.append(f"    _{details}_")
        
        message_lines.extend([
            f"",
            f"⏰ **Time:** {explanation['timestamp'][:19]}",  # Truncate milliseconds
            f"🤖 **Model:** {explanation.get('model_version', 'unknown')}"
        ])
        
        # Add footer note if confluence is low
        if explanation["confluence_score"] < 3.5:
            message_lines.append(f"")
            message_lines.append(f"⚠️ *Low confluence - consider manual review*")
        
        return "\n".join(message_lines)