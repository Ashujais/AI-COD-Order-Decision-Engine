# COD Guardian: AI-Powered RTO Triage & Decision Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

> **Associate Software Engineer / AI Automation Engineer — Take-Home Assignment**  
> An automated, production-grade COD triage engine for a D2C haircare brand (Shopify) to eliminate RTO (Return to Origin) cash burn while aggressively preserving customer acquisition and top-line growth.

---

## ⚡ Quick Start (Run in under 10 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Comprehensive CLI Demo & Backtest
Evaluates all 2,018 historical orders, prints the Founder Morning Brief, showcases operations-friendly plain-English reasons, tests the WhatsApp state machine, and verifies prepaid discount math:
```bash
python run_demo.py
```

### 3. Launch the Founder Morning Dashboard
Opens the interactive web application featuring the morning brief KPI cards, the Head of Ops vs. Marketing trade-off simulator, live threshold sliders, and an interactive WhatsApp chat preview:
```bash
python run_dashboard.py
# Or directly:
streamlit run dashboard/app.py
```

### 4. Run the Automated Test Suite
Runs all 11 unit and integration tests:
```bash
python -m pytest tests/
```

### 5. (Optional) Recompile the Executive PDF Memo
Compiles the 2-page executive memorandum to `BUSINESS_MEMO.pdf`:
```bash
python generate_memo_pdf.py
```

---

## 🎯 The Business Problem & Financial Context

- **Monthly Volume:** ~3,000 orders/month
- **Average Order Value (AOV):** ₹649
- **COD Share:** 55% (~1,650 COD orders/month)
- **Baseline COD RTO Rate:** **28.4%** (compared to only 4% on prepaid)
- **Delivered Gross Margin (62%):** **+₹402.38** per order
- **Cost of an RTO:**
  - Forward shipping: ₹65
  - Reverse return shipping: ₹65
  - Packaging & handling: ₹25
  - 8% damaged/unsellable stock (avg product cost ₹180): ₹14.40
  - **Total Cash Lost per RTO = ₹169.40**
- **Meta Ads Customer Acquisition Cost (CAC):** ₹300+ per first-time buyer.

---

## ⚖️ Resolving the Leadership Conflict: Operations vs. Marketing

| Stakeholder | Argument | Flaw in Logic | Net Impact on 2,018 Orders |
| :--- | :--- | :--- | :---: |
| **Head of Operations** | *"RTO is killing us. Cancel any risky COD order. If a pincode has bad history, stop COD."* | **Cancelling a genuine order costs ₹702** (₹402 gross margin + ₹300 Meta CAC), which is **4.1x more damaging than an RTO**. Blanket bans kill customer acquisition. | **-₹120,000+** (mass cancellation destroys genuine gross profit) |
| **Head of Marketing** | *"We spend ₹300+ on Meta ads. Please don't cancel orders or kill growth."* | Shipping every order blindly bleeds cash on 573 returns. | **-₹97,000** (pure shipping & product damage drain) |
| **Our Balanced AI Engine** | **Precision 4-Tier Triage**: Cancels only true fraud ($\ge 75\%$ risk), nudges high-value COD to prepaid, and verifies moderate-risk orders via WhatsApp. | Satisfies both leaders: **slashes RTO costs by ₹65,089 while preserving 96.5% of sales**. | **+₹28,422 NET GAIN** (+₹14.08 / order) |

---

## 🏗️ System Architecture & Where We Drew the Line on AI

```
                        [ Incoming COD Order ]
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
   [ Fast Code / Maths ]                         [ LLM Evaluator ]
  - Customer order & RTO history                - Colloquial Indian addresses
  - Exact phone format validation               - Hinglish navigation cues
  - High order value brackets                   - Bot / test name detection
  - State-level baseline rates                  - Landmark & completeness score
         │                                                 │
         └────────────────────────┬────────────────────────┘
                                  ▼
                   [ Hybrid Decision Engine ]
        (Evaluates risk against non-technical config.json)
                                  │
      ┌──────────────┬────────────┴─────────────┬──────────────┐
      ▼              ▼                          ▼              ▼
[ 1. Ship As-Is ] [ 2. Confirm WhatsApp ] [ 3. Nudge Prepaid ] [ 4. Hold/Cancel ]
 (Repeat buyers &  (Hinglish/vague addrs;  (High-value COD;     (Serial RTO >=2 &
 clean addresses)   intent verification)    Rs 50 discount)      bot test orders)
```

