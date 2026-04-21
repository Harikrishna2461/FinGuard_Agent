# Customer Segmentation and KYC Reference

> Sources: Investopedia (Know Your Client Requirements, by James Chen, updated Aug 2025), FinCEN.gov (BSA Requirements, CDD Rule), FINRA.org (Rules 2090, 2111)

## Know Your Customer (KYC) Framework

### Three Pillars of KYC (per FinCEN/FINRA)

#### 1. Customer Identification Program (CIP)

Financial firms must obtain and verify four key pieces of client information:
- **Name** — Full legal name
- **Date of Birth** — For individuals
- **Address** — Residential or business address
- **Identification Number** — SSN (for U.S. persons), passport number, or alien identification number

Acceptable identification documents include: government-issued photo ID (driver's license, passport), birth certificate, social security card. Some institutions require two forms of ID.

#### 2. Customer Due Diligence (CDD)

CDD involves gathering a customer's credentials to confirm their identity and assess their risk for suspicious activities. Per FinCEN requirements, financial institutions must:
- Understand the nature and purpose of customer relationships
- Develop customer risk profiles
- Conduct ongoing monitoring to report suspicious transactions
- Maintain and update customer information on a risk basis

#### 3. Enhanced Due Diligence (EDD)

EDD applies to customers at higher risk for infiltration, terrorism financing, or money laundering. Requires additional information collection including:
- Source of funds and source of wealth
- Purpose of the account and expected activity patterns
- Beneficial ownership and control structure
- Nature of the customer's business
- Enhanced transaction monitoring

### Beneficial Ownership Requirements

Under FinCEN's CDD Rule, covered financial institutions must identify and verify the identity of the beneficial owners of legal entity customers. A beneficial owner is:
- Each individual who, directly or indirectly, owns 25% or more of the equity interests of the legal entity customer
- A single individual with significant responsibility to control, manage, or direct the legal entity (e.g., CEO, CFO, COO, managing member, general partner)

## FINRA KYC Rules

### Rule 2090 — Know Your Customer

Every broker-dealer must use reasonable diligence regarding the opening and maintenance of every account, to know (and retain) the essential facts concerning every customer and concerning the authority of each person acting on behalf of such customer. Essential facts include:
- Identity of the customer
- Persons authorized to act on the customer's behalf
- The customer's financial profile

### Rule 2111 — Suitability

A broker-dealer must have a reasonable basis to believe that a recommended transaction or investment strategy is suitable for the customer, based on:
- Customer's age
- Other investments
- Financial situation and needs
- Tax status
- Investment objectives
- Investment experience
- Investment time horizon
- Liquidity needs
- Risk tolerance

## Customer Risk Segmentation

### Risk Categories

| Risk Level | Characteristics | Due Diligence | Monitoring |
|-----------|----------------|---------------|-----------|
| Low | Domestic individuals, established history, standard products | Standard CDD | Routine |
| Medium | Business accounts, moderate transaction volumes, some geographic risk | Enhanced CDD | Periodic review |
| High | PEPs, non-resident aliens, high-value accounts, complex structures | Full EDD | Continuous monitoring |
| Prohibited | SDN-listed, sanctioned countries, known bad actors | Reject/block | N/A |

### Politically Exposed Persons (PEPs)

Individuals with prominent public functions who pose a higher risk for money laundering and corruption:
- Current or former heads of state or government
- Senior government officials, judicial or military officials
- Senior executives of state-owned corporations
- Important political party officials
- Family members and close associates of the above

PEPs require EDD, including:
- Senior management approval for establishing relationships
- Establishing the source of wealth and source of funds
- Conducting enhanced ongoing monitoring

### Customer Lifecycle Management

1. **Onboarding**: CIP verification, CDD/EDD assessment, risk scoring
2. **Ongoing Monitoring**: Transaction monitoring, periodic KYC refresh, sanctions screening
3. **Trigger Events**: Material changes in customer profile, unusual activity, adverse media
4. **Periodic Review**: Risk-based schedule (high-risk annually, medium every 2-3 years, low every 3-5 years)
5. **Account Closure**: SAR filing if warranted, proper documentation of closure rationale

## Customer Profile Data Elements

### Individual Customers
- Full legal name, date of birth, SSN/TIN
- Residential address, phone, email
- Employment status, employer, occupation
- Annual income, net worth, liquid net worth
- Investment experience and objectives
- Source of funds (employment, inheritance, business income, etc.)
- Expected account activity (types, volumes, geographic exposure)

### Entity Customers
- Legal entity name, jurisdiction of formation
- Business type and nature of business
- Tax identification number (EIN)
- Principal place of business
- Beneficial ownership information (25%+ owners, controlling person)
- Expected account activity and purpose
- Financial statements (for higher-risk entities)
