# AI Usage Log

This document records the AI tools used during the development of the COD RTO Decision Engine, the specific tasks they assisted with, and 3 concrete examples where the AI produced incorrect, weak, or misleading suggestions and how they were diagnosed and corrected.

---

### 1. AI Tools Used & Scope of Assistance

- **Antigravity AI (Pair Programming Assistant powered by Gemini 3.8 / 2.5):**
  - Used for rapid script scaffolding, pandas data exploration scripts, and test suite generation.
  - Assisted in designing the ReportLab PDF compilation flow and Streamlit UI component layouts.
- **Large Language Model (Gemini 2.5 Flash API via `google-genai` SDK):**
  - Used in `core/llm_evaluator.py` to evaluate unstructured, colloquial Indian addresses and detect subtle bot/test name patterns.
  - Evaluated Hinglish navigation cues (*"ph krke aana"*, *"ke saamne"*) that cannot be parsed by standard Western address validators.

---

### 2. Concrete Examples Where AI Output Was Wrong or Weak, and How It Was Fixed

#### Example 1: The "ha" Substring Cancellation Bug in WhatsApp Flow
- **What the AI Suggested:**  
  When writing the incoming WhatsApp message handler, the AI drafted a quick keyword match to catch Hindi/Hinglish affirmations:
  ```python
  # AI's original code:
  if any(k in msg_lower for k in ["yes", "ha", "haan", "confirm", "ok", "bhejo"]):
      state = "CONFIRMED"
  ```
- **Why It Failed:**  
  When testing real customer cancellation phrases such as `"nahi chahiye cancel kar do"`, the system erroneously flagged the message as **CONFIRMED**! The substring `"ha"` was matching inside the word `"chahiye"` (and `"nahi"`), causing the bot to tell a customer who wanted to cancel that their order was packed and shipped.
- **How It Was Caught:**  
  During automated pytest execution, `test_whatsapp_flow_confirm_and_cancel` failed with:
  `AssertionError: assert FlowState.CONFIRMED == FlowState.CANCELLED_BY_CUSTOMER`.
- **How It Was Fixed:**  
  1. Replaced raw substring searching with regex word-boundary matching (`\bha\b`, `\byes\b`).
  2. Implemented strict priority checking: negative cancellation keywords (`cancel`, `nahi`, `mat bhejna`) are evaluated **before** confirmation keywords.

---

#### Example 2: Naive 50% RTO Cancellation Cutoff (Ignoring the 4.1x Asymmetry)
- **What the AI Suggested:**  
  In the initial decision engine rules, the AI recommended:
  *"If an order's estimated probability of RTO exceeds 50%, mark it as 'Hold / cancel' to protect operations from shipping losses."*
- **Why It Was Flawed:**  
  The AI treated RTO cost and false cancellation loss as equal (symmetric costs). However, in our business:
  - Preventing an RTO saves **₹169.40**.
  - Cancelling a genuine customer destroys **₹702.38** (₹402.38 in lost 62% gross margin + ₹300 sunk Meta CAC).
  - A false cancellation is **4.1 times more expensive** than an RTO!
  - When running the AI's 50% cutoff against the 2,018 orders, it cancelled over 160 orders and resulted in a **net negative profit impact (-₹16,849)** because the margin lost from genuine buyers far outweighed the courier fees saved.
- **How It Was Caught:**  
  Backtesting through `core/simulator.py` revealed that the "Hold / cancel" bucket was showing a negative net rupee return.
- **How It Was Fixed:**  
  Derived the exact mathematical breakeven formula:
  $$(1 - p) \times ₹402.38 - p \times ₹169.40 = 0 \implies p = \frac{402.38}{402.38 + 169.40} = 70.35\%$$
  Adjusted the cancellation cutoff to strictly $\ge 75\%$, reserving cancellations for repeat abusers ($\ge 2$ RTOs) and true bot/test accounts (`asdf` + `.` address). Moderate-risk orders (40–70%) were routed to WhatsApp confirmation and prepaid nudging, instantly swinging the net financial outcome from -₹16k to **+₹28,422 in net profit expansion**.

---

#### Example 3: Misclassifying Hinglish Colloquial Addresses as Low-Quality Garbage
- **What the AI Suggested:**  
  In a zero-shot address evaluation prompt, the LLM initially rated addresses like *"Station chowk se left, Hanuman Mandir ke saamne"* with a low quality score (0.35/1.0), reasoning: *"Address is missing flat number, street number, and official building designation."*
- **Why It Was Wrong:**  
  In Indian Tier-2/Tier-3 cities, postal addresses rarely follow Western numbering. Delivery boys navigate via landmarks and phone directions. In our actual dataset, these 388 Hinglish landmark orders delivered successfully **68.0% of the time**, generating over ₹1.5 Lakhs in gross margin! Flagging them as invalid would have destroyed genuine growth.
- **How It Was Caught:**  
  Cross-referencing the address categorization with historical delivery rates revealed that Hinglish landmark addresses delivered at more than double the rate of dummy entries (`.` or `xyz`).
- **How It Was Fixed:**  
  Updated the prompt system instructions and semantic parser with explicit domain guidance on Indian delivery logistics: instructions containing landmarks (`mandir`, `masjid`, `chowk`, `petrol pump`) and navigation cues (`ke paas`, `ke saamne`, `gali no`, `ph krke aana`) are recognized as deliverable and given a deliverability score of 0.65–0.85, routing them to **Ship after confirmation** rather than penalizing or cancelling them.
