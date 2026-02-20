# Municipal Bond Finance Ontology

**Version:** 1.0 | **Created:** 2026-02-18
**Purpose:** Domain knowledge taxonomy for the Muni-Pal Research Agent
**Scope:** Revenue bond focus with waste/environmental (primary) and healthcare (secondary)

---

## DOMAIN 1: INSTRUMENT TAXONOMY

### 1.1 General Obligation (GO) Bonds
- Secured by the **full faith and credit** and taxing power of the issuer
- Backed by ad valorem (property) taxes, sometimes with unlimited tax pledge
- Issued by states, counties, cities, school districts, special districts
- Voter approval typically required (varies by state)
- Generally considered lower risk than revenue bonds due to broad tax base
- **Limited tax GO**: pledge limited to a specific millage rate or tax ceiling
- **Unlimited tax GO**: pledge includes authority to raise taxes as needed to meet debt service
- **Double-barreled**: GO pledge combined with a revenue pledge (e.g., utility GO backed by water rates + property taxes)

### 1.2 Revenue Bonds
Revenue bonds are the **primary focus** of this agent and the Muni-Pal platform.

- Secured by a **specific revenue stream** from the financed project or enterprise
- No recourse to the issuer's general taxing power
- Typically issued through enterprise funds, authorities, or conduit issuers
- Higher yields than GO bonds (reflecting narrower security pledge)
- Covenants: rate covenant (maintain sufficient revenues), additional bonds test, flow of funds requirements

#### 1.2.1 Revenue Bond Sub-Types by Sector

**Waste Management / Environmental Services** (PRIMARY SECTOR):
- **Solid waste system revenue bonds**: Secured by tipping fees, collection charges, recycling revenue
- **Resource recovery revenue bonds**: Waste-to-energy facilities, secured by energy sales + tipping fees
- **Landfill revenue bonds**: Secured by disposal fees, often with closure/post-closure funding requirements
- **Environmental improvement revenue bonds**: Remediation, brownfield redevelopment
- **Private activity bonds (PAB)**: Tax-exempt conduit issuance for private solid waste facilities under IRC 142(a)(6)
- Key revenue sources: tip fees ($/ton), franchise fees, host community fees, energy sales, recyclable commodity sales, landfill gas royalties
- Typical structures: serial + term bonds, optional redemption after 10 years, additional bonds test at 1.25x DSCR

**Healthcare** (SECONDARY SECTOR):
- **Hospital revenue bonds**: Secured by gross revenues of the hospital/health system
  - Typically issued through a state or county health facility authority as conduit
  - Master trust indenture (MTI) structure common for multi-facility systems
  - Revenue pledge: gross revenues (all patient service revenue, grants, investment income)
  - Key metrics: operating margin, DSCR (typically 1.10-1.40x minimum), days cash on hand (150-300+), payor mix
- **501(c)(3) conduit bonds**: Tax-exempt conduit issuance for nonprofit healthcare entities under IRC 145
  - Most common healthcare muni structure
  - Conduit issuer (authority) has no obligation; bonds are solely secured by the borrower's revenues
  - TEFRA hearing required (Tax Equity and Fiscal Responsibility Act)
- **Continuing Care Retirement Community (CCRC) bonds**: Secured by entrance fees + monthly service fees
  - Higher risk sub-sector; entrance fee refund obligations create actuarial exposure
  - Key metrics: entrance fee reserves, actuarial soundness, waitlist depth, occupancy by care level
  - Often rated below investment grade or unrated
  - Start-up CCRCs (new construction) carry highest risk; established CCRCs with waitlists carry lower risk
- **Senior living revenue bonds**: Assisted living, independent living, memory care
  - Revenue pledge: resident fees, ancillary service charges
  - Key metrics: occupancy rate (85%+ target), revenue per occupied unit, acuity mix, staffing ratios
  - Regulatory risk: state licensing, Medicaid waiver programs
- **Behavioral health revenue bonds**: Psychiatric hospitals, substance abuse treatment, crisis centers
  - Revenue pledge: patient service revenues (often heavily Medicaid/Medicare dependent)
  - Key metrics: bed utilization, average length of stay, reimbursement rate stability, parity law compliance
  - Regulatory risk: state certificate of need (CON), federal parity requirements, Medicaid expansion status

