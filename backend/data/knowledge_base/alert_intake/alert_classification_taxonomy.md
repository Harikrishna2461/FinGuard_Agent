# Alert Classification and Fraud Typologies Reference

> Sources: FinCEN.gov (SAR Advisory Key Terms, Advisories/Alerts), Investopedia (Suspicious Activity Reports)

## Alert Classification Taxonomy

### Alert Severity Levels

| Level | Description | Response SLA |
|-------|-------------|--------------|
| Critical | Confirmed fraud, active account compromise, sanctions match | Immediate (< 1 hour) |
| High | Strong indicators of suspicious activity, large-value anomalous transactions | < 4 hours |
| Medium | Pattern deviations requiring investigation, moderate-risk triggers | < 24 hours |
| Low | Minor anomalies, informational flags for monitoring | < 72 hours |

### Alert Categories (Based on FinCEN SAR Advisory Key Terms)

1. **Money Laundering / Structuring**: Transactions designed to evade BSA reporting requirements
2. **Terrorist Financing**: Funds flowing to designated terrorist organizations
3. **Fraud**: Identity theft, account takeover, check fraud, wire fraud, deepfake fraud
4. **Sanctions Violations**: Transactions involving SDN-listed persons, blocked countries
5. **Insider Abuse/Trading**: Suspicious activity by employees or insiders
6. **Cyber-Enabled Crime**: Computer hacking, business email compromise, ransomware
7. **Tax Evasion/Fraud**: Structuring to avoid tax obligations, ERC fraud
8. **Human Trafficking/Smuggling**: Financial patterns associated with trafficking
9. **Elder Financial Exploitation**: Suspicious activity targeting elderly customers
10. **Virtual Currency**: Pig butchering scams, CVC kiosk abuse, mixer services

## FinCEN Fraud Typology Alerts (Active)

### Deepfake Fraud (FIN-2024-Alert004, November 2024)

FinCEN Alert on Fraud Schemes Involving Deepfake Media Targeting Financial Institutions. SAR Key Term: FIN-2024-DEEPFAKEFRAUD. Financial institutions should be vigilant for fraud attempts using AI-generated synthetic media to bypass identity verification.

### Check Fraud / Mail Theft (FIN-2023-Alert003, February 2023)

FinCEN Alert on Nationwide Surge in Mail Theft-Related Check Fraud Schemes Targeting the U.S. Mail. SAR Key Term: FIN-2023-MAILTHEFT. Covers schemes where checks are stolen from U.S. mail, altered (washed), and cashed or deposited.

### Pig Butchering (FIN-2023-Alert005, September 2023)

FinCEN Alert on Prevalent Virtual Currency Investment Scam Commonly Known as "Pig Butchering." SAR Key Term: FIN-2023-PIGBUTCHERING. Long-con investment fraud where victims are groomed online before being directed to invest in fraudulent cryptocurrency platforms.

### Account Takeover (FIN-2011-A016, December 2011)

Advisory on Account Takeover Activity. SAR Key Term: ACCOUNT TAKEOVER FRAUD. Covers unauthorized access to customer accounts through credential theft, phishing, and social engineering.

### Business Email Compromise (FIN-2019-A005, July 2019)

Advisories on Email Compromise Fraud Schemes. SAR Key Terms: BEC FRAUD, EAC FRAUD, BEC DATA THEFT. Sophisticated scams where attackers impersonate executives, vendors, or attorneys to redirect wire transfers.

### Ransomware (FIN-2021-A004, November 2021)

Advisory on Ransomware Activity. SAR Key Term: CYBER FIN-2021-A004. Covers ransomware payments and related financial activity indicators.

### Elder Financial Exploitation (FIN-2022-A002, June 2022)

Advisory on Elder Financial Exploitation. SAR Key Term: EFE FIN-2022-A002. Patterns include unusual withdrawals, new persons of authority on accounts, sudden changes in financial documents.

## SAR Suspicious Activity Patterns (from FinCEN)

The Financial Crimes Enforcement Network identifies these common suspicious patterns:

1. **No legitimate business purpose**: Transactions with no apparent economic or lawful purpose
2. **Business type mismatch**: Unusual financial nexuses between unrelated business types
3. **Volume anomalies**: Transactions not commensurate with stated business type
4. **Wire transfer patterns**: Unusually large numbers/volumes or repetitive patterns
5. **Complex layering**: Transactions involving multiple accounts, banks, and parties
6. **Bulk cash**: Large cash and monetary instrument transactions
7. **Mixed deposits**: Unusual combinations of deposit types into business accounts
8. **Dormant account activity**: Sudden transaction bursts in previously inactive accounts
9. **Inconsistent account usage**: Activity inconsistent with account opening purpose
10. **Structuring indicators**: Transactions that appear designed to avoid reporting thresholds

## SAR Filing Requirements

- File within **30 calendar days** from initial detection
- Retain for **five years** after filing
- **No disclosure** to customer or involved parties
- Does not require proof of a crime — reports potentially concerning activity
- SARs help law enforcement identify patterns and trends in financial crimes

## Alert Triage Decision Framework

1. **Validate**: Confirm the alert data is accurate and relates to the correct customer/account
2. **Enrich**: Gather additional context (transaction history, KYC profile, related alerts)
3. **Assess**: Determine if activity matches known suspicious patterns or fraud typologies
4. **Decide**: Escalate for SAR filing, close as false positive, or request additional review
5. **Document**: Record rationale for disposition regardless of outcome
