#!/usr/bin/env python3
"""
Track earnings dates and major events for Nvidia supply chain
Monitor upcoming catalysts and historical earnings impacts
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import requests

def get_earnings_calendar(tickers):
    """Fetch upcoming earnings dates for tickers"""
    earnings_data = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            
            # Get earnings dates
            if hasattr(stock, 'calendar') and stock.calendar is not None:
                calendar = stock.calendar
                
                # Extract earnings date
                if 'Earnings Date' in calendar.index:
                    earnings_date = calendar.loc['Earnings Date']
                    if isinstance(earnings_date, pd.Series):
                        earnings_date = earnings_date.iloc[0] if len(earnings_date) > 0 else None
                    
                    earnings_data[ticker] = {
                        "next_earnings": earnings_date.strftime('%Y-%m-%d') if pd.notna(earnings_date) else None,
                        "revenue_estimate": calendar.loc['Revenue Estimate'].iloc[0] if 'Revenue Estimate' in calendar.index else None,
                        "earnings_estimate": calendar.loc['Earnings Estimate'].iloc[0] if 'Earnings Estimate' in calendar.index else None
                    }
                else:
                    earnings_data[ticker] = {"next_earnings": None}
            
            # Get historical earnings
            if hasattr(stock, 'earnings_history'):
                earnings_hist = stock.earnings_history
                if earnings_hist is not None and not earnings_hist.empty:
                    recent_earnings = earnings_hist.tail(4).to_dict('records')
                    earnings_data[ticker]["recent_earnings"] = recent_earnings
                    
                    # Calculate average surprise
                    if 'epsestimate' in earnings_hist.columns and 'epsactual' in earnings_hist.columns:
                        surprises = ((earnings_hist['epsactual'] - earnings_hist['epsestimate']) / 
                                   earnings_hist['epsestimate'] * 100)
                        earnings_data[ticker]["avg_surprise"] = surprises.mean()
            
        except Exception as e:
            earnings_data[ticker] = {"error": str(e)}
    
    return earnings_data

def analyze_earnings_impact(ticker, lookback_quarters=8):
    """Analyze historical price impact around earnings"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get earnings history
        if not hasattr(stock, 'earnings_dates') or stock.earnings_dates is None:
            return {"error": "No earnings history available"}
        
        earnings_dates = stock.earnings_dates
        if earnings_dates.empty:
            return {"error": "No earnings dates found"}
        
        # Get price history
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_quarters * 90)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            return {"error": "No price history available"}
        
        impacts = []
        
        # Analyze each earnings date
        for earnings_date in earnings_dates.index[:lookback_quarters]:
            if pd.isna(earnings_date):
                continue
                
            # Convert to datetime if needed
            if not isinstance(earnings_date, pd.Timestamp):
                earnings_date = pd.Timestamp(earnings_date)
            
            # Find prices around earnings
            before_date = earnings_date - timedelta(days=5)
            after_date = earnings_date + timedelta(days=5)
            
            # Get closest available prices
            before_prices = hist.loc[before_date:earnings_date]['Close']
            after_prices = hist.loc[earnings_date:after_date]['Close']
            
            if len(before_prices) > 0 and len(after_prices) > 1:
                pre_earnings_price = before_prices.iloc[-1]
                post_earnings_price = after_prices.iloc[1] if len(after_prices) > 1 else after_prices.iloc[0]
                
                impact = ((post_earnings_price / pre_earnings_price - 1) * 100)
                
                impacts.append({
                    "date": earnings_date.strftime('%Y-%m-%d'),
                    "pre_price": pre_earnings_price,
                    "post_price": post_earnings_price,
                    "impact_pct": impact,
                    "direction": "positive" if impact > 0 else "negative"
                })
        
        # Calculate statistics
        if impacts:
            impact_values = [i["impact_pct"] for i in impacts]
            avg_impact = sum(impact_values) / len(impact_values)
            max_impact = max(impact_values)
            min_impact = min(impact_values)
            positive_ratio = len([i for i in impact_values if i > 0]) / len(impact_values)
            
            return {
                "ticker": ticker,
                "earnings_impacts": impacts,
                "statistics": {
                    "average_move": avg_impact,
                    "max_gain": max_impact,
                    "max_loss": min_impact,
                    "positive_earnings_ratio": positive_ratio,
                    "typical_volatility": abs(avg_impact)
                }
            }
        
        return {"error": "Insufficient earnings data"}
        
    except Exception as e:
        return {"error": str(e)}

def identify_catalyst_clusters(earnings_calendar):
    """Identify periods with multiple earnings releases"""
    clusters = []
    dated_earnings = []
    
    # Collect all earnings with dates
    for ticker, data in earnings_calendar.items():
        if data.get("next_earnings"):
            try:
                date = pd.to_datetime(data["next_earnings"])
                dated_earnings.append({
                    "ticker": ticker,
                    "date": date,
                    "data": data
                })
            except:
                continue
    
    # Sort by date
    dated_earnings.sort(key=lambda x: x["date"])
    
    # Find clusters (multiple earnings within 7 days)
    i = 0
    while i < len(dated_earnings):
        cluster_start = dated_earnings[i]["date"]
        cluster_end = cluster_start + timedelta(days=7)
        cluster_tickers = []
        
        j = i
        while j < len(dated_earnings) and dated_earnings[j]["date"] <= cluster_end:
            cluster_tickers.append(dated_earnings[j]["ticker"])
            j += 1
        
        if len(cluster_tickers) > 1:
            clusters.append({
                "period": f"{cluster_start.strftime('%Y-%m-%d')} to {cluster_end.strftime('%Y-%m-%d')}",
                "tickers": cluster_tickers,
                "count": len(cluster_tickers)
            })
        
        i = j if j > i else i + 1
    
    return clusters