### 1.3 Capital Appreciation Bonds (CABs)
- Zero-coupon bonds that accrete value over time rather than paying current interest
- Investor receives a single payment at maturity (accreted value = original principal + compounded interest)
- **Why they exist**: Match deferred revenue profiles (e.g., projects with construction/ramp-up periods before cash flow)
- **UCS archetype**: 5-7 year accretion at 6.0-6.5%, converting to current-pay
- **Regulatory scrutiny**: Some states have imposed limits on CAB issuance (California AB 182) due to concerns about total interest cost
- **Conversion feature**: Some CABs convert to current interest bonds (CIBs) at a specified date or revenue trigger

### 1.4 Tax Status Categories

**Tax-Exempt (IRC 103)**:
- **Governmental bonds**: Issued by and for government entities; no private use limitations
- **501(c)(3) bonds** (IRC 145): Conduit issuance for nonprofit entities; 5% private business use test
- **Private Activity Bonds** (IRC 141-142): Tax-exempt despite private use; must fit enumerated categories:
  - Exempt facility bonds: airports, docks, waste disposal (142(a)(6)), water/sewage, solid waste, mass transit
  - Qualified residential rental projects (142(d)): Multi-family housing (4% LIHTC pairing)
  - Qualified 501(c)(3) bonds
  - Subject to state volume cap allocation (except 501(c)(3) and governmental)

**Taxable Municipal Bonds**:
- **Build America Bonds (BABs)**: Created under ARRA 2009 (expired 12/31/2010); 35% federal interest subsidy
- **Taxable revenue bonds**: When tax-exempt eligibility is unavailable or advantageous to issue taxable
- **Sustainability-Linked Bonds (SLBs)**: Typically taxable; step-up/step-down coupon tied to KPI achievement
- **Recovery Zone Economic Development Bonds**: Expired program; taxable with 45% credit

### 1.5 Short-Term Instruments
- **Bond Anticipation Notes (BANs)**: Bridge financing until long-term bonds are issued
- **Tax and Revenue Anticipation Notes (TRANs)**: Cash flow borrowing against expected tax/revenue receipts
- **Revenue Anticipation Notes (RANs)**: Secured by specific anticipated revenue
- **Commercial Paper (CP)**: Rolling short-term notes; requires liquidity facility (LOC or SBPA)
- **Variable Rate Demand Obligations (VRDOs)**: Long-term bonds with periodic rate resets and put features

### 1.6 Derivative Overlays
- **Interest rate swaps**: Fixed-to-floating or floating-to-fixed; synthetic fixed rate structures
- **Basis swaps**: SIFMA-to-LIBOR/SOFR
- **Caps/floors/collars**: Interest rate protection for variable-rate debt
- **Swaptions**: Options on swaps for advance refunding alternatives
- **Termination risk**: Mark-to-market termination payments; collateral posting requirements

---

## DOMAIN 2: ISSUER & GOVERNANCE TAXONOMY

### 2.1 Direct Issuers
Entities that issue bonds on their own behalf with their own credit:
- **States**: General obligation; transportation/highway revenue
- **Counties**: GO, revenue (utility, health system, solid waste)
- **Cities/Municipalities**: GO, utility revenue, TIF bonds, special assessment
- **School Districts**: GO (voter-approved), certificates of participation
- **Special Districts**: Water, sewer, fire protection, park, library, hospital
- **Public Utilities**: Electric, gas, water, wastewater (enterprise fund bonds)
- **Transit Authorities**: Farebox + sales tax revenue bonds

### 2.2 Conduit Issuers
Entities that issue bonds on behalf of a borrower; the conduit issuer typically has **no obligation** on the bonds:
- **Industrial Development Authorities (IDAs)**: Conduit for manufacturing, commercial, solid waste facilities
- **Health Facility Authorities**: Conduit for nonprofit hospitals, CCRCs, senior living
- **Housing Finance Agencies (HFAs)**: Single-family mortgage revenue bonds, multi-family PABs
- **Higher Education Facility Authorities**: Conduit for private colleges/universities
- **Economic Development Corporations**: Conduit for economic development projects
- **Public Finance Authorities** (e.g., Wisconsin PFA): State-level conduit programs