### Where Code / Maths Does It:
- **Numerical History:** Detecting serial returners (`customer_prior_rto >= 2` $\rightarrow$ 76.5% failure rate).
- **Phone Validation:** Flagging non-10 digit numbers and repeated digits (`9999999999`).
- **Unit Economics & Margins:** Calculating breakeven thresholds, financial trade-offs, and dynamic discounts.
- **Why:** Code/maths is 1,000x faster, deterministic, 100% auditable, and incurs zero API costs.

### Where LLM Does It:
- **Indian & Hinglish Addresses:** Interpreting local colloquial cues like *"ph krke aana, Masjid ke paas"*, *"gali no 22 ke andar"*, *"Nehru chowk se left"*.
- **Distinguishing Junk from Authentic Landmark Instructions:** In historical data, Hinglish landmark orders delivered **68.0% of the time**! Naive regex marks them as invalid, which would kill ₹1.5 Lakhs in sales. True dummy placeholders (`.`, `xyz`, `home`, `call me`) failed 62%–73% of the time. The LLM tells the difference.
- **Bot / Test Names:** Spotting keyboard spam and test accounts (`asdf`, `qwerty`, `Test Order`, `xyz xyz`).

---

## 📦 Historical Simulation Results (Last Month's 2,018 Orders)

| Action Bucket | Count | Share (%) | Historical RTO % | Avg Value | Plain-English Reason Example | Net ₹ Impact |
| :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| **1. Ship as-is** | 654 | 32.4% | 15.7% | ₹738 | *"Verified repeat buyer (3 past orders, 0 returns). Fast-tracked for immediate dispatch."* | ₹0 (base) |
| **2. Ship after confirm** | 872 | 43.2% | 29.7% | ₹675 | *"Colloquial Hinglish landmark address. WhatsApp confirmation requested to ensure delivery availability."* | **+₹28,518** |
| **3. Nudge to prepaid** | 422 | 20.9% | 37.2% | ₹1,704 | *"High value COD risk (₹1,704). Offering ₹50 discount to convert to prepaid (4% RTO) and protect gross margin."* | **+₹6,322** |
| **4. Hold / cancel** | 70 | 3.5% | 77.1% | ₹912 | *"Cancelled: Customer has 2 prior return history (76.5% RTO rate). COD suspended to stop serial returns."* | -₹6,419 |
| **TOTALS** | **2,018** | **100.0%** | **28.4%** | **₹897** | **Avoided RTO Costs: ₹65,089 \| Net Margin Gain:** | **+₹28,422** |

---

## 💬 WhatsApp Confirmation & Prepaid Flow (Part 2)

### 1. "Ship After Confirmation" Flow
- **When It Goes Out:** 5 minutes after order placement (catches buyers while still attentive).
- **Language:** Hinglish (default for Indian D2C) or clean English.
- **Interactive Buttons:** `[ Confirm Order ✅ ]`, `[ Change Address 📍 ]`, `[ Cancel Order ❌ ]`.
- **Handling Responses:**
  - **"Yes" / Confirm / "bhej do":** Order marked `CONFIRMED` $\rightarrow$ moved to warehouse dispatch queue.
  - **"No" / Cancel / "nahi chahiye":** Order immediately marked `CANCELLED_BY_CUSTOMER`. Prevents forward freight (₹65), reverse freight (₹65), packaging (₹25), and product damage risk (₹14.40) before packing.
  - **"Change Address":** Bot prompts for house/street number and landmark; updates Shopify shipping address, then confirms.
  - **Random / FAQs ("kab aayega?"):** NLP intent classifier answers expected delivery timeframe (3–4 days) and re-prompts for confirmation.
  - **24-Hour Timeout:** Gentle reminder at 12 hours. At 24 hours, the order is automatically moved to `ON_HOLD` with an "Unpause My Order" reactivation button.

