# Fraud Patterns and Transaction Monitoring Reference

> Sources: FinCEN.gov (Advisories FIN-2024-Alert004, FIN-2023-Alert003, FIN-2023-Alert005, FIN-2011-A016, FIN-2019-A005, FIN-2021-A004, FIN-2022-A002), Investopedia (SAR Patterns and Triggers)

## Transaction Monitoring Fundamentals

### Purpose

Transaction monitoring systems analyze customer transactions in real time or near-real time to identify activity that may indicate money laundering, terrorist financing, fraud, or other financial crimes. These systems are a core component of BSA/AML compliance programs.

### Monitoring Approaches

1. **Rule-Based Detection**: Predefined thresholds and patterns (e.g., transactions > $10,000, velocity rules, geographic filters)
2. **Statistical/Anomaly Detection**: Identifying deviations from expected customer behavior based on historical patterns3. **Network Analysis**: Mapping relationships between accounts, entities, and transactions to identify suspicious networks
4. **Machine Learning**: Pattern recognition using supervised (labeled fraud data) and unsupervised (clustering, anomaly detection) models

## Key Monitoring Rules and Thresholds

### Cash Transaction Monitoring

| Rule | Threshold | Action |
|------|-----------|--------|
| CTR Trigger | Cash > $10,000 per day | Automatic CTR filing |
| Structuring Detection | Multiple cash transactions just below $10,000 | SAR investigation |
| Large Cash Pattern | Unusual cash activity relative to customer profile | Alert generation |

### Wire Transfer Monitoring

| Rule | Threshold | Action |
|------|-----------|--------|
| International Wire | Cross-border transfers to high-risk jurisdictions | Enhanced review |
| Rapid Fund Movement | Funds in-and-out within 24 hours | Alert generation |
| Payee Mismatch | Wire beneficiary doesn't match documented relationships | Review |
| Round-Dollar Wires | Recurring exact-amount international transfers | Pattern analysis |

### Account Activity Monitoring

| Rule | Threshold | Action |
|------|-----------|--------|
| Dormant Account Activation | Activity after 12+ months of inactivity | Alert |
| Profile Deviation | Transaction 3x+ above historical average | Alert |
| New Account Velocity | High-value transactions within first 30 days | Alert |
| ACH/Check Anomaly | Sudden increase in check deposits or ACH credits | Review |

## FinCEN Fraud Pattern Advisories

### Deepfake Fraud Indicators (FIN-2024-Alert004)

Key red flags for deepfake-enabled fraud targeting financial institutions:
- Photo or video inconsistencies during identity verification (lighting, resolution, lip sync)
- Customer's appearance on video call doesn't match previously submitted documents
- Synthetic or computer-generated voice detected in phone verification
- Multiple accounts opened using photos with subtle but detectable AI artifacts
- Remote onboarding attempts with unusually perfect document scans

### Check Fraud / Mail Theft Indicators (FIN-2023-Alert003)

Red flags per FinCEN's nationwide surge advisory:
- Mobile deposits of checks appearing to be altered (different ink, whiteout, inconsistent handwriting)
- Checks deposited that were reported stolen from U.S. mail
- Multiple checks deposited from different payers but with similar alterations
- New accounts opened with subsequent high-volume check deposits
- Checks made payable to names that don't match the account holder

### Pig Butchering Indicators (FIN-2023-Alert005)

Red flags for virtual currency investment scams:
- Customer reports meeting an "investment advisor" through social media or dating app
- Progressive increases in wire transfers or ACH payments to cryptocurrency exchanges
- Customer mentions an investment platform that is unregistered with the SEC
- Customer frustrated about inability to withdraw funds from a crypto platform
- Transfers preceded by extended period of small, escalating amounts

### Account Takeover Indicators (FIN-2011-A016)

Behavioral and technical flags:
- Contact information changed (address, phone, email) shortly before large transactions
- Login from new device/IP address followed immediately by fund transfers
- SIM swap activity preceding account access
- Multiple failed MFA attempts followed by successful bypass
- Password reset initiated from unrecognized email address

### BEC Fraud Indicators (FIN-2019-A005)

Business email compromise patterns:
- Last-minute changes to wire transfer instructions, especially beneficiary account
- Email requests that bypass normal approval processes or urgently request payment
- Spoofed email addresses that closely mimic legitimate domains (e.g., company-name.com vs. companynarne.com)
- Requests to wire funds to new international accounts
- CEO/CFO impersonation requesting urgent confidential transfers

### Ransomware Indicators (FIN-2021-A004)

Financial activity flags:
- Customers purchasing large quantities of CVC (convertible virtual currency) unexpectedly
- Wire transfers to cryptocurrency exchanges immediately following a reported cyber incident
- Payments to CVC wallets previously identified in ransomware campaigns
- Small "test" payments to CVC addresses before larger transfers
- Insurance claim filing followed by CVC purchases matching ransom amounts

### Elder Financial Exploitation Indicators (FIN-2022-A002)

- Sudden large or unexplained withdrawals from accounts
- New persons of authority (POA, authorized signer, beneficiary) on elderly customer's account
- Customer appears confused, fearful, or under the control of another person during transactions
- Unusual cashier's check, wire, or ATM activity inconsistent with the customer's profile
- Account transactions that don't align with the customer's stated cognitive or physical capabilities

## Machine Learning in Transaction Monitoring

### Supervised Models

- **Transaction Classification**: Train on labeled data (confirmed fraud vs. legitimate) to predict fraud probability
- **Features**: Transaction amount, velocity, time of day, merchant category, geographic distance, customer age, account age, historical pattern deviation
- **Metrics**: Precision (minimize false positives), Recall (minimize missed fraud), F1-score, AUC-ROC

### Unsupervised Models

- **Anomaly Detection**: Isolation Forest, Autoencoders to detect statistical outliers
- **Clustering**: Group similar transaction patterns, identify outlier clusters
- **Network Analysis**: Graph-based detection of suspicious fund flow patterns

### Model Governance

- Regular model validation and back-testing against confirmed outcomes
- Explainability requirements (SHAP values, feature importance)
- Human-in-the-loop review for all model-generated alerts
- Annual model risk assessment per SR 11-7 (OCC/Fed Model Risk Management Guidance)
