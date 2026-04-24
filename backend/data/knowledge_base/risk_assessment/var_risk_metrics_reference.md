# Value at Risk (VaR) and Risk Metrics Reference

> Sources: Investopedia (Value at Risk), BIS/BCBS (Minimum Capital Requirements for Market Risk, d457)

## What Is Value at Risk (VaR)?

Value at Risk (VaR) is a quantitative measure used to estimate potential portfolio losses based on probability and market volatility. VaR calculations help risk managers understand the probabilities and extents of potential losses in portfolios, specific positions, or an entire firm. This insight allows institutions to assess their risk exposure and determine the adequacy of their capital reserves.

A 95% one-month VaR of $5,000 means there is a 95% chance the portfolio will not lose more than $5,000 over the next month. Key components: confidence level (typically 95% or 99%), time horizon, and loss amount.

## Three VaR Calculation Methods

### 1. Historical Simulation Method

Looks at prior returns history and orders them from worst losses to greatest gains. Formula: VaR = vm(vi / v(i-1)) where m is the number of days of historical data and vi is the number of variables on day i. Calculates percent change of each risk factor for the past 252 trading days.

### 2. Variance-Covariance (Parametric) Method

Assumes gains and losses are normally distributed. Frames potential losses as standard deviation events from the mean. Works best where distributions are known and reliably estimated. Less reliable if sample size is very small.

### 3. Monte Carlo Simulation

Uses computational models to simulate projected returns over hundreds or thousands of iterations. Most computationally intensive method. Assumes the probability distribution for risk factors is known.

## Benefits of VaR

- Single number expressed as percentage or price units, easily interpreted
- Comparable across different asset types — shares, bonds, derivatives, currencies
- Widely available in financial software tools

## Limitations and Criticisms

- No standard protocol for statistics used to determine risk
- Statistics from low-volatility periods may underestimate future risk events
- Normal distribution assumptions downplay rare extreme events (black swan events)
- Represents the lowest amount of risk in a range of outcomes
- The 2008 financial crisis exposed VaR's underestimation of subprime mortgage portfolio risks
- VaR does not report the maximum potential loss, offering a false sense of security

## Related Risk Metrics

**Marginal VaR**: Additional risk that a new position will add to a portfolio.
**Incremental VaR**: Precise change in risk when a position is added or removed.
**Standard Deviation**: Measures return volatility over time (smaller = lower risk).

## Basel III Market Risk Framework (BIS/BCBS d457)

### Minimum Capital Requirements for Market Risk

Published January 2019 by the Basel Committee. Core features:
- Clearly defined boundary between trading book and banking book
- Internal Models Approach (IMA) using Expected Shortfall models with separate requirements for non-modellable risk factors
- Standardised Approach (SA) that is risk-sensitive and serves as credible fallback to IMA

### Expected Shortfall (ES)

Basel III replaced VaR with Expected Shortfall as the primary risk measure. ES measures the average loss in the distribution tail beyond the VaR threshold, providing more comprehensive tail risk assessment.

### Key Revisions

- Simplified standardised approach for banks with small or non-complex trading portfolios
- Refined treatments of foreign exchange risk and index instruments
- Revised risk weights for general interest rate risk, FX, and credit spread risk
- Revised assessment process for internal models at individual trading desk level

## Stress Testing

### Types

- **Historical Stress Tests**: Apply past crisis conditions (2008 crisis, COVID-19) to current portfolio
- **Hypothetical Stress Tests**: Apply plausible scenarios that haven't occurred
- **Reverse Stress Tests**: Start with adverse outcome and work backward
- **Sensitivity Analysis**: Measure portfolio value changes with respect to individual risk factor changes
