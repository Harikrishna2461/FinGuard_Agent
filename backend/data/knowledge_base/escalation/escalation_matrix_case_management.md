# Escalation Matrix and Case Management Reference

> Sources: FinCEN.gov (SAR Filing Requirements, Advisory Key Terms), Investopedia (SAR Filing Process and Triggers)

## Escalation Framework

### Tier 1 — Automated Alert Triage

Initial system-generated alerts from transaction monitoring and screening systems:
- Sanctions screening matches (OFAC SDN, country lists)
- Transaction threshold violations (CTR triggers > $10,000)
- Rule-based anomaly detection (velocity, amount, pattern)
- Disposition: Auto-close false positives, escalate genuine matches

### Tier 2 — Analyst Investigation

Trained compliance analysts investigate escalated alerts:
- Review full transaction history and customer profile
- Check for related alerts and prior SARs on the same customer
- Apply FinCEN advisory typologies and red flags
- Determine if SAR filing is warranted
- Time to disposition: within 24-48 hours for high-priority alerts

### Tier 3 — Senior Compliance Review

Complex or high-risk cases requiring senior expertise:
- Multi-jurisdictional activity involving sanctions
- Cases involving PEPs or high-profile customers
- Patterns suggesting organized criminal activity
- Cases requiring coordination with law enforcement (e.g., FinCEN 314(a) requests)
- Bank executive or insider involvement

### Tier 4 — Executive / Legal Escalation

Cases requiring executive management or legal counsel involvement:
- Mandatory regulatory reporting (Section 314(a) responses)
- Law enforcement subpoenas and information requests
- Potential account termination or de-risking decisions
- Cases with reputational risk to the institution
- Communication with regulators (OCC, FDIC, Federal Reserve, FINRA)

## SAR Filing Requirements (per FinCEN)

### Filing Timeline

Financial institutions generally have **30 calendar days** from the date of initial detection of facts that may constitute a basis for filing a SAR. If no suspect is identified, the institution may delay filing for an additional 30 days to identify a suspect, but in no case may reporting be delayed more than 60 days after the date of initial detection.

### SAR Content Requirements

A SAR includes:
- **Subject information**: Identities of individuals or entities involved
- **Account information**: Account numbers, types, and institutions involved
- **Transaction details**: Nature, amounts, dates, and methods of suspicious transactions
- **Narrative**: Comprehensive explanation of the suspicious activity, including:
  - Who is conducting the activity
  - What instruments or mechanisms are being used
  - When the activity occurred
  - Where the activity took place
  - Why the activity is suspicious
  - How the activity was conducted

### SAR Narrative Best Practices

Per FinCEN guidance, the narrative should:
- Be clear, concise, and complete
- Provide a chronological description of the suspicious activity
- Include all relevant facts and basis for suspicion
- Reference specific FinCEN advisory key terms where applicable
- Not include any information that could reveal the existence of the SAR to the subject

### SAR Advisory Key Terms (FinCEN)

When filing SARs related to specific FinCEN advisories, include the designated key term in the SAR narrative. Examples:
- FIN-2024-DEEPFAKEFRAUD (Deepfake fraud)
- FIN-2023-MAILTHEFT (Check fraud via mail theft)
- FIN-2023-PIGBUTCHERING (Crypto investment scams)
- ACCOUNT TAKEOVER FRAUD (Account compromises)
- BEC FRAUD / EAC FRAUD (Business email compromise)
- CYBER FIN-2021-A004 (Ransomware)
- EFE FIN-2022-A002 (Elder financial exploitation)

### SAR Retention and Confidentiality

- SARs must be retained for **five years** after filing
- Filing institutions may not notify any person involved in the transaction that a SAR has been filed
- Violation of SAR confidentiality can result in **severe penalties** for both individuals and institutions
- The USA PATRIOT Act provides safe harbor protection for SAR filers acting in good faith

## Case Management Workflow

### Case Lifecycle

1. **Case Creation**: Alert or referral generates a new case with unique identifier
2. **Assignment**: Auto-assigned based on case type, complexity, and analyst availability
3. **Collection**: Gather relevant documentation (transactions, KYC records, prior SARs)
4. **Analysis**: Apply investigative procedures, identify patterns, assess risk
5. **Decision**: Determine disposition (SAR filing, case closure, further monitoring, account action)
6. **Documentation**: Record all findings, rationale, and actions taken
7. **Filing**: Submit SAR if warranted, within 30-day regulatory timeline
8. **Follow-up**: Monitor for continuing activity, file continuing SARs as needed (every 90 days if activity continues)

### Case Priority Matrix

| Transaction Amount | High Suspicion | Medium Suspicion | Low Suspicion |
|-------------------|---------------|-----------------|--------------|
| > $1,000,000 | Critical (4h SLA) | High (8h SLA) | Medium (24h SLA) |
| $100,000 - $1M | High (8h SLA) | Medium (24h SLA) | Low (72h SLA) |
| $25,000 - $100K | Medium (24h SLA) | Low (72h SLA) | Low (72h SLA) |
| < $25,000 | Medium (24h SLA) | Low (72h SLA) | Auto-review |

### FinCEN Information Sharing

#### Section 314(a) — Law Enforcement to Financial Institutions

FinCEN may request financial institutions to search their records for accounts and transactions of persons reasonably suspected of engaging in terrorist activity or money laundering. Response typically required within **14 days**.

#### Section 314(b) — Financial Institution to Financial Institution

Allows financial institutions to share information with each other for the purpose of identifying and reporting activities that may involve terrorist activity or money laundering. Participation is **voluntary** and requires filing a notice with FinCEN.

## Regulatory Reporting Obligations

| Report | Trigger | Timeline | Form |
|--------|---------|----------|------|
| SAR | Suspicious activity ≥ $5,000 | 30 days from detection | FinCEN Form 111 |
| CTR | Cash transaction > $10,000 | 15 days from transaction | FinCEN Form 112 |
| CMIR | Cross-border currency > $10,000 | At time of transport | FinCEN Form 105 |
| FBAR | Foreign accounts > $10,000 aggregate | April 15 (Oct 15 extension) | FinCEN Form 114 |