### 2. "Nudge to Prepaid" Flow & Mathematical Proof for ₹50 Discount
- **When It Goes Out:** 2 minutes post-checkout on high-value or high-risk COD orders.
- **Value Proposition:** Instant ₹50 discount via UPI/Card link + priority express dispatch.
- **The Mathematical Proof:**
  - Delivered Gross Profit: $62\% \times ₹649 = \mathbf{₹402.38}$
  - Expected RTO cost on Risky COD (35% RTO): $0.35 \times ₹169.40 = \mathbf{₹59.29}$
  - Expected RTO cost on Prepaid (4% RTO): $0.04 \times ₹169.40 = \mathbf{₹6.78}$
  - **Direct RTO Shipping Cost Savings Delta:** $₹59.29 - ₹6.78 = \mathbf{₹52.51}$
  - **The ₹50 discount is 100% self-funded by the ₹52.51 reduction in shipping waste alone!**
  - **Net Profit on Prepaid with Discount:** $(1 - 0.04) \times (₹402.38 - ₹50) - ₹6.78 = \mathbf{₹331.50}$
  - **Net Profit on Risky COD:** $(1 - 0.35) \times ₹402.38 - ₹59.29 = \mathbf{₹202.26}$
  - **Net Financial Advantage per Conversion:** $₹331.50 - ₹202.26 = \mathbf{+₹129.24}$!

---

## 🖥️ Simple Morning Dashboard (Part 3)

The dashboard (`dashboard/app.py`) provides the founder with an instant morning pulse:
1. **The 4 Morning Numbers:** Total orders, ₹ saved from avoided RTOs, ₹ lost from false cancellations, and **Net ₹ Impact**.
2. **Yesterday's Bucket Distribution:** Instant breakdown of the 4 buckets with historical RTO rates.
3. **Leadership Comparator:** Side-by-side financial simulation of Ops' Policy vs. Marketing's Policy vs. Our AI Engine.
4. **Interactive WhatsApp Simulator:** Test real customer replies ("Yes", "No", "kal bhejoge?", timeout simulations).
5. **No-Code Configuration Sliders:** Change risk thresholds and prepaid discount amounts in real time without touching code.

---

## 📁 Repository Structure

```
.
├── orders_sample.csv               # Historical dataset (2,018 past COD orders)
├── config.json                     # Non-technical operational thresholds & financial parameters
│
├── core/
│   ├── __init__.py
│   ├── financial_model.py          # Unit economics, RTO formulas, and prepaid discount proof
│   ├── llm_evaluator.py            # LLM address quality & bot name auditor (with offline fallback)
│   ├── decision_engine.py          # 4-bucket decision routing & plain-English reasons
│   └── simulator.py                # Batch historical backtesting engine
│
├── whatsapp/
│   ├── __init__.py
│   ├── templates.py                # Multilingual message templates & quick reply buttons
│   ├── flow_manager.py             # State machine handling yes/no/random/timeout transitions
│   └── mock_service.py             # Mock Meta Cloud API webhook handler
│
├── dashboard/
│   ├── __init__.py
│   └── app.py                      # Founder Morning Brief & Interactive Streamlit Dashboard
│
├── tests/
│   ├── __init__.py
│   └── test_engine.py              # Automated test suite (11 unit & integration tests)
│
├── run_demo.py                     # 1-command CLI demonstration & batch evaluation
├── run_dashboard.py                # 1-command launcher for Streamlit dashboard
├── generate_memo_pdf.py            # Compiles BUSINESS_MEMO.pdf via ReportLab
│
├── BUSINESS_MEMO.md                # Executive Memo to the Founder (Part 4)
├── BUSINESS_MEMO.pdf               # High-res, 2-page executive PDF
├── DECISION_LOG.md                 # Design choices, alternatives considered, and trade-offs
├── AI_USAGE_LOG.md                 # AI tools used, prompts, and 3 weak/wrong AI cases & fixes
├── README.md                       # Comprehensive system documentation
└── requirements.txt                # Python dependencies
```

---

## 📋 Deliverables Checklist

- [x] **Part 1:** Decision Engine producing 4 buckets with short, plain-English reasons & no-code configurable thresholds (`config.json`).
- [x] **Part 2:** WhatsApp confirmation & prepaid nudge flow with mock API, timeout handling, and mathematical proof for ₹50 discount.
- [x] **Part 3:** Streamlit dashboard answering the founder's 4 morning questions with interactive simulator.
- [x] **Part 4:** 2-page Business Memo (`BUSINESS_MEMO.md` and compiled `BUSINESS_MEMO.pdf`) covering surprising findings, rule impact, Ops vs. Marketing trade-off, failure modes, and 2-week roadmap.
- [x] **Decision Log:** Comprehensive list of choices, alternatives, and rationale (`DECISION_LOG.md`).
- [x] **AI Usage Log:** Transparent log of AI tools and 3 concrete examples of caught and fixed errors (`AI_USAGE_LOG.md`).
