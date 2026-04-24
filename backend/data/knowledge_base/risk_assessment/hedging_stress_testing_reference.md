# Hedging and Stress Testing Reference

> Sources: IRS.gov (Publication 550 — Hedging, Straddles, Short Sales), BIS/BCBS (Basel III Market Risk Framework)

## Hedging Transactions (IRS Publication 550)

A hedging transaction is any transaction entered into in the normal course of business primarily to manage the risk of price changes or currency fluctuations with respect to ordinary property or ordinary obligations. Gains and losses from qualifying hedging transactions are treated as ordinary gains and losses, not capital gains/losses.

### Requirements for Hedging Treatment

To qualify as a hedging transaction under IRS rules:
- Must be entered into in the normal course of your trade or business
- Must primarily manage risk of price changes or currency fluctuations
- Must be clearly identified as a hedging transaction before the close of the day on which it was acquired, originated, or entered into

### Straddle Rules (IRS Publication 550)

A straddle is created when you hold offsetting positions — positions in personal property if there is a substantial diminution of risk of loss from holding one position by reason of holding one or more other positions.

Key straddle provisions:
- **Loss deferral rule**: Losses from disposing of straddle positions are deferred to the extent of unrealized gain in the offsetting position
- **Wash sale rule extension**: Applies to straddle positions
- **Short sale rule extension**: Rules for holding period of short sales apply to straddle positions
- **Mixed straddle elections**: Available when a straddle includes both Section 1256 contracts and non-Section 1256 positions

## Short Sales (IRS Publication 550)

A short sale occurs when you sell borrowed property (usually stock) and later close the sale by returning property to the lender. Key rules:
- If you held substantially identical property for one year or less on the date of the short sale, any gain on closing is short-term
- If you held substantially identical property for more than one year, gain may be long-term but loss is always long-term

## Section 1256 Contracts — Mark-to-Market

Section 1256 contracts include regulated futures contracts, foreign currency contracts, nonequity options, dealer equity options, and dealer securities futures contracts.

### 60/40 Rule

Gains and losses on Section 1256 contracts are treated as:
- **60% long-term** capital gains or losses
- **40% short-term** capital gains or losses
- Regardless of actual holding period
- Marked to market at year-end (treated as sold at fair market value on the last business day of the tax year)

## Basel III Stress Testing Framework

### Regulatory Requirements

The Basel III framework requires banks to conduct rigorous forward-looking stress testing that identifies possible events or changes in market conditions that could adversely impact the bank.

### Types of Stress Tests

1. **Sensitivity Analysis**: Evaluates portfolio response to single risk factor changes (e.g., interest rate shift of +/- 200 basis points, equity market decline of 25%)

2. **Scenario Analysis**: Evaluates portfolio response to simultaneous changes in multiple risk factors under a coherent scenario (e.g., recession scenario combining equity decline, credit spread widening, interest rate changes)

3. **Reverse Stress Testing**: Identifies scenarios that would cause a bank to breach minimum capital requirements or become non-viable. Required to consider scenarios beyond normal business expectations.

### Expected Shortfall (ES)

The Basel III Internal Models Approach replaces VaR with Expected Shortfall at a 97.5% confidence level:
- ES measures the average loss in the tail beyond the VaR threshold
- Captures tail risk more effectively than VaR
- Calculated over a base horizon of 10 days, with liquidity-adjusted horizons (20, 40, 60, or 120 days) for less liquid risk factors

### Non-Modellable Risk Factors (NMRF)

Risk factors that cannot be modelled due to insufficient data require separate capital charges based on stress scenarios. Banks must demonstrate that they have sufficient observable data (at least 24 observations over the preceding 12 months) for a risk factor to be considered modellable.

## Practical Stress Testing Scenarios

### Historical Scenarios

| Scenario | Key Parameters |
|----------|---------------|
| 2008 Global Financial Crisis | Equity -50%, credit spreads +500bp, interbank rates spike, liquidity freeze |
| 2020 COVID-19 Crash | Equity -35% in weeks, VIX > 80, oil prices collapse, yields plummet |
| 2010 European Sovereign Debt | PIIGS spreads widen, EUR depreciation, bank CDS spike |
| 2015 China Devaluation | CNY -3%, EM selloff, commodity decline |

### Hypothetical Scenarios

- Sudden interest rate shock (+300bp)
- Geopolitical crisis (major sanctions, trade war escalation)
- Cyber attack on financial infrastructure
- Climate transition shock (carbon tax, stranded assets)
- Stagflation (rising inflation with economic contraction)

## Risk Factor Categories

1. **Interest Rate Risk**: Changes in yield curves, basis risk between benchmarks
2. **Equity Risk**: Stock price movements, volatility changes
3. **Credit Spread Risk**: Changes in credit spreads for corporate and sovereign bonds
4. **Foreign Exchange Risk**: Currency movements
5. **Commodity Risk**: Price changes in energy, metals, agriculture
