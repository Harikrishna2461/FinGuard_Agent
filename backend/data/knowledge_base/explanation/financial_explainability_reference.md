# Financial Explainability Reference

> Sources: Investopedia (Technical Analysis, Modern Portfolio Theory, Value at Risk, KYC, SAR), SEC.gov (Investor Publications), FINRA.org (Investor Education)

## Explainable AI (XAI) in Financial Services

### Why Explainability Matters

Financial regulators increasingly require that automated decisions affecting customers can be explained. Key requirements:
- **Fair lending laws** require explanations for credit denials
- **Reg BI** requires broker-dealers to disclose material facts about recommendations
- **FINRA Rule 2111** suitability requires documented rationale for recommendations
- Customers have the right to understand decisions affecting their accounts

### Model Interpretability Approaches

- **Feature Importance**: Which input variables most influenced the model's output
- **SHAP Values**: Shapley Additive Explanations quantify each feature's contribution to a prediction
- **LIME**: Local Interpretable Model-Agnostic Explanations approximate complex models locally with interpretable ones
- **Partial Dependence Plots**: Show marginal effect of one or two features on predictions
- **Counterfactual Explanations**: "What would need to change for a different outcome?"

## Financial Concepts Glossary

### Risk Metrics

| Term | Definition |
|------|-----------|
| Value at Risk (VaR) | Maximum expected loss at a given confidence level over a specified time period. Example: 95% 1-day VaR of $10,000 means there's a 95% chance daily losses won't exceed $10,000. |
| Expected Shortfall (ES) | Average loss in the tail beyond the VaR threshold. More conservative than VaR because it accounts for the severity of tail losses. |
| Standard Deviation | Measures how much returns vary around the mean. Higher value indicates greater volatility and risk. |
| Beta | Systematic risk relative to the market benchmark. Beta > 1 means more volatile than market, < 1 means less volatile. |
| Sharpe Ratio | Risk-adjusted return: (Portfolio Return - Risk-Free Rate) / Portfolio Standard Deviation. Higher is better. |
| Alpha | Excess return relative to a risk-adjusted benchmark. Positive alpha means outperformance. |

### Portfolio Concepts

| Term | Definition |
|------|-----------|
| Diversification | Spreading investments across asset classes to reduce risk. Based on the principle that assets with low correlation reduce portfolio volatility. |
| Efficient Frontier | Curve of portfolios offering the highest expected return for each level of risk (per Modern Portfolio Theory). |
| Asset Allocation | Distribution of investments across asset classes (stocks, bonds, real estate, cash). |
| Rebalancing | Adjusting portfolio weights back to target allocations to maintain desired risk level. |
| Correlation | Statistical measure of how two securities move in relation to each other. Range: -1 (perfect inverse) to +1 (perfect direct). |

### Trading and Technical Analysis

| Term | Definition |
|------|-----------|
| RSI (Relative Strength Index) | Momentum oscillator (0-100). Above 70 = overbought, below 30 = oversold. Developed by J. Welles Wilder Jr. (1978). |
| MACD | Moving Average Convergence Divergence. Trend-following indicator: 12-period EMA minus 26-period EMA with 9-day signal line. |
| Support | Price level where buying interest prevents further decline. |
| Resistance | Price level where selling pressure prevents further advance. |
| Moving Average | Average of closing prices over n periods. SMA (equal weight) or EMA (recent prices weighted more). |
| Bollinger Bands | Volatility indicator: 20-period SMA ± 2 standard deviations. Bands widen in high volatility. |

### Compliance and Regulatory

| Term | Definition |
|------|-----------|
| SAR | Suspicious Activity Report — confidential filing to FinCEN when a financial institution detects potentially illegal activity. Filed within 30 days of detection. |
| CTR | Currency Transaction Report — required for cash transactions exceeding $10,000 in a single business day. |
| BSA | Bank Secrecy Act — requires financial institutions to maintain records and file reports that help detect and prevent money laundering. |
| KYC | Know Your Customer — verification of client identity (CIP), financial profile (CDD), and enhanced review for high-risk clients (EDD). |
| AML | Anti-Money Laundering — measures and processes used to detect, prevent, and report money laundering activity. |
| OFAC | Office of Foreign Assets Control — administers U.S. economic sanctions programs against targeted countries, individuals, and entities. |
| SDN List | Specially Designated Nationals list — OFAC's list of blocked persons and entities. |
| PEP | Politically Exposed Person — individual with prominent public function requiring enhanced due diligence. |

### Fraud Types

| Term | Definition |
|------|-----------|
| Structuring | Breaking transactions into smaller amounts to avoid CTR reporting thresholds ($10,000). Federal crime. |
| Money Laundering | Making illegally obtained money appear legitimate through placement, layering, and integration. |
| Phishing | Fraudulent communications designed to steal credentials or sensitive information. |
| Account Takeover | Unauthorized access to and control of a customer's financial account. |
| Business Email Compromise | Fraud where attackers impersonate trusted parties to redirect wire transfers or steal data. |
| Pig Butchering | Long-con cryptocurrency investment scam where victims are groomed online, then directed to fraudulent platforms. |
| Wash Sale | Selling securities at a loss and buying substantially identical securities within 30 days — loss is disallowed for tax purposes. |

## Explaining Risk Scores to Customers

### Score Interpretation Framework

When communicating risk assessments:

1. **State the outcome clearly**: "Your transaction was flagged for additional review."
2. **Cite contributing factors**: "The following factors contributed to this assessment: [list top factors]"
3. **Provide context**: "Transactions with these characteristics are reviewed as part of our standard compliance program."
4. **Note limitations**: Risk scores are one input into decision-making, not deterministic outcomes.
5. **Offer next steps**: "If you believe this is in error, you may [contact/provide documentation]."

### Important Caveats

- **SAR existence cannot be disclosed** to customers under any circumstances
- Risk scores should be communicated in general terms without revealing specific model thresholds
- Compliance decisions must be documented with rationale regardless of automated scoring
- Human review is required before adverse actions based on automated risk scores
