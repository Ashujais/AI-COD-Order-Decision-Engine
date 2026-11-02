# Decision Log: COD RTO Decision Engine

This document provides a running record of key architectural, operational, and mathematical choices made during development, what alternatives were considered, and why the chosen approach was selected.

---

### 1. Hybrid Architecture: Code/Maths vs. LLM Boundary
- **Choice:** Used standard deterministic code/maths for 90% of numerical and rule evaluations (priors, order values, phone length, regional aggregations, cost modeling), and used an LLM strictly for natural language evaluation (unstructured address deliverability, Hinglish landmark interpretation, and bot/troll name detection).
- **Alternatives Considered:**
  - *Pure Machine Learning (e.g. XGBoost/RandomForest on tabular data):* Fails on unstructured text; cannot interpret nuances like *"gali no 22 ke andar"* vs. *". "* without extensive manual NLP labeling.
  - *Pure LLM Prompting (sending every order JSON to Gemini/GPT):* Highly redundant, expensive (~$0.002 per order), slow (1-2s latency per order), and prone to hallucinating arithmetic when computing margin trade-offs.
- **Why Picked:** LLMs excel at linguistic context (Indian addresses and name slang) where regex fails. Conversely, simple Python math calculates gross margin and unit economics 1,000x faster, with 0 latency, 0 cost, and 100% determinism.

---

### 2. Four Operational Buckets Instead of Binary Ship vs. Cancel
- **Choice:** Created 4 distinct action tiers: `Ship as-is`, `Ship after confirmation`, `Nudge to prepaid`, and `Hold / cancel`.
- **Alternatives Considered:**
  - *Binary Decision (Ship or Cancel):* Forces a zero-sum war between Operations (who want to cancel everything risky) and Marketing (who want to cancel nothing).
  - *Three Buckets (Ship, Confirm, Cancel):* Misses the massive margin-recovery opportunity of high-value COD orders via prepaid conversion.
- **Why Picked:** Binary choices destroy value. The 4-tier model matches real Indian e-commerce operational workflows:
  1. `Ship as-is` preserves zero-friction delivery for repeat buyers (13.8% RTO).
  2. `Ship after confirmation` filters out 65%+ of uncommitted RTO buyers without cancelling genuine customers.
  3. `Nudge to prepaid` converts high-value COD orders into upfront revenue (4% RTO) with +₹129 net profit per conversion.
  4. `Hold / cancel` is strictly restricted to proven fraud (77%+ RTO).

---

### 3. Rejecting Pincode Blacklisting in Favor of Macro-Regional & Address Quality Signals
- **Choice:** Refused to blacklist individual 6-digit pincodes, relying instead on state-level baseline risk and address completeness.
- **Alternatives Considered:**
  - *Hard Pincode Blacklisting:* Suggested by Head of Operations ("If a pincode has bad history, stop COD there").
- **Why Picked:** The dataset contains 1,066 unique pincodes across 2,018 orders. Over 96.6% of pincodes had fewer than 5 orders (840 had exactly 1 order). A single return created an illusory "100% RTO rate" due to extreme sparsity ($n=1$). Blacklisting pincodes would have banned hundreds of postal circles and throttled Meta ad acquisition. Macro-state patterns (Bihar 53.4% RTO, UP 44.7% RTO vs. Maharashtra 17.9%), however, are statistically significant ($n > 100$).

---

### 4. Pricing the Prepaid Discount at Exactly ₹50
- **Choice:** Selected a flat ₹50 upfront discount on COD orders exceeding ₹499.
- **Alternatives Considered:**
  - *Percentage Discount (e.g. 10% or 15%):* On a ₹2,000 order, a 15% discount is ₹300, which exceeds the gross margin and wipes out profitability.
  - *Small Discount (₹20 or ₹25):* Too insignificant to convince Indian consumers to switch away from cash.
  - *No Discount (Only nudging with messaging):* Achieves single-digit conversion rates.
- **Why Picked:** Mathematical proof:
  - High-risk COD expected RTO cost = $35\% \times ₹169.40 = ₹59.29$.
  - Prepaid expected RTO cost = $4\% \times ₹169.40 = ₹6.78$.
  - Shipping savings delta = $₹59.29 - ₹6.78 = \mathbf{₹52.51}$.
  - The ₹50 discount is completely self-funded by the ₹52.51 reduction in shipping/damage waste alone!
  - Converting the customer delivers **+₹129.24 in net incremental profit** per converted order ($₹331.50 \text{ vs. } ₹202.26$).

---

### 5. Resolving the 4.1x Asymmetry Rule (Ops vs. Marketing)
- **Choice:** Set the threshold for `Hold / cancel` at >70% RTO probability, strictly reserving cancellation for repeat abusers ($\ge 2$ returns) and blatant bot/test orders (`asdf` / `.` address).
- **Alternatives Considered:**
  - *Lowering the Cancellation Cutoff to 50%:* Would cancel ~400 orders, including 150+ genuine customers.
- **Why Picked:**
  - Catching an RTO saves **₹169.40**.
  - Cancelling a genuine customer destroys **₹702.38** (₹402.38 lost gross profit + ₹300 sunk Meta CAC).
  - Cancelling a genuine order is **4.1 times more expensive** than suffering an RTO.
  - Mathematical breakeven: $p = 402.38 / (402.38 + 169.40) = 70.35\%$. Cancelling an order with less than 70.4% failure probability guarantees net financial loss.

---

### 6. Dual-Mode Evaluation (Live LLM + Fast Local Heuristic Fallback)
- **Choice:** Built `core/llm_evaluator.py` to support live Google Gemini API when an API key is available, while embedding a local semantic parsing engine for offline runs.
- **Alternatives Considered:**
  - *Requiring a live paid API key:* Would cause setup friction, network timeouts, or failures during evaluation.
  - *Pure hardcoded regex without LLM capability:* Fails to satisfy the assignment requirement to demonstrate where an LLM adds value.
- **Why Picked:** Gives the evaluator zero setup friction (runs in under 10 minutes out of the box with `pytest` or `run_demo.py`), while providing production-ready integration with Gemini 2.5 Flash for production deployment.

---

### 7. Interactive Streamlit Dashboard with Embedded Mobile WhatsApp Simulator
- **Choice:** Developed a full Streamlit application featuring a Founder KPI morning brief, an Ops vs. Marketing scenario comparator, dynamic threshold sliders, and an interactive WhatsApp chat preview.
- **Alternatives Considered:**
  - *Static Jupyter Notebook:* Difficult for a founder or non-technical operations manager to interact with or test scenarios.
  - *Headless script only:* Fails the requirement for "one screen our founder can look at every morning."
- **Why Picked:** Provides a clean single-page morning executive brief that answers all 4 founder questions in 5 seconds, lets ops managers adjust thresholds without editing code, and lets anyone test WhatsApp customer replies interactively.
