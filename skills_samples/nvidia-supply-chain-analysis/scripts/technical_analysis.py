#!/usr/bin/env python3
"""
Technical analysis for Nvidia supply chain stocks
Identifies trading signals, patterns, and momentum indicators
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def identify_support_resistance(prices, window=20):
    """Identify support and resistance levels"""
    # Find local maxima and minima
    highs = prices.rolling(window=window).max()
    lows = prices.rolling(window=window).min()
    
    # Get unique levels
    resistance_levels = highs.dropna().unique()[-5:]  # Last 5 resistance levels
    support_levels = lows.dropna().unique()[:5]  # First 5 support levels
    
    return support_levels, resistance_levels

def analyze_volume_profile(volume, prices):
    """Analyze volume patterns"""
    avg_volume = volume.mean()
    volume_surge = volume[-1] / avg_volume if avg_volume > 0 else 0
    
    # Price-volume correlation
    price_changes = prices.pct_change()
    volume_changes = volume.pct_change()
    correlation = price_changes.corr(volume_changes)
    
    return {
        "current_vs_avg": volume_surge,
        "price_volume_correlation": correlation,
        "unusual_volume": volume_surge > 1.5
    }

def detect_patterns(prices, volume):
    """Detect common chart patterns"""
    patterns = []
    
    # Recent data
    recent_prices = prices[-20:]
    recent_volume = volume[-20:]
    
    if len(recent_prices) >= 20:
        # Breakout detection
        resistance = recent_prices[-20:-10].max()
        if prices[-1] > resistance * 1.02:  # 2% above resistance
            patterns.append({
                "pattern": "breakout",
                "level": resistance,
                "strength": "strong" if recent_volume[-1] > recent_volume.mean() * 1.5 else "weak"
            })
        
        # Breakdown detection
        support = recent_prices[-20:-10].min()
        if prices[-1] < support * 0.98:  # 2% below support
            patterns.append({
                "pattern": "breakdown",
                "level": support,
                "strength": "strong" if recent_volume[-1] > recent_volume.mean() * 1.5 else "weak"
            })
        
        # Trend detection
        sma_5 = recent_prices[-5:].mean()
        sma_20 = recent_prices.mean()
        
        if sma_5 > sma_20 * 1.01:
            patterns.append({"pattern": "uptrend", "strength": "confirmed"})
        elif sma_5 < sma_20 * 0.99:
            patterns.append({"pattern": "downtrend", "strength": "confirmed"})
    
    return patterns

def generate_signals(ticker, period="3mo"):
    """Generate trading signals for a ticker"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if len(hist) < 30:
            return {"error": "Insufficient data"}
        
        prices = hist['Close']
        volume = hist['Volume']
        
        # Calculate indicators
        rsi = calculate_rsi(prices)
        macd_line, signal_line, histogram = calculate_macd(prices)
        upper_band, middle_band, lower_band = calculate_bollinger_bands(prices)
        support, resistance = identify_support_resistance(prices)
        volume_analysis = analyze_volume_profile(volume, prices)
        patterns = detect_patterns(prices, volume)
        
        # Current values
        current_price = prices[-1]
        current_rsi = rsi[-1]
        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        
        # Generate signals
        signals = {
            "ticker": ticker,
            "current_price": current_price,
            "timestamp": datetime.now().isoformat(),
            "indicators": {
                "rsi": current_rsi,
                "macd": current_macd,
                "macd_signal": current_signal,
                "bollinger_position": "above" if current_price > upper_band[-1] else "below" if current_price < lower_band[-1] else "within",
                "volume_analysis": volume_analysis
            },
            "levels": {
                "nearest_support": max([s for s in support if s < current_price], default=None),
                "nearest_resistance": min([r for r in resistance if r > current_price], default=None)
            },
            "patterns": patterns,
            "signals": []
        }
        
        # RSI signals
        if current_rsi < 30:
            signals["signals"].append({
                "type": "oversold",
                "indicator": "RSI",
                "value": current_rsi,
                "action": "potential_buy"
            })
        elif current_rsi > 70:
            signals["signals"].append({
                "type": "overbought",
                "indicator": "RSI",
                "value": current_rsi,
                "action": "potential_sell"
            })
        
        # MACD signals
        if current_macd > current_signal and histogram[-1] > histogram[-2]:
            signals["signals"].append({
                "type": "bullish_crossover",
                "indicator": "MACD",
                "action": "buy_signal"
            })
        elif current_macd < current_signal and histogram[-1] < histogram[-2]:
            signals["signals"].append({
                "type": "bearish_crossover",
                "indicator": "MACD",
                "action": "sell_signal"
            })
        
        # Bollinger Band signals
        if current_price < lower_band[-1]:
            signals["signals"].append({
                "type": "bollinger_oversold",
                "indicator": "Bollinger",
                "action": "potential_bounce"
            })
        elif current_price > upper_band[-1]:
            signals["signals"].append({
                "type": "bollinger_overbought",
                "indicator": "Bollinger",
                "action": "potential_reversal"
            })
        
        # Volume signals
        if volume_analysis["unusual_volume"]:
            signals["signals"].append({
                "type": "volume_surge",
                "indicator": "Volume",
                "value": volume_analysis["current_vs_avg"],
                "action": "increased_interest"
            })
        
        # Momentum calculation
        momentum_1w = (prices[-1] / prices[-5] - 1) * 100 if len(prices) > 5 else None
        momentum_1m = (prices[-1] / prices[-20] - 1) * 100 if len(prices) > 20 else None
        
        signals["momentum"] = {
            "1_week": momentum_1w,
            "1_month": momentum_1m
        }
        
        return signals
        
    except Exception as e:
        return {"error": str(e)}

