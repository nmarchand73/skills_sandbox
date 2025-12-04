# Market Analysis Strategies

## Fundamental Analysis Framework

### Supply Chain Health Score
Calculate composite score (0-100) based on:

1. **Capacity Utilization** (25%)
   - TSM utilization >90% = bullish for pricing
   - <85% = demand concerns
   - Memory utilization as secondary indicator

2. **Lead Time Trends** (25%)
   - Extending = demand > supply (bullish)
   - Shortening = demand softening
   - Track via supplier commentary

3. **Inventory Metrics** (25%)
   - Days of inventory (DOI) trends
   - Channel inventory levels
   - Customer inventory digestion

4. **Pricing Power** (25%)
   - ASP trends for GPUs
   - Foundry wafer pricing
   - Memory (especially HBM) pricing

### Relative Valuation Framework

#### P/E Multiple Analysis
- Compare forward P/E across supply chain tiers
- Historical range analysis (5-year context)
- Relative to semiconductor index (SOXX)

#### EV/Sales Relationships
```
Premium Tier (>10x): NVDA, ASML
High Tier (5-10x): TSM, KLAC, CDNS
Mid Tier (2-5x): AMAT, LRCX, MU
Value Tier (<2x): AMKR, ASX
```

#### PEG Ratio Screening
- Identify mispriced growth in supply chain
- Compare growth rates to multiple paid
- Sweet spot: PEG < 1.5 with >20% growth

## Technical Analysis Patterns

### Supply Chain Divergence Signals

#### Bullish Divergence Pattern
When equipment stocks (ASML, AMAT) break out BEFORE NVDA:
- Indicates capacity expansion
- 3-6 month leading signal
- Confirm with order book data

#### Bearish Divergence Pattern
When memory stocks (MU, SK) break down BEFORE NVDA:
- Indicates demand weakness
- 1-3 month leading signal
- Confirm with pricing data

### Correlation Breakdown Analysis

Monitor 20-day rolling correlation:
- Normal range: 0.5-0.8 for tier-1 suppliers
- Breakdown (<0.3) = Potential opportunity
- Spike (>0.9) = Risk-off environment

### Volume Profile Analysis

Track unusual volume in supply chain before earnings:
- >2x average daily volume = Information leakage
- Options flow in suppliers = Directional bet
- Dark pool activity in equipment stocks

## Sentiment Analysis Framework

### Insider Transaction Patterns

#### Bullish Signals
- Cluster buying in equipment stocks
- 10b5-1 plan suspensions for sales
- Board-level purchases

#### Bearish Signals  
- CFO/CEO sales outside of plans
- Multiple insiders selling simultaneously
- Early vesting exercises

### Analyst Revision Momentum

Track 30-day revision trends:
- >20% upward revisions = Bullish momentum
- Equipment revisions lead chip revisions
- Memory revisions are contrarian indicators

### Social Sentiment Metrics

Reddit/Twitter mention analysis:
- WSB interest in SMCI/AMD = Retail extremes
- Semiconductor engineer forums = Ground truth
- LinkedIn hiring trends = Capacity planning

## Options Market Intelligence

### Put/Call Ratio Analysis
- Supply chain aggregate P/C ratio
- Unusual options activity in Tier-2/3 names
- Term structure analysis for event timing

### Implied Volatility Patterns
- IV rank across supply chain
- Event volatility (earnings) patterns
- Volatility surface skew analysis

### Options Flow Strategies

#### Smart Money Indicators
- Large block trades in equipment names
- Spread trades indicating direction
- Calendar spreads for event positioning

## Quantitative Strategies

### Pair Trading Opportunities

#### Classic Pairs
1. **NVDA/AMD**: Market share shifts
2. **TSM/INTC**: Foundry competition  
3. **AMAT/LRCX**: Equipment cycle
4. **MU/SK**: Memory pricing

#### Pair Entry Signals
- 2+ standard deviation spread
- Mean reversion over 20-60 days
- Stop loss at 3 standard deviations

### Factor Model Approach

Key factors for supply chain:
1. **Momentum**: 3-month price momentum
2. **Quality**: ROE, ROIC trends
3. **Growth**: Revenue growth acceleration
4. **Value**: EV/Sales relative to history
5. **Volatility**: Inverse volatility weight

### Mean Reversion Strategies

#### RSI Extremes
- Buy when RSI <30 on Tier-2/3 names
- Sell when RSI >70 on extended moves
- Best in equipment and memory stocks

#### Bollinger Band Reversions
- 2.5 SD bands for entry signals
- Confirm with volume spike
- Target mean reversion over 5-10 days

## Risk Management Framework

### Position Sizing by Tier

```
Tier 1 (NVDA, TSM): Up to 10% per position
Tier 2 (ASML, MU): Up to 5% per position  
Tier 3 (AMAT, LRCX): Up to 3% per position
Tier 4-5: Up to 2% per position
```

### Correlation-Adjusted Portfolios
- Maximum 40% in highly correlated names
- Diversify across supply chain tiers
- Include hedges (puts, inverse ETFs)

### Stop Loss Framework

#### Fundamental Stops
- Break of key supply agreements
- Major customer loss
- Technology disruption

#### Technical Stops
- Close below 50-day MA for trends
- Break of major support levels
- Volatility-adjusted stops (2x ATR)

## Macro Overlay Considerations

### Interest Rate Sensitivity
- Equipment stocks most sensitive
- Memory follows with lag
- NVDA relatively insulated

### Currency Impacts
- USD/TWD for TSM
- USD/EUR for ASML
- USD/KRW for memory

### China Policy Risk
- Equipment most exposed (20-30% revenue)
- Memory significant (15-25%)
- Monitor export control updates

## Execution Best Practices

### Entry Tactics
- Scale in over 3-5 days
- Use VWAP for large positions
- Avoid first/last 30 minutes

### Earnings Season Positioning
- Reduce before equipment reports
- Add on supply chain confirmation
- Hedge before NVDA reports

### Rebalancing Schedule
- Quarterly tier reweighting
- Monthly correlation check
- Weekly sentiment review

## Key Data Sources

### Primary Data
- Company investor relations
- SEMI industry reports
- TrendForce for memory/foundry

### Alternative Data
- Satellite imagery of fabs
- Shipping data for equipment
- Job postings for capacity

### Real-time Indicators
- Asian supplier updates (overnight)
- Supply chain news alerts
- Option flow services