**Critical distinction**: In conduit issuance, the **obligated person** (borrower) — not the conduit issuer — is responsible for debt service. Credit analysis focuses on the borrower.

### 2.3 Transaction Participants

| Role | Function | Fiduciary Duty |
|------|----------|----------------|
| **Bond Counsel** | Renders tax opinion, drafts authorizing documents | To the transaction (not a party) |
| **Disclosure Counsel** | Assists with OS/POS preparation, 10b-5 letter | To the issuer or underwriter |
| **Underwriter** | Purchases bonds from issuer, resells to investors | Fair dealing (MSRB G-17) |
| **Financial Advisor (FA)** | Advises issuer on structure, timing, pricing | Fiduciary duty to issuer |
| **Trustee** | Holds funds, enforces covenants, represents bondholders | Fiduciary to bondholders |
| **Paying Agent** | Processes interest and principal payments | Ministerial |
| **Registrar** | Maintains bondholder records | Ministerial |
| **Credit Enhancer** | Provides insurance, LOC, or guarantee | Contractual |
| **Swap Counterparty** | Provides interest rate swap/derivative | Contractual |
| **Rating Agencies** | Assign credit ratings (Moody's, S&P, Fitch, Kroll) | Analytical independence |
| **Verification Agent** | Verifies sufficiency of escrow for refunding/defeasance | Ministerial |

### 2.4 Governance Structures
- **Inducement resolution**: Board action authorizing exploration of bond financing (non-binding)
- **Bond resolution/ordinance**: Formal authorization to issue bonds; establishes terms, covenants, flow of funds
- **Trust indenture**: Contract between issuer and trustee; defines bondholder rights
- **Master trust indenture (MTI)**: Framework for multiple series of bonds under common covenants
- **Supplemental indenture**: Amends or supplements the master indenture for a specific series
- **Loan agreement**: Between conduit issuer and borrower; mirrors bond terms
- **Continuing disclosure agreement (CDA)**: Post-issuance commitment to annual financial reporting and event notices (SEC Rule 15c2-12)

---

## DOMAIN 3: SECURITY & CREDIT STRUCTURE

### 3.1 Pledge Types

**Gross Revenue Pledge**: All revenues of the enterprise/system are pledged before operating expenses
- Strongest pledge type; operating expenses paid from residual after debt service
- Common in solid waste, water/sewer, hospital revenue bonds
- Bondholders have first claim on revenues

**Net Revenue Pledge**: Revenues pledged after payment of operations and maintenance (O&M) expenses
- O&M has priority over debt service
- Common in utility and enterprise fund bonds
- Lower bondholder priority but issuer retains operational flexibility

**Special Tax Pledge**: Specific tax revenues dedicated to debt service
- Sales tax, hotel/motel tax, fuel tax, sin tax
- Revenue limited to the pledged tax; no recourse to general fund

**Assessment Pledge**: Special assessments levied on benefited properties
- Community Facilities Districts (CFDs/Mello-Roos in California)
- Special Improvement Districts (SIDs)
- Assessment based on benefit received (land area, front footage, equivalent dwelling units)

**Ad Valorem Tax Pledge**: Property tax levy (GO bonds)

### 3.2 Lien Architecture
- **Senior lien (first lien)**: First priority claim on pledged revenues
- **Subordinate lien (junior lien)**: Claims only after senior lien debt service is fully paid
- **Pari passu**: Equal priority among bonds of the same series/lien level
- **Closed lien**: No additional bonds can be issued with equal priority
- **Open lien**: Additional bonds can be issued with equal priority if additional bonds test is met

### 3.3 Flow of Funds (Revenue Bond Waterfall)
Typical order of priority for pledged revenues:

1. **Revenue Fund**: All gross revenues deposited
2. **O&M Fund** (if net revenue pledge): Operating and maintenance expenses
3. **Debt Service Fund**: Current period principal and interest
4. **Debt Service Reserve Fund (DSRF)**: Replenishment to required level
5. **Renewal & Replacement Fund (R&R)**: Capital maintenance reserve
6. **Subordinate Debt Service**: Junior lien obligations
7. **Surplus Fund / General Fund**: Residual available for any lawful purpose

### 3.4 Credit Enhancement Mechanisms

| Enhancement | Description | Effect |
|------------|-------------|--------|
| **Debt Service Reserve Fund (DSRF)** | Cash reserve = max of (10% of par, MADS, 125% average annual DS) | Liquidity cushion for missed payments |
| **Surety bond** | Insurance company guarantees DSRF-equivalent amount | Replaces cash-funded DSRF |
| **Letter of Credit (LOC)** | Bank provides payment guarantee | Credit substitution to bank's rating |
| **Bond insurance** | Monoline insurer guarantees P&I payments | Rating uplift to insurer's rating |
| **Moral obligation** | State/local government "may" (not "shall") replenish reserve | Soft credit enhancement; not legally binding |
| **State intercept/aid** | State intercepts revenue (e.g., state aid to school districts) | Automatic diversion mechanism |
| **Additional bonds test (ABT)** | Historical or projected DSCR must exceed threshold before new debt | Protects existing bondholders from dilution |
| **Rate covenant** | Issuer agrees to set rates sufficient to meet coverage requirements | Revenue maintenance commitment |

### 3.5 Key Financial Covenants

**Debt Service Coverage Ratio (DSCR)**:
```
DSCR = Net Revenue Available for Debt Service / Annual Debt Service
```
- Minimum DSCR covenant: typically 1.10x - 1.50x depending on sector and rating
- Waste sector typical: 1.25x - 1.35x
- Hospital sector typical: 1.10x - 1.25x (lower due to operating complexity)
- CCRC sector: often 1.00x - 1.20x (higher risk tolerance due to entrance fees)
- **Additional bonds test**: Usually higher than minimum DSCR (e.g., 1.25x historical or 1.35x projected)

**Rate Covenant**: Issuer agrees to maintain rates/charges at levels producing minimum DSCR

**Additional Bonds Test**: Must demonstrate historical or projected coverage above threshold before issuing additional parity debt

**Springing Lien / Consultant Trigger**: If DSCR falls below covenant level, issuer must retain independent consultant

---

## DOMAIN 4: LEGAL & REGULATORY FRAMEWORK

### 4.1 Federal Tax Law (IRC)

**IRC Section 103**: Interest on state and local bonds is excluded from gross income if the bonds are not "private activity bonds" (or fit an exception)

**IRC Sections 141-150** — Private Activity Bond Rules:
- **141**: Definition of private activity bonds (private business use test: >10% of proceeds used by private entity; private security/payment test: >10% of debt service secured by private payments)
- **142**: Exempt facility bonds (enumerated categories: airports, docks, solid waste disposal, water/sewage, etc.)
- **143**: Mortgage revenue bonds
- **144**: Qualified small issue bonds, qualified redevelopment bonds
- **145**: Qualified 501(c)(3) bonds
- **146**: Volume cap ($120/capita or state floor, indexed for inflation; ~$110-$130 per capita currently)
- **147**: Other requirements: maturity limitation, land acquisition limitation, existing property limitation
- **148**: Arbitrage rules — yield restriction and rebate requirements
- **149**: Issuance requirements — registration, information reporting, hedge identification

**Arbitrage Rebate**: Issuers must rebate to the IRS any earnings on bond proceeds invested at yields exceeding the bond yield, unless an exception applies (6-month spending exception, 18-month spending exception, 24-month construction exception, small issuer exception)

**Private Use Remediation**: If bonds violate private use limits post-issuance, remediation options include: voluntary closing agreement program (VCAP), redemption or defeasance of non-qualified bonds, alternative use of proceeds

### 4.2 SEC Regulation

**Rule 15c2-12** (Continuing Disclosure):
- Applies to primary offerings >$1M
- Underwriter must reasonably determine issuer/obligated person has agreed to:
  - **Annual financial information**: Audited financial statements + specified operating data (within 180 days of fiscal year end, typically)
  - **Event notices**: Material events listed in the rule (rating changes, defaults, draw on reserves, etc.) — filed on EMMA within 10 business days
- **Listed events** (16 categories): Principal/interest payment delinquencies, non-payment related defaults, unscheduled draws on DSRF or credit enhancement, adverse tax opinions, rating changes, defeasances, tender offers, bankruptcy, etc.

**Securities Act / Exchange Act**:
- Municipal securities are exempt from Securities Act registration (Section 3(a)(2))
- Municipal securities are exempt from Exchange Act reporting
- BUT: anti-fraud provisions (Section 17(a) Securities Act, Section 10(b)/Rule 10b-5 Exchange Act) still apply
- Issuers can be held liable for material misstatements or omissions in official statements

### 4.3 MSRB Rules

| Rule | Subject | Key Requirements |
|------|---------|-----------------|
| **G-17** | Fair dealing | Underwriters must deal fairly; disclosure of conflicts, risks, compensation |
| **G-32** | Disclosures | Official statements submitted to EMMA within prescribed timeframes |
| **G-34** | CUSIP numbers | Obtaining and disseminating CUSIP numbers for new issues |
| **G-37** | Political contributions | Pay-to-play restrictions on municipal securities professionals |
| **G-38** | Consultants | Disclosure of consultant arrangements |
| **G-42** | Financial advisors | Fiduciary duty, conflicts disclosure, fair dealing for municipal advisors |

**EMMA (Electronic Municipal Market Access)**: MSRB's centralized platform for municipal bond disclosure
- Official statements, continuing disclosures, trade data, credit ratings
- Real-time trade reporting (RTRS)
- Free public access at emma.msrb.org

### 4.4 State-Level Framework
State enabling statutes govern:
- What entities can issue bonds (and what types)
- Voter approval requirements
- Debt limitations (as % of assessed valuation, typically)
- Conduit issuance authority
- Public purpose requirements
- Validation proceedings (judicial confirmation of bond authorization)

**State variation is significant**: Each state has its own municipal bond framework. Critical for analysis:
- Does the state authorize the bond type being considered?
- What approval process is required (legislative, executive, voter)?
- Are there debt limits that apply?
- What is the state's intercept or backstop mechanism (if any)?
- What is the state's approach to conduit issuance (liberal vs. restrictive)?

---

## DOMAIN 5: CREDIT ANALYSIS FRAMEWORK

### 5.1 Rating Agency Methodologies

**Moody's** — Sector-Specific Methodologies:
- *Waste & Environmental Services*: Franchise characteristics (exclusivity, service area stability), flow control, operating efficiency, financial metrics (operating margin, DSCR, leverage), management quality
- *Healthcare (Nonprofit Hospitals)*: Market position (leading, significant, adequate, limited), operating performance, balance sheet strength, governance/management
- *CCRCs*: Occupancy, financial cushion (days cash, MADS coverage), entrance fee dependency, competitive position

**S&P** — Sector-Specific Methodologies:
- Enterprise risk profile + financial risk profile matrix
- *Waste/Environmental*: Industry risk, competitive position, management/governance
- *Healthcare*: Business position, financial performance, financial flexibility
- Management and governance assessment (separate from financial analysis)

**Fitch** — Sector-Specific Methodologies:
- Revenue defensibility, operating risk, financial profile
- *Solid Waste*: Service area characteristics, rate flexibility, debt profile
- *Healthcare*: Revenue defensibility (market position, payor mix), operating risk (cost management, capex), financial profile (leverage, liquidity, DSCR)

**Kroll (KBRA)**:
- Growing presence in municipal healthcare ratings
- Governance assessment emphasized

### 5.2 Quantitative Metrics by Sector

#### Waste Management / Environmental Services
| Metric | AAA/AA | A | BBB | Below IG |
|--------|--------|---|-----|----------|
| Operating Margin | >25% | 15-25% | 10-15% | <10% |
| DSCR | >2.5x | 1.5-2.5x | 1.25-1.5x | <1.25x |
| Days Cash on Hand | >365 | 180-365 | 90-180 | <90 |
| Debt/Revenue | <2.0x | 2.0-4.0x | 4.0-6.0x | >6.0x |
| Revenue Concentration | <20% top customer | 20-40% | 40-60% | >60% |

#### Healthcare (Hospitals)
| Metric | AA | A | BBB | Below IG |
|--------|-----|---|-----|----------|
| Operating Margin | >4% | 2-4% | 0-2% | <0% |
| DSCR | >4.0x | 2.5-4.0x | 1.5-2.5x | <1.5x |
| Days Cash on Hand | >300 | 200-300 | 100-200 | <100 |
| Debt/Capitalization | <30% | 30-50% | 50-65% | >65% |
| Medicare/Medicaid % | <50% | 50-60% | 60-70% | >70% |

#### CCRCs
| Metric | Investment Grade | Below IG |
|--------|-----------------|----------|
| Independent Living Occupancy | >90% | <85% |
| MADS Coverage | >1.5x | <1.2x |
| Days Cash on Hand | >400 | <200 |
| Entrance Fee Refund Reserve | >90% funded | <70% funded |

### 5.3 Qualitative Factors
- **Management assessment**: Track record, transparency, strategic planning, succession
- **Governance**: Board independence, oversight practices, audit committee effectiveness
- **Economic base**: Service area demographics, income levels, employment diversity
- **Competitive position**: Market share, barriers to entry, franchise exclusivity
- **Regulatory environment**: Permitting stability, rate-setting authority, political support
- **ESG factors**: Environmental compliance, social impact, governance practices — increasingly integrated into credit analysis by all major agencies

### 5.4 Default and Recovery
- **Municipal default rates are historically very low**: ~0.1% cumulative 10-year default rate for investment-grade munis (Moody's data)
- **Revenue bonds default more frequently than GO bonds**: Revenue bonds ~0.3-0.5% vs. GO bonds ~0.01%
- **Sector variation is significant**: Healthcare/senior living/CCRC have the highest muni default rates; GO and essential-service utilities have the lowest
- **Recovery rates**: Generally high for secured revenue bonds (50-80%) but highly variable for healthcare (20-70% depending on facility viability)
- **Distressed exchanges**: Increasingly common as an alternative to formal default; covenant modifications, maturity extensions, rate adjustments

---

## DOMAIN 6: TRANSACTION LIFECYCLE

### 6.1 Pre-Issuance Phase
1. **Project identification and feasibility**: Issuer determines need for capital financing
2. **Financial advisor engagement**: FA retained to advise on structure, timing, market conditions
3. **Bond counsel engagement**: Counsel retained to draft authorizing documents and render tax opinion
4. **Inducement resolution**: Governing body authorizes exploration of bond financing (non-binding)
5. **Credit analysis**: Preliminary assessment of creditworthiness; engage rating agencies
6. **Validation proceedings** (optional): Judicial confirmation of bond authorization (provides legal certainty)
7. **TEFRA hearing** (if applicable): Required for private activity bonds; public hearing on proposed issuance

### 6.2 Structuring Phase
1. **Sizing**: Determine par amount based on project costs, reserves, issuance costs, capitalized interest
2. **Maturity schedule**: Serial bonds (annual maturities) + term bonds (bullet maturities with mandatory sinking fund)
3. **Call provisions**: Optional redemption (typically 10-year par call), mandatory sinking fund, extraordinary redemption
4. **Credit enhancement**: Evaluate insurance, LOC, DSRF funding, surety
5. **Tax analysis**: Determine eligibility for tax-exempt status; private use analysis; volume cap allocation
6. **Rating process**: Submit to 1-3 rating agencies; management presentations; receive preliminary ratings

### 6.3 Marketing and Pricing
1. **Preliminary Official Statement (POS)**: Draft disclosure document circulated to investors
2. **Retail order period**: Individual investors submit orders (typically 1-2 days)
3. **Institutional pricing**: Underwriter sets final yields based on market conditions and order flow
4. **Competitive sale** (alternative): Sealed bids from underwriting syndicates; lowest true interest cost wins
5. **Bond Purchase Agreement (BPA)**: Underwriter commits to purchase bonds at agreed prices

### 6.4 Closing and Settlement
1. **Official Statement (OS)**: Final disclosure document (POS updated with pricing)
2. **Closing**: Delivery of bonds, receipt of proceeds, execution of all transaction documents
3. **Settlement**: Funds distributed per flow of funds; project fund established; reserve funds funded
4. **Post-closing**: EMMA filings (OS, CDA), Form 8038 (IRS), state filings

### 6.5 Post-Issuance Compliance
1. **Continuing disclosure**: Annual financial statements + operating data filed on EMMA
2. **Event notices**: Material events filed on EMMA within 10 business days
3. **Arbitrage compliance**: Track investment earnings on bond proceeds; calculate rebate liability; file Form 8038-T
4. **Private use monitoring**: Ensure continued compliance with private use limits
5. **Covenant compliance**: DSCR calculation, rate covenant, additional bonds test
6. **Investor relations**: Respond to investor inquiries; maintain current financial information

### 6.6 Terminal Events
- **Maturity**: Bonds paid at par on stated maturity date
- **Optional redemption (call)**: Issuer redeems bonds prior to maturity, typically at par + premium
- **Mandatory sinking fund redemption**: Required annual payments on term bonds
- **Extraordinary redemption**: Triggered by specific events (casualty, condemnation, determination of taxability)
- **Defeasance**: Issuer deposits sufficient funds (typically US Treasuries/SLGS) in escrow to pay all remaining debt service; bonds are legally defeased and no longer considered outstanding
- **Current refunding**: New bonds issued to refund outstanding bonds within 90 days of call date
- **Advance refunding**: Pre-2017 TCJA: tax-exempt advance refundings permitted once. Post-2017: only taxable advance refundings permitted for tax-exempt bonds
- **Tender offer**: Issuer offers to purchase bonds from holders in the secondary market
- **Default and workout**: Failure to pay; appointment of receiver; restructuring; bankruptcy (Chapter 9 for municipalities)

---

## DOMAIN 7: MARKET & PRICING DYNAMICS

### 7.1 Primary Market

**Negotiated Sale**:
- Issuer selects underwriter(s) through RFP or relationship
- Allows for marketing and pre-sale investor engagement
- Majority of municipal bond sales are negotiated (~75-80%)
- Underwriter compensation: gross spread (management fee, underwriting fee, takedown)

**Competitive Sale**:
- Open bidding from underwriting syndicates
- Lowest True Interest Cost (TIC) or Net Interest Cost (NIC) wins
- Generally results in tighter pricing but less marketing flexibility
- Common for well-known, frequently issuing credits (states, large utilities)
- MSRB Rule G-34 requires electronic bid submission

**Direct/Private Placement**:
- Bonds sold directly to institutional buyer(s) without public offering
- Avoids disclosure requirements (no OS needed if exempt from 15c2-12)
- Common for small issues, bank-qualified bonds, or credits with limited market access

### 7.2 Secondary Market
- **Dealer-intermediated**: Municipal bonds trade OTC through approximately 100-150 active dealers
- **Thin liquidity**: Average municipal bond trades only 3-4 times per year after issuance
- **EMMA trade reporting**: Real-time trade prices and volumes published on EMMA
- **Bid-wanted auctions**: Dealers solicit bids from other dealers for client sell orders
- **Alternative Trading Systems (ATS)**: Electronic platforms (e.g., MuniBrokers, TMC Bonds)
- **Retail-dominated**: ~70% of municipal bonds are held by individuals (directly or through funds/ETFs)

### 7.3 Yield Curves and Benchmarks

**AAA MMD (Municipal Market Data)**:
- Benchmark AAA GO yield curve maintained by Refinitiv
- The primary benchmark for municipal bond pricing
- Curves published for various maturities (1-30 years)

**BVAL (Bloomberg Valuations)**:
- Bloomberg's municipal bond valuation curves
- Used for portfolio pricing and relative value analysis

**SIFMA Index** (formerly BMA):
- Weekly reset rate for tax-exempt variable-rate demand obligations (VRDOs)
- Benchmark for floating-rate municipal instruments

**ICE BofA Municipal Master Index**:
- Broad municipal bond market performance index
- Sector sub-indices available (healthcare, transportation, utility, etc.)

### 7.4 Credit Spreads
- Spreads measured relative to AAA MMD or comparable-maturity Treasuries
- **Typical spread ranges by rating** (10-year maturity, revenue bonds):
  - AA: 25-50 bps over AAA MMD
  - A: 50-100 bps
  - BBB: 100-200 bps
  - BB: 200-350 bps
  - Below BB: 350+ bps
- **Sector premium**: Healthcare bonds typically trade 10-25 bps wider than general revenue bonds at same rating
- **Liquidity premium**: Smaller issues (<$25M) trade 10-30 bps wider than benchmark-size deals

### 7.5 Tax-Equivalent Yield
```
Tax-Equivalent Yield = Tax-Exempt Yield / (1 - Marginal Tax Rate)
```
- At 37% federal rate: 3.00% tax-exempt = 4.76% taxable equivalent
- State tax exemption adds further value for in-state investors
- **Muni/Treasury ratio**: Tax-exempt yield / Treasury yield; historical average ~80-85%; above 100% indicates munis are "cheap" relative to Treasuries

### 7.6 Market Cycles and Supply/Demand
- **Seasonal patterns**: Heavy issuance in spring and fall; lighter in summer and year-end
- **Rate sensitivity**: Municipal bond prices move inversely with interest rates (modified duration)
- **Fund flows**: Mutual fund and ETF inflows/outflows significantly impact supply-demand balance
- **Tax reform risk**: Changes to marginal tax rates or municipal bond tax exemption directly impact relative value
- **Advance refunding elimination** (2017 TCJA): Reduced supply of new-money equivalent issuance
- **Credit events**: Defaults (Detroit 2013, Puerto Rico 2016) can cause sector-wide spread widening

---

## SECTOR-SPECIFIC CROSS-REFERENCES TO MUNI-PAL SCHEMA

### Waste/Environmental → Muni-Pal Schema Mapping
| Ontology Concept | Muni-Pal Schema Path | Notes |
|-----------------|---------------------|-------|
| Tipping fee revenue | `revenue.commodities.list` | Per-ton pricing |
| Franchise exclusivity | `risk.market` / `risk.regulatory` | Competitive barrier |
| Landfill closure liability | `risk.technology` | Post-closure funding |
| Flow control | `revenue.offtake.agreements` | Municipal contracts |
| Environmental permits | `permitting.air-quality.status` | Title V, Subtitle D |
| DSCR covenant | `finmodel.inputs.dscr.minimum` | Typically 1.25-1.35x |
| Revenue pledge | `security.revenue.pledge` | Gross or net |

### Healthcare → Muni-Pal Schema Mapping (TO BE DEVELOPED)
| Ontology Concept | Proposed Schema Path | Notes |
|-----------------|---------------------|-------|
| Payor mix | `healthcare.payor_mix` | Medicare/Medicaid/commercial % |
| Case mix index | `healthcare.case_mix_index` | Acuity measure |
| Occupancy rate | `healthcare.occupancy` | By care level |
| Days cash on hand | `healthcare.days_cash` | Liquidity measure |
| CON status | `healthcare.con_status` | Certificate of need |
| Master trust indenture | `security.mti` | Multi-facility structure |
| Entrance fee reserves | `healthcare.ccrc.entrance_fee_reserve` | CCRC-specific |
| Actuarial soundness | `healthcare.ccrc.actuarial` | CCRC-specific |

---

## KEY QUESTIONS BY DOMAIN

The agent should be able to answer these questions rigorously:

**Instruments**: What bond structure best matches this project's cash flow profile? Why?
**Issuers**: Is conduit issuance appropriate here? What authority has the enabling legislation?
**Security**: What pledge structure provides the strongest bondholder protection for this revenue stream?
**Legal**: Does this project qualify for tax-exempt financing under IRC 142? What private use issues exist?
**Credit**: How would Moody's/S&P evaluate this credit? What are the key rating drivers?
**Lifecycle**: What are the critical path items from inducement to closing?
**Market**: What spread should this credit trade at given its sector, rating, and structure? What are the comparables?
