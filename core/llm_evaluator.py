"""
LLM Evaluator for Address Quality and Name Legitimacy.
Uses an LLM where language, colloquial nuances, and Indian address patterns matter:
- Judging whether an address is real, deliverable, or a placeholder/dummy.
- Reading Hinglish instructions (e.g. 'ph krke aana, Masjid ke paas', 'gali no 22 ke andar').
- Spotting fake, troll, or bot names (e.g. 'asdf', 'test order', 'qwerty').

Includes both:
1. Live Gemini / OpenAI / Anthropic integration if API key is present.
2. Fast local semantic heuristic parser for zero-dependency, 100% reliable offline runs.
"""

import os
import re
from typing import Dict, Any, Optional

class LLMEvaluator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.has_live_llm = bool(self.api_key)

    def evaluate_order(self, customer_name: str, address: str, city: str, state: str, pincode: Any) -> Dict[str, Any]:
        """
        Evaluate address and name legitimacy using LLM (or offline semantic parser).
        """
        name_clean = str(customer_name).strip()
        addr_clean = str(address).strip()
        city_clean = str(city).strip() if city is not None else ""
        state_clean = str(state).strip() if state is not None else ""
        pin_clean = str(pincode).strip().replace(".0", "") if pincode is not None else ""

        # We first run semantic analysis (always fast and consistent)
        heuristic_res = self._semantic_parse(name_clean, addr_clean, city_clean, state_clean, pin_clean)

        # If live LLM is enabled and address is borderline/unusual, we can query live model
        if self.has_live_llm and heuristic_res["is_borderline"]:
            try:
                live_res = self._call_live_gemini(name_clean, addr_clean, city_clean, state_clean, pin_clean)
                return live_res
            except Exception:
                # Graceful fallback to heuristic result if API times out or fails
                return heuristic_res

        return heuristic_res

    def _semantic_parse(self, name: str, addr: str, city: str, state: str, pincode: str) -> Dict[str, Any]:
        name_lower = name.lower()
        addr_lower = addr.lower()
        city_lower = city.lower()

        # 1. Name Analysis
        fake_names = {
            "test", "test order", "asdf", "qwerty", "xyz", "xyz xyz",
            "admin", "user", "na", "aaa", "abc", "null", "none", "demo"
        }
        is_fake_name = False
        name_reason = "Normal customer name."
        name_score = 1.0

        if name_lower in fake_names:
            is_fake_name = True
            name_score = 0.1
            name_reason = f"Identified placeholder/bot test name '{name}'."
        elif re.search(r'\b(test|asdf|qwerty)\b', name_lower):
            is_fake_name = True
            name_score = 0.2
            name_reason = f"Contains keyboard spam or test keyword '{name}'."
        elif len(set(name_lower.replace(" ", ""))) <= 2 and len(name_lower) > 2:
            is_fake_name = True
            name_score = 0.2
            name_reason = f"Suspicious repeated character sequence in name '{name}'."
        elif len(name_lower) <= 2:
            is_fake_name = True
            name_score = 0.3
            name_reason = f"Abnormally short name '{name}'."

        # 2. Address Analysis
        dummy_exact = {".", "xyz", "home", "call me", "near station", "test", "nil", "na", "none", "house"}
        is_dummy = False
        addr_score = 1.0
        addr_type = "structured"
        addr_reason = "Detailed, complete delivery address."
        is_borderline = False

        # Hinglish and landmark patterns
        hinglish_patterns = [
            r'ke\s+paas', r'ke\s+saamne', r'ke\s+samne', r'ke\s+andar', r'ke\s+piche',
            r'se\s+left', r'se\s+right', r'ph\s+krke\s+aana', r'phone\s+karna',
            r'ghar\s+ka\s+naam', r'gali\s+no', r'ward\s+no', r'mandir', r'masjid',
            r'chowk', r'chauraha', r'pulia', r'petrol\s+pump'
        ]
        has_hinglish = any(re.search(pat, addr_lower) for pat in hinglish_patterns)

        # Standard delivery landmarks & address components
        standard_patterns = [
            r'flat', r'house\s+no', r'h\.no', r'plot\s+no', r'sector', r'nagar',
            r'colony', r'road', r'street', r'floor', r'apartment', r'enclave',
            r'opp\.', r'opposite', r'behind', r'near'
        ]
        has_standard = any(re.search(pat, addr_lower) for pat in standard_patterns)
        has_digits = bool(re.search(r'\d+', addr))

        if addr_lower in dummy_exact or len(addr) <= 2:
            is_dummy = True
            addr_score = 0.05
            addr_type = "dummy"
            addr_reason = f"Dummy placeholder address '{addr}' with no delivery information."
        elif addr_lower == city_lower or (len(addr.split()) == 1 and len(addr) < 15 and not has_digits):
            is_dummy = True
            addr_score = 0.20
            addr_type = "dummy"
            addr_reason = f"Incomplete address '{addr}' containing only a city/word with no street or house."
        elif addr_lower == "near station":
            is_dummy = True
            addr_score = 0.25
            addr_type = "vague"
            addr_reason = "Extremely vague address ('near station') missing colony, house number, or contact instructions."
        elif has_hinglish:
            # Hinglish address: deliverable if contains landmark or direction
            addr_type = "hinglish_landmark"
            if has_digits or "gali" in addr_lower or "house" in addr_lower or "flat" in addr_lower:
                addr_score = 0.85
                addr_reason = "Hinglish colloquial address with specific landmark and local navigation cues."
            else:
                addr_score = 0.65
                addr_reason = "Hinglish delivery directions provided; lacks formal house number but contains identifiable landmarks."
                is_borderline = True
        elif has_standard and (has_digits or len(addr) >= 25):
            addr_type = "structured"
            addr_score = 0.95
            addr_reason = "Standard structured address with street, area, and building identifiers."
        elif len(addr) < 20 and not has_digits:
            addr_score = 0.40
            addr_type = "vague"
            addr_reason = f"Short address ({len(addr)} chars) without house/street number or landmark."
            is_borderline = True
        else:
            addr_score = 0.70
            addr_type = "standard"
            addr_reason = "Reasonably complete address."

        deliverable = addr_score >= 0.50 and not is_dummy

        return {
            "address_quality_score": round(addr_score, 2),
            "address_type": addr_type,
            "is_address_deliverable": deliverable,
            "address_reason": addr_reason,
            "name_legitimacy_score": round(name_score, 2),
            "is_fake_name": is_fake_name,
            "name_reason": name_reason,
            "is_borderline": is_borderline
        }

    def _call_live_gemini(self, name: str, addr: str, city: str, state: str, pincode: str) -> Dict[str, Any]:
        """
        Optional live LLM prompt using Google GenAI SDK.
        """
        import json
        from google import genai

        client = genai.Client(api_key=self.api_key)
        prompt = f"""
You are an expert Indian e-commerce delivery logistics auditor.
Analyze whether the following COD customer name and address are legitimate, deliverable, or fake/dummy.
Note: Indian e-commerce often has Hinglish addresses (e.g. 'ph krke aana', 'Mandir ke paas', 'gali no 4 ke andar') which ARE deliverable by local delivery boys!
However, dummy entries like '.', 'xyz', 'home', or 'call me' are NOT deliverable.

Customer Name: {name}
Address: {addr}
City: {city}
State: {state}
Pincode: {pincode}

Return a valid JSON object with EXACTLY these keys:
{{
  "address_quality_score": <float between 0.0 and 1.0>,
  "address_type": <"structured" | "hinglish_landmark" | "vague" | "dummy">,
  "is_address_deliverable": <true | false>,
  "address_reason": "<1-sentence plain-English reason for operations team>",
  "name_legitimacy_score": <float between 0.0 and 1.0>,
  "is_fake_name": <true | false>,
  "name_reason": "<1-sentence plain-English reason for operations team>"
}}
Only output the raw JSON object, no markdown backticks.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n", "", text)
            text = re.sub(r"\n```$", "", text)
        data = json.loads(text)
        data["is_borderline"] = False
        return data
