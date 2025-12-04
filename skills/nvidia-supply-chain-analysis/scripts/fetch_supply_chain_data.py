#!/usr/bin/env python3
"""
Fetch and analyze Nvidia supply chain stock data
This script retrieves current and historical data for Nvidia and its key suppliers
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys

# Key Nvidia supply chain companies and their relationships
NVIDIA_ECOSYSTEM = {
    "NVDA": {
        "name": "NVIDIA Corporation",
        "role": "Primary company",
        "category": "GPU Designer"
    },
    "TSM": {
        "name": "Taiwan Semiconductor Manufacturing",
        "role": "Primary chip manufacturer",
        "category": "Foundry",
        "relationship": "Manufactures all advanced GPUs (4nm, 5nm nodes)"
    },
    "ASML": {
        "name": "ASML Holding",
        "role": "EUV lithography equipment",
        "category": "Equipment Supplier",
        "relationship": "Supplies critical lithography to TSMC"
    },
    "AMAT": {
        "name": "Applied Materials",
        "role": "Semiconductor equipment",
        "category": "Equipment Supplier",
        "relationship": "Provides manufacturing equipment"
    },
    "LRCX": {
        "name": "Lam Research",
        "role": "Wafer fabrication equipment",
        "category": "Equipment Supplier",
        "relationship": "Etching and deposition equipment"
    },
    "KLAC": {
        "name": "KLA Corporation",
        "role": "Process control equipment",
        "category": "Equipment Supplier",
        "relationship": "Inspection and metrology"
    },
    "SK": {
        "name": "SK Hynix",
        "role": "HBM memory supplier",
        "category": "Memory Supplier",
        "relationship": "Supplies HBM3 memory for AI GPUs"
    },
    "MU": {
        "name": "Micron Technology",
        "role": "Memory supplier",
        "category": "Memory Supplier",
        "relationship": "Alternative HBM supplier"
    },
    "AMKR": {
        "name": "Amkor Technology",
        "role": "Packaging and test",
        "category": "OSAT",
        "relationship": "Advanced packaging for GPUs"
    },
    "ASX": {
        "name": "ASE Group",
        "role": "Assembly and test",
        "category": "OSAT",
        "relationship": "IC packaging services"
    },
    "SMCI": {
        "name": "Super Micro Computer",
        "role": "Server systems",
        "category": "System Integrator",
        "relationship": "AI server manufacturer using Nvidia GPUs"
    },
    "DELL": {
        "name": "Dell Technologies",
        "role": "Enterprise systems",
        "category": "System Integrator",
        "relationship": "Enterprise AI infrastructure"
    },
    "HPE": {
        "name": "Hewlett Packard Enterprise",
        "role": "Enterprise systems",
        "category": "System Integrator",
        "relationship": "HPC and AI systems"
    }
}

def fetch_stock_data(tickers, period="3mo"):
    """
    Fetch stock data for multiple tickers
    
    Args:
        tickers: List of stock tickers
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        Dictionary with ticker data
    """
    data = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            
            # Get historical data
            hist = stock.history(period=period)
            
            # Get current info
            info = stock.info
            
            # Calculate metrics
            current_price = hist['Close'][-1] if len(hist) > 0 else None
            start_price = hist['Close'][0] if len(hist) > 0 else None
            
            data[ticker] = {
                "current_price": current_price,
                "period_return": ((current_price / start_price - 1) * 100) if current_price and start_price else None,
                "volatility": hist['Close'].pct_change().std() * np.sqrt(252) * 100 if len(hist) > 1 else None,
                "volume_avg": hist['Volume'].mean() if len(hist) > 0 else None,
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "beta": info.get('beta'),
                "52w_high": info.get('fiftyTwoWeekHigh'),
                "52w_low": info.get('fiftyTwoWeekLow'),
                "history": hist.to_dict() if len(hist) > 0 else None
            }
            
        except Exception as e:
            print(f"Error fetching {ticker}: {e}", file=sys.stderr)
            data[ticker] = {"error": str(e)}
    
    return data

def calculate_correlations(tickers, period="3mo"):
    """
    Calculate price correlations between stocks
    
    Args:
        tickers: List of stock tickers
        period: Time period for correlation calculation
    
    Returns:
        Correlation matrix as DataFrame
    """
    price_data = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if len(hist) > 0:
                price_data[ticker] = hist['Close']
        except Exception as e:
            print(f"Error fetching {ticker} for correlation: {e}", file=sys.stderr)
    
    if price_data:
        df = pd.DataFrame(price_data)
        # Calculate returns
        returns = df.pct_change().dropna()
        # Calculate correlation
        correlation = returns.corr()
        return correlation
    
    return None

def analyze_supply_chain_impact(reference_ticker="NVDA"):
    """
    Analyze the impact and relationships within the supply chain
    
    Args:
        reference_ticker: The main ticker to compare others against
    
    Returns:
        Analysis results
    """
    tickers = list(NVIDIA_ECOSYSTEM.keys())
    
    # Fetch data
    print("Fetching stock data...", file=sys.stderr)
    stock_data = fetch_stock_data(tickers)
    
    # Calculate correlations
    print("Calculating correlations...", file=sys.stderr)
    correlations = calculate_correlations(tickers)
    
    # Analyze results
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "reference": reference_ticker,
        "supply_chain": {},
        "correlations": {},
        "momentum_indicators": {},
        "risk_indicators": []
    }
    
    # Process each company
    for ticker, info in NVIDIA_ECOSYSTEM.items():
        if ticker in stock_data and not stock_data[ticker].get("error"):
            data = stock_data[ticker]
            
            analysis["supply_chain"][ticker] = {
                "name": info["name"],
                "role": info["role"],
                "category": info["category"],
                "relationship": info.get("relationship", ""),
                "current_price": data.get("current_price"),
                "3m_return": data.get("period_return"),
                "volatility": data.get("volatility"),
                "market_cap": data.get("market_cap"),
                "pe_ratio": data.get("pe_ratio"),
                "beta": data.get("beta")
            }
            
            # Add correlation to NVDA
            if correlations is not None and ticker in correlations.columns and reference_ticker in correlations.columns:
                analysis["correlations"][ticker] = float(correlations.loc[ticker, reference_ticker])
    
    # Identify momentum leaders/laggards
    returns = [(t, analysis["supply_chain"][t]["3m_return"]) 
               for t in analysis["supply_chain"] 
               if analysis["supply_chain"][t].get("3m_return") is not None]
    
    returns_sorted = sorted(returns, key=lambda x: x[1], reverse=True)
    
    if returns_sorted:
        analysis["momentum_indicators"]["top_performers"] = returns_sorted[:3]
        analysis["momentum_indicators"]["laggards"] = returns_sorted[-3:]
    
    # Identify risk indicators
    for ticker in analysis["supply_chain"]:
        company = analysis["supply_chain"][ticker]
        
        # High volatility warning
        if company.get("volatility") and company["volatility"] > 50:
            analysis["risk_indicators"].append({
                "ticker": ticker,
                "type": "high_volatility",
                "value": company["volatility"],
                "message": f"{ticker} shows high volatility ({company['volatility']:.1f}%)"
            })
        
        # Correlation divergence
        if ticker in analysis["correlations"]:
            corr = analysis["correlations"][ticker]
            if abs(corr) < 0.3 and ticker != reference_ticker:
                analysis["risk_indicators"].append({
                    "ticker": ticker,
                    "type": "low_correlation",
                    "value": corr,
                    "message": f"{ticker} shows low correlation with NVDA ({corr:.2f})"
                })
    
    return analysis

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Nvidia supply chain stocks')
    parser.add_argument('--period', default='3mo', help='Analysis period (1mo, 3mo, 6mo, 1y)')
    parser.add_argument('--format', default='json', choices=['json', 'summary'], help='Output format')
    parser.add_argument('--ticker', help='Specific ticker to analyze')
    
    args = parser.parse_args()
    
    if args.ticker:
        # Analyze specific ticker
        data = fetch_stock_data([args.ticker], period=args.period)
        print(json.dumps(data, indent=2, default=str))
    else:
        # Full supply chain analysis
        analysis = analyze_supply_chain_impact()
        
        if args.format == 'json':
            print(json.dumps(analysis, indent=2, default=str))
        else:
            # Summary format
            print("\n=== NVIDIA SUPPLY CHAIN ANALYSIS ===")
            print(f"Timestamp: {analysis['timestamp']}")
            print("\n--- Top Performers (3M) ---")
            for ticker, return_pct in analysis["momentum_indicators"].get("top_performers", []):
                name = analysis["supply_chain"][ticker]["name"]
                print(f"{ticker}: {name} - {return_pct:.1f}%")
            
            print("\n--- Laggards (3M) ---")
            for ticker, return_pct in analysis["momentum_indicators"].get("laggards", []):
                name = analysis["supply_chain"][ticker]["name"]
                print(f"{ticker}: {name} - {return_pct:.1f}%")
            
            print("\n--- Risk Indicators ---")
            for risk in analysis["risk_indicators"]:
                print(f"⚠️  {risk['message']}")
            
            print("\n--- Key Correlations with NVDA ---")
            corr_sorted = sorted(analysis["correlations"].items(), key=lambda x: abs(x[1]), reverse=True)
            for ticker, corr in corr_sorted[:5]:
                if ticker != "NVDA":
                    name = analysis["supply_chain"][ticker]["name"]
                    print(f"{ticker} ({name}): {corr:.2f}")

if __name__ == "__main__":
    main()
