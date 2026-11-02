"""
Test Suite for COD Decision Engine, Financial Models, and WhatsApp Flow.
Run: pytest tests/
"""

import pytest
from core.financial_model import BusinessEconomics
from core.llm_evaluator import LLMEvaluator
from core.decision_engine import DecisionEngine
from core.simulator import BatchSimulator
from whatsapp.flow_manager import WhatsAppFlowManager, FlowState

def test_financial_model_rto_cost():
    econ = BusinessEconomics()
    # ₹65 forward + ₹65 return + ₹25 packaging + (8% * ₹180 = ₹14.40) = ₹169.40
    assert round(econ.rto_cost_per_order, 2) == 169.40

def test_prepaid_discount_math():
    econ = BusinessEconomics()
    proof = econ.compute_prepaid_discount_justification()
    assert proof["proposed_discount"] == 50.0
    assert proof["rto_savings_delta"] >= 52.0
    assert proof["net_gain_to_brand_per_conversion"] > 100.0

def test_llm_dummy_address_detection():
    llm = LLMEvaluator()
    res_dot = llm.evaluate_order("Sneha Iyer", ".", "Mumbai", "Maharashtra", 400001)
    assert res_dot["address_type"] == "dummy"
    assert not res_dot["is_address_deliverable"]

    res_xyz = llm.evaluate_order("Rahul Sharma", "xyz", "Delhi", "Delhi", 110001)
    assert res_xyz["address_type"] == "dummy"

def test_llm_hinglish_address_detection():
    llm = LLMEvaluator()
    addr = "Station chowk se left, Hanuman Mandir ke saamne"
    res = llm.evaluate_order("Ananya Verma", addr, "Patna", "Bihar", 800001)
    assert res["address_type"] == "hinglish_landmark"
    # Hinglish landmark addresses are deliverable by local delivery partners!
    assert res["is_address_deliverable"]

def test_llm_fake_name_detection():
    llm = LLMEvaluator()
    res_fake = llm.evaluate_order("asdf", "Flat 101, Palm Beach Road", "Mumbai", "Maharashtra", 400050)
    assert res_fake["is_fake_name"]

    res_test = llm.evaluate_order("Test Order", "House 12, Sector 4", "Delhi", "Delhi", 110001)
    assert res_test["is_fake_name"]

    res_real = llm.evaluate_order("Pooja Sharma", "House 12, Sector 4", "Delhi", "Delhi", 110001)
    assert not res_real["is_fake_name"]

def test_decision_serial_rto_hold_cancel():
    engine = DecisionEngine()
    order = {
        "order_id": "TEST_RTO_ABUSER",
        "customer_name": "Pooja Joshi",
        "phone": "9876543210",
        "address": "182/9, Ring Road",
        "city": "Jaipur",
        "state": "Rajasthan",
        "order_value": 499,
        "customer_prior_orders": 3,
        "customer_prior_rto": 2
    }
    decision = engine.evaluate_order(order)
    assert decision["action"] == "Hold / cancel"
    assert "prior return" in decision["reason"].lower()

def test_decision_repeat_customer_ship_as_is():
    engine = DecisionEngine()
    order = {
        "order_id": "TEST_GOOD_REPEAT",
        "customer_name": "Rohan Gupta",
        "phone": "9876543210",
        "address": "Flat 402, Sunshine Apartments, MG Road",
        "city": "Mumbai",
        "state": "Maharashtra",
        "order_value": 649,
        "customer_prior_orders": 3,
        "customer_prior_rto": 0
    }
    decision = engine.evaluate_order(order)
    assert decision["action"] == "Ship as-is"
    assert "repeat buyer" in decision["reason"].lower()

def test_decision_high_value_nudge_prepaid():
    engine = DecisionEngine()
    order = {
        "order_id": "TEST_HIGH_VAL",
        "customer_name": "Kavita Rao",
        "phone": "9876543210",
        "address": "House 54, Sector 14",
        "city": "Patna",
        "state": "Bihar",
        "order_value": 2499,
        "customer_prior_orders": 0,
        "customer_prior_rto": 0
    }
    decision = engine.evaluate_order(order)
    assert decision["action"] == "Nudge to prepaid"
    assert "prepaid" in decision["reason"].lower()

def test_whatsapp_flow_confirm_and_cancel():
    flow = WhatsAppFlowManager()
    order = {
        "order_id": "KT9999",
        "customer_name": "Meera Nair",
        "order_value": 699,
        "address": "Nehru chowk ke paas",
        "city": "Lucknow"
    }
    flow.start_flow(order, "Ship after confirmation")
    assert flow.conversations["KT9999"]["state"] == FlowState.AWAITING_CONFIRMATION

    # Test "Yes" confirmation
    res_yes = flow.process_incoming_message("KT9999", "yes bhej do please")
    assert res_yes["state"] == FlowState.CONFIRMED

    # Test "Cancel" on another conversation
    flow.start_flow(order, "Ship after confirmation")
    res_cancel = flow.process_incoming_message("KT9999", "nahi chahiye cancel kar do")
    assert res_cancel["state"] == FlowState.CANCELLED_BY_CUSTOMER

def test_whatsapp_24h_timeout():
    flow = WhatsAppFlowManager()
    order = {
        "order_id": "KT_TIMEOUT",
        "customer_name": "Vikram Seth",
        "order_value": 899,
        "address": "MG Road",
        "city": "Delhi"
    }
    flow.start_flow(order, "Ship after confirmation")
    res = flow.simulate_timeout("KT_TIMEOUT", hours=24)
    assert res["state"] == FlowState.HELD_ON_TIMEOUT
    assert "Paused" in res["template"]["body"]

def test_batch_simulation_runs():
    simulator = BatchSimulator()
    res = simulator.run_simulation("orders_sample.csv")
    assert res["total_orders"] == 2018
    assert res["financial_summary"]["net_profit_impact_inr"] > 0
    assert len(res["action_counts"]) == 4