def scan_supply_chain(tickers, period="3mo"):
    """Scan all supply chain stocks for signals"""
    all_signals = {}
    buy_signals = []
    sell_signals = []
    momentum_leaders = []
    
    for ticker in tickers:
        signals = generate_signals(ticker, period)
        
        if "error" not in signals:
            all_signals[ticker] = signals
            
            # Categorize signals
            for signal in signals.get("signals", []):
                if signal.get("action") in ["potential_buy", "buy_signal", "potential_bounce"]:
                    buy_signals.append({
                        "ticker": ticker,
                        "price": signals["current_price"],
                        "signal": signal
                    })
                elif signal.get("action") in ["potential_sell", "sell_signal", "potential_reversal"]:
                    sell_signals.append({
                        "ticker": ticker,
                        "price": signals["current_price"],
                        "signal": signal
                    })
            
            # Track momentum
            if signals.get("momentum", {}).get("1_week"):
                momentum_leaders.append({
                    "ticker": ticker,
                    "1w_momentum": signals["momentum"]["1_week"],
                    "1m_momentum": signals["momentum"].get("1_month")
                })
    
    # Sort momentum leaders
    momentum_leaders.sort(key=lambda x: x["1w_momentum"], reverse=True)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "detailed_signals": all_signals,
        "summary": {
            "buy_opportunities": buy_signals[:5],  # Top 5
            "sell_signals": sell_signals[:5],
            "momentum_leaders": momentum_leaders[:5],
            "total_scanned": len(tickers),
            "signals_found": len(buy_signals) + len(sell_signals)
        }
    }

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Technical analysis for Nvidia supply chain')
    parser.add_argument('--ticker', help='Analyze specific ticker')
    parser.add_argument('--period', default='3mo', help='Analysis period')
    parser.add_argument('--scan', action='store_true', help='Scan all supply chain stocks')
    
    args = parser.parse_args()
    
    # Default supply chain tickers
    SUPPLY_CHAIN = ["NVDA", "TSM", "ASML", "AMAT", "LRCX", "KLAC", "MU", "SMCI", "AMKR"]
    
    if args.scan:
        results = scan_supply_chain(SUPPLY_CHAIN, args.period)
        print(json.dumps(results, indent=2, default=str))
    elif args.ticker:
        signals = generate_signals(args.ticker, args.period)
        print(json.dumps(signals, indent=2, default=str))
    else:
        # Default: scan all
        results = scan_supply_chain(SUPPLY_CHAIN, args.period)
        
        # Print summary
        print("\n=== SUPPLY CHAIN TECHNICAL ANALYSIS ===")
        print(f"Scanned: {results['summary']['total_scanned']} stocks")
        print(f"Signals found: {results['summary']['signals_found']}")
        
        print("\n--- BUY OPPORTUNITIES ---")
        for opp in results['summary']['buy_opportunities']:
            print(f"{opp['ticker']} @ ${opp['price']:.2f} - {opp['signal']['type']}")
        
        print("\n--- MOMENTUM LEADERS ---")
        for leader in results['summary']['momentum_leaders']:
            print(f"{leader['ticker']}: 1W={leader['1w_momentum']:.1f}%, 1M={leader['1m_momentum']:.1f}%")

if __name__ == "__main__":
    main()