def get_insider_sentiment(ticker):
    """Fetch insider trading data as a sentiment indicator"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get insider transactions
        if hasattr(stock, 'insider_transactions'):
            transactions = stock.insider_transactions
            
            if transactions is not None and not transactions.empty:
                recent = transactions.head(10)
                
                # Calculate buy/sell ratio
                buys = len(recent[recent['Transaction'] == 'Buy'])
                sells = len(recent[recent['Transaction'] == 'Sale'])
                
                # Calculate value flows
                if 'Value' in recent.columns:
                    buy_value = recent[recent['Transaction'] == 'Buy']['Value'].sum()
                    sell_value = abs(recent[recent['Transaction'] == 'Sale']['Value'].sum())
                else:
                    buy_value = 0
                    sell_value = 0
                
                return {
                    "recent_buys": buys,
                    "recent_sells": sells,
                    "buy_sell_ratio": buys / (sells + 1),  # Avoid division by zero
                    "net_value_flow": buy_value - sell_value,
                    "sentiment": "bullish" if buys > sells else "bearish" if sells > buys else "neutral"
                }
        
        return {"sentiment": "no_data"}
        
    except Exception as e:
        return {"error": str(e)}

def compile_event_calendar(tickers):
    """Compile comprehensive event calendar for supply chain"""
    
    # Get earnings calendar
    earnings = get_earnings_calendar(tickers)
    
    # Identify catalyst clusters
    clusters = identify_catalyst_clusters(earnings)
    
    # Analyze historical impacts
    impact_analysis = {}
    for ticker in tickers[:5]:  # Analyze top 5 to save time
        impact_analysis[ticker] = analyze_earnings_impact(ticker, lookback_quarters=4)
    
    # Get insider sentiment
    insider_sentiment = {}
    for ticker in tickers[:5]:  # Top 5 for efficiency
        insider_sentiment[ticker] = get_insider_sentiment(ticker)
    
    # Compile timeline
    timeline = []
    for ticker, data in earnings.items():
        if data.get("next_earnings"):
            timeline.append({
                "date": data["next_earnings"],
                "ticker": ticker,
                "event": "earnings",
                "estimates": {
                    "revenue": data.get("revenue_estimate"),
                    "earnings": data.get("earnings_estimate")
                },
                "historical_impact": impact_analysis.get(ticker, {}).get("statistics", {}).get("average_move"),
                "insider_sentiment": insider_sentiment.get(ticker, {}).get("sentiment")
            })
    
    # Sort timeline
    timeline.sort(key=lambda x: x["date"] if x["date"] else "9999-12-31")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "upcoming_events": timeline[:10],  # Next 10 events
        "catalyst_clusters": clusters,
        "historical_impacts": impact_analysis,
        "insider_sentiment": insider_sentiment
    }

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Track supply chain events and earnings')
    parser.add_argument('--ticker', help='Analyze specific ticker')
    parser.add_argument('--calendar', action='store_true', help='Show full calendar')
    
    args = parser.parse_args()
    
    # Default tickers
    SUPPLY_CHAIN = ["NVDA", "TSM", "ASML", "AMAT", "LRCX", "MU", "SMCI"]
    
    if args.ticker:
        # Single ticker analysis
        earnings = get_earnings_calendar([args.ticker])
        impact = analyze_earnings_impact(args.ticker)
        sentiment = get_insider_sentiment(args.ticker)
        
        result = {
            "earnings": earnings.get(args.ticker),
            "historical_impact": impact,
            "insider_sentiment": sentiment
        }
        print(json.dumps(result, indent=2, default=str))
        
    else:
        # Full calendar
        calendar = compile_event_calendar(SUPPLY_CHAIN)
        
        if args.calendar:
            print(json.dumps(calendar, indent=2, default=str))
        else:
            # Summary view
            print("\n=== SUPPLY CHAIN EVENT CALENDAR ===")
            print(f"Generated: {calendar['timestamp']}")
            
            print("\n--- UPCOMING EARNINGS ---")
            for event in calendar['upcoming_events'][:5]:
                impact = event.get('historical_impact', 0) or 0
                sentiment = event.get('insider_sentiment', 'unknown')
                print(f"{event['date']}: {event['ticker']} - Avg move: {impact:.1f}%, Insider: {sentiment}")
            
            print("\n--- CATALYST CLUSTERS ---")
            for cluster in calendar['catalyst_clusters']:
                print(f"{cluster['period']}: {cluster['count']} earnings - {', '.join(cluster['tickers'])}")
            
            print("\n--- INSIDER SENTIMENT ---")
            for ticker, sentiment in calendar['insider_sentiment'].items():
                if 'error' not in sentiment:
                    print(f"{ticker}: {sentiment.get('sentiment', 'unknown')} (B/S ratio: {sentiment.get('buy_sell_ratio', 0):.1f})")

if __name__ == "__main__":
    main()
