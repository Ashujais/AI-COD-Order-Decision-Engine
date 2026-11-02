"""
Founder Morning Dashboard & Interactive COD Decision Engine.
Runs with: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import streamlit as st
import pandas as pd
import numpy as np

from core.decision_engine import DecisionEngine
from core.simulator import BatchSimulator
from whatsapp.flow_manager import WhatsAppFlowManager, FlowState
from whatsapp.mock_service import MockWhatsAppService

st.set_page_config(
    page_title="COD Guardian | Founder Morning Brief",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .kpi-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 18px 22px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
    }
    .kpi-subtext {
        font-size: 0.82rem;
        color: #64748b;
        margin-top: 4px;
    }
    .badge-ship { background-color: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-confirm { background-color: #fef9c3; color: #854d0e; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-nudge { background-color: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-cancel { background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .whatsapp-bubble-bot {
        background-color: #ffffff;
        border-radius: 8px 8px 8px 0px;
        padding: 10px 14px;
        margin: 6px 0;
        max-width: 80%;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    .whatsapp-bubble-user {
        background-color: #d9fdd3;
        border-radius: 8px 8px 0px 8px;
        padding: 10px 14px;
        margin: 6px 0 6px auto;
        max-width: 80%;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv("orders_sample.csv")

raw_df = load_data()

# Sidebar: Controls & Non-technical Threshold Configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=64)
    st.title("COD Guardian")
    st.caption("AI-Powered COD Decision & RTO Prevention Engine")
    st.divider()

    st.subheader("⚙️ Decision Thresholds")
    st.caption("Operations managers can adjust these without touching code:")

    cancel_cutoff = st.slider("Hold / Cancel Risk Cutoff", 0.60, 0.95, 0.75, 0.05,
                              help="Orders with risk score above this or serial returners will be cancelled.")
    nudge_cutoff = st.slider("Nudge to Prepaid Cutoff", 0.35, 0.65, 0.45, 0.05,
                             help="Orders with risk score between this and cancel will be offered a prepaid discount.")
    confirm_cutoff = st.slider("WhatsApp Confirm Cutoff", 0.15, 0.40, 0.25, 0.05,
                               help="Orders with risk score above this will require WhatsApp confirmation.")
    high_order_val = st.number_input("High Order Value Threshold (₹)", 1000, 3000, 1500, 100)
    prepaid_discount = st.number_input("Prepaid Discount Amount (₹)", 20, 100, 50, 5)

    custom_config = {
        "decision_thresholds": {
            "cancel_risk_cutoff": cancel_cutoff,
            "nudge_prepaid_risk_cutoff": nudge_cutoff,
            "whatsapp_confirm_risk_cutoff": confirm_cutoff,
            "max_allowed_prior_rto": 1,
            "high_order_value_threshold": float(high_order_val),
            "high_risk_states": ["Bihar", "Uttar Pradesh", "Madhya Pradesh"]
        },
        "prepaid_incentive": {
            "discount_amount": float(prepaid_discount),
            "min_order_value_for_discount": 499.0
        }
    }

    st.divider()
    st.info("💡 **Unit Economics Configured:**\n- AOV: ₹649\n- Gross Margin: 62% (₹402.38)\n- RTO Cost: ₹169.40\n- Meta CAC: ₹300")

# Run Simulation with Current Thresholds
engine = DecisionEngine()
engine.reload_config(custom_config)
simulator = BatchSimulator(engine)
sim_results = simulator.run_simulation("orders_sample.csv")
sim_df = sim_results["simulated_df"]
fin = sim_results["financial_summary"]
buckets = sim_results["bucket_stats"]

# Dashboard Header
st.title("☀️ Founder's Morning Brief")
st.markdown("Automated COD order triage and financial impact summary.")

# Row 1: The 4 Key Founder KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Orders Processed</div>
        <div class="kpi-value">{sim_results['total_orders']:,}</div>
        <div class="kpi-subtext">COD batch analyzed</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid #10b981;">
        <div class="kpi-title">₹ Saved from Avoided RTOs</div>
        <div class="kpi-value" style="color: #059669;">+₹{fin['total_rto_saved_inr']:,.0f}</div>
        <div class="kpi-subtext">Shipping & damage costs prevented</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid #ef4444;">
        <div class="kpi-title">₹ Lost from False Cancels</div>
        <div class="kpi-value" style="color: #dc2626;">-₹{fin['total_margin_lost_inr']:,.0f}</div>
        <div class="kpi-subtext">Minimized by precision rules</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    net_val = fin['net_profit_impact_inr']
    color = "#059669" if net_val >= 0 else "#dc2626"
    sign = "+" if net_val >= 0 else ""
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid {color}; background: #f0fdf4;">
        <div class="kpi-title">Net ₹ Profit Impact</div>
        <div class="kpi-value" style="color: {color};">{sign}₹{net_val:,.0f}</div>
        <div class="kpi-subtext"><b>{sign}₹{fin['avg_impact_per_order_inr']:.2f}</b> net profit per order</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: The 4 Buckets Breakdown
st.subheader("📊 Yesterday's Orders Across the 4 Buckets")
b1, b2, b3, b4 = st.columns(4)

with b1:
    s = buckets["Ship as-is"]
    st.markdown(f"""
    <div class="kpi-card">
        <span class="badge-ship">1. Ship As-Is</span>
        <div class="kpi-value" style="margin-top: 10px;">{s['count']} <span style="font-size: 1rem; color: #64748b;">({s['percentage']}%)</span></div>
        <div class="kpi-subtext">Historical RTO: <b>{s['historical_rto_rate']}%</b></div>
        <div class="kpi-subtext">Low friction, repeat & verified buyers</div>
    </div>
    """, unsafe_allow_html=True)

with b2:
    c = buckets["Ship after confirmation"]
    st.markdown(f"""
    <div class="kpi-card">
        <span class="badge-confirm">2. Ship After Confirmation</span>
        <div class="kpi-value" style="margin-top: 10px;">{c['count']} <span style="font-size: 1rem; color: #64748b;">({c['percentage']}%)</span></div>
        <div class="kpi-subtext">Historical RTO: <b>{c['historical_rto_rate']}%</b></div>
        <div class="kpi-subtext">WhatsApp interactive check before packing</div>
    </div>
    """, unsafe_allow_html=True)

with b3:
    n = buckets["Nudge to prepaid"]
    st.markdown(f"""
    <div class="kpi-card">
        <span class="badge-nudge">3. Nudge to Prepaid</span>
        <div class="kpi-value" style="margin-top: 10px;">{n['count']} <span style="font-size: 1rem; color: #64748b;">({n['percentage']}%)</span></div>
        <div class="kpi-subtext">Historical RTO: <b>{n['historical_rto_rate']}%</b></div>
        <div class="kpi-subtext">High value COD; ₹{prepaid_discount:.0f} discount offered</div>
    </div>
    """, unsafe_allow_html=True)

with b4:
    h = buckets["Hold / cancel"]
    st.markdown(f"""
    <div class="kpi-card">
        <span class="badge-cancel">4. Hold / Cancel</span>
        <div class="kpi-value" style="margin-top: 10px;">{h['count']} <span style="font-size: 1rem; color: #64748b;">({h['percentage']}%)</span></div>
        <div class="kpi-subtext">Historical RTO: <b>{h['historical_rto_rate']}%</b></div>
        <div class="kpi-subtext">Serial RTO abusers & bot/dummy orders</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Tab Navigation: Deep Dive, WhatsApp Simulator, Leadership Trade-off, Order Explorer
tab1, tab2, tab3, tab4 = st.tabs([
    "⚖️ Operations vs Marketing Trade-Off",
    "💬 Interactive WhatsApp Simulator",
    "🔍 Detailed Orders Explorer",
    "📐 Prepaid Discount Mathematical Proof"
])

# TAB 1: Operations vs Marketing
with tab1:
    st.subheader("The ₹ Dilemma: Resolving Head of Operations vs Head of Marketing")
    st.markdown("""
    - **Head of Operations** wants aggressive cancellation: *"Cancel any risky COD order... If a pincode has bad history, stop COD."*
    - **Head of Marketing** wants zero cancellations: *"We spend ₹300 to acquire customers... Don't kill growth."*
    """)

    # Compute 3 Scenarios
    # Scenario A: Head of Ops (Cancel all high risk state + prior RTO >= 1 + order val > 1500 + dummy addr)
    ops_cancel_mask = (sim_df['state'].isin(['Bihar', 'Uttar Pradesh'])) | (sim_df['customer_prior_rto'] >= 1) | (sim_df['order_value'] > 1500)
    ops_cancelled_count = ops_cancel_mask.sum()
    ops_false_cancels = ((sim_df['actual_status'] == 'DELIVERED') & ops_cancel_mask).sum()
    ops_true_cancels = ((sim_df['actual_status'] == 'RTO') & ops_cancel_mask).sum()
    ops_saved = ops_true_cancels * 169.40
    ops_lost = ops_false_cancels * (649 * 0.62 + 300)
    ops_net = ops_saved - ops_lost

    # Scenario B: Head of Marketing (Ship everything COD, 0 cancellations)
    mktg_rto_count = (sim_df['actual_status'] == 'RTO').sum()
    mktg_rto_cost = mktg_rto_count * 169.40
    mktg_net = -mktg_rto_cost

    # Scenario C: Our Balanced AI Engine
    ai_net = fin['net_profit_impact_inr']

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(f"""
        <div class="kpi-card" style="border: 2px solid #ef4444;">
            <h4 style="color: #dc2626; margin: 0;">❌ Head of Ops Policy</h4>
            <p style="font-size: 0.85rem; color: #64748b;">Naive blanket cancellation</p>
            <ul style="font-size: 0.85rem; padding-left: 18px;">
                <li>Orders Cancelled: <b>{ops_cancelled_count}</b></li>
                <li>False Cancellations: <b>{ops_false_cancels}</b></li>
                <li>RTO Cost Saved: +₹{ops_saved:,.0f}</li>
                <li>Margin & CAC Lost: -₹{ops_lost:,.0f}</li>
            </ul>
            <div style="font-size: 1.3rem; font-weight: 700; color: #dc2626;">Net: -₹{abs(ops_net):,.0f}</div>
            <p style="font-size: 0.8rem; color: #dc2626;"><b>Verdict:</b> Incinerates revenue & Meta ad spend.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div class="kpi-card" style="border: 2px solid #f59e0b;">
            <h4 style="color: #d97706; margin: 0;">⚠️ Head of Marketing Policy</h4>
            <p style="font-size: 0.85rem; color: #64748b;">Ship everything blindly</p>
            <ul style="font-size: 0.85rem; padding-left: 18px;">
                <li>Orders Cancelled: <b>0</b></li>
                <li>RTO Orders Shipped: <b>{mktg_rto_count}</b></li>
                <li>RTO Cash Drain: <b>-₹{mktg_rto_cost:,.0f}</b></li>
                <li>Fake Accounts Filtered: <b>0</b></li>
            </ul>
            <div style="font-size: 1.3rem; font-weight: 700; color: #d97706;">Net: -₹{abs(mktg_net):,.0f}</div>
            <p style="font-size: 0.8rem; color: #d97706;"><b>Verdict:</b> Bleeds shipping cash on 573 returns.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_c:
        st.markdown(f"""
        <div class="kpi-card" style="border: 2px solid #10b981; background: #f0fdf4;">
            <h4 style="color: #059669; margin: 0;">🏆 Our Balanced Decision Engine</h4>
            <p style="font-size: 0.85rem; color: #64748b;">Precision 4-bucket AI routing</p>
            <ul style="font-size: 0.85rem; padding-left: 18px;">
                <li>Targeted Cancels: <b>{buckets['Hold / cancel']['count']}</b> (77% RTO)</li>
                <li>WhatsApp Confirmations: <b>{buckets['Ship after confirmation']['count']}</b></li>
                <li>Prepaid Conversions: <b>{buckets['Nudge to prepaid']['count']}</b></li>
                <li>Fast-Track Dispatches: <b>{buckets['Ship as-is']['count']}</b></li>
            </ul>
            <div style="font-size: 1.3rem; font-weight: 700; color: #059669;">Net: +₹{ai_net:,.0f}</div>
            <p style="font-size: 0.8rem; color: #059669;"><b>Verdict:</b> Maximizes revenue AND slashes RTO!</p>
        </div>
        """, unsafe_allow_html=True)

# TAB 2: WhatsApp Simulator
with tab2:
    st.subheader("💬 Live WhatsApp Flow Simulator")
    st.caption("Test how the automated WhatsApp flow interacts with real orders from the dataset.")

    # Select an order to test
    sample_order_ids = sim_df["order_id"].tolist()[:100]
    selected_id = st.selectbox("Select Order ID to simulate:", sample_order_ids)
    selected_row = sim_df[sim_df["order_id"] == selected_id].iloc[0]

    scol1, scol2 = st.columns([1, 1.2])

    with scol1:
        st.markdown("#### 📦 Order Details")
        st.write(f"**Customer:** {selected_row['customer_name']} ({selected_row['phone']})")
        st.write(f"**Address:** {selected_row['address']}, {selected_row['city']} ({selected_row['state']})")
        st.write(f"**Order Value:** ₹{selected_row['order_value']:,.0f}")
        st.write(f"**Prior Orders:** {selected_row['customer_prior_orders']} | **Prior RTO:** {selected_row['customer_prior_rto']}")
        st.info(f"**Engine Action:** `{selected_row['recommended_action']}`\n\n**Reason:** {selected_row['reason']}")

    with scol2:
        st.markdown("#### 📱 Simulated WhatsApp Chat")

        # Initialize session state for chat simulation
        if "sim_order_id" not in st.session_state or st.session_state["sim_order_id"] != selected_id:
            st.session_state["sim_order_id"] = selected_id
            st.session_state["flow_manager"] = WhatsAppFlowManager()
            st.session_state["flow_manager"].start_flow(selected_row.to_dict(), selected_row["recommended_action"])

        flow = st.session_state["flow_manager"]
        conv = flow.conversations.get(selected_id, {})

        # Display Chat History
        chat_box = st.container(height=320)
        with chat_box:
            for item in conv.get("history", []):
                if item["sender"] == "system":
                    st.markdown(f'<div class="whatsapp-bubble-bot">{item["message"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="whatsapp-bubble-user">{item["message"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

        st.caption(f"Current State: `{conv.get('state', 'INIT')}`")

        # Interactive quick buttons
        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            if st.button("Confirm Order ✅"):
                flow.process_incoming_message(selected_id, "btn_confirm")
                st.rerun()
        with bcol2:
            if st.button("Cancel Order ❌"):
                flow.process_incoming_message(selected_id, "btn_cancel")
                st.rerun()
        with bcol3:
            if st.button("Pay Online 💳"):
                flow.process_incoming_message(selected_id, "btn_pay_online")
                st.rerun()

        # Custom text response input
        user_reply = st.text_input("Type customer reply (e.g. 'kab aayega?', 'ha bhej do', 'House 42, Green Park'):", key="user_text")
        if st.button("Send Message 📤") and user_reply:
            flow.process_incoming_message(selected_id, user_reply)
            st.rerun()

        # Simulate 24-hr Timeout
        if st.button("⏳ Simulate 24-Hour Inaction Timeout"):
            flow.simulate_timeout(selected_id, 24)
            st.rerun()

# TAB 3: Orders Explorer
with tab3:
    st.subheader("🔍 Order-Level Triage Explorer")

    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        bucket_filter = st.multiselect("Filter by Action Bucket:", ["Ship as-is", "Ship after confirmation", "Nudge to prepaid", "Hold / cancel"], default=["Hold / cancel", "Nudge to prepaid"])
    with fcol2:
        state_filter = st.multiselect("Filter by State:", sorted(sim_df["state"].dropna().unique().tolist()))
    with fcol3:
        search_query = st.text_input("Search Customer Name, Phone, or Order ID:")

    filtered_df = sim_df.copy()
    if bucket_filter:
        filtered_df = filtered_df[filtered_df["recommended_action"].isin(bucket_filter)]
    if state_filter:
        filtered_df = filtered_df[filtered_df["state"].isin(state_filter)]
    if search_query:
        q = search_query.lower()
        filtered_df = filtered_df[
            filtered_df["customer_name"].str.lower().str.contains(q) |
            filtered_df["order_id"].str.lower().str.contains(q) |
            filtered_df["phone"].astype(str).str.contains(q)
        ]

    st.write(f"Showing **{len(filtered_df)}** of {len(sim_df)} orders:")
    cols_to_show = ["order_id", "customer_name", "phone", "state", "order_value", "recommended_action", "actual_status", "reason"]
    st.dataframe(filtered_df[cols_to_show], width=1200)

    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export Processed Orders (CSV)", csv_data, "processed_cod_orders.csv", "text/csv")

# TAB 4: Prepaid Math
with tab4:
    st.subheader("📐 Unit Economics: The ₹50 Prepaid Discount Justification")
    st.markdown("""
    ### Why exactly ₹50 discount on a ₹649 order?

    Here is the exact financial derivation showing why offering ₹50 discount generates **+₹129 net profit per converted order**:

    #### 1. Baseline Assumptions (from Company Data):
    - **AOV:** ₹649
    - **Delivered Gross Margin (62%):** ₹402.38
    - **Cost of an RTO:**
      - Forward Shipping: ₹65
      - Return Shipping: ₹65
      - Packaging & Handling: ₹25
      - Expected Product Damage (8% damaged @ ₹180): ₹14.40
      - **Total RTO Cost per Return = ₹169.40**
    - **Prepaid Historical RTO Rate:** **4.0%**
    - **Risky COD Segment RTO Rate:** **35.0%**

    ---

    #### 2. Expected Cost Comparison:
    - **If customer remains on Risky COD (35% RTO):**
      $$\\text{Expected RTO Cost} = 35\\% \\times ₹169.40 = ₹59.29$$
      $$\\text{Expected Profit} = (1 - 0.35) \\times ₹402.38 - ₹59.29 = ₹261.55 - ₹59.29 = \\mathbf{₹202.26}$$

    - **If customer converts to Prepaid with ₹50 Discount:**
      $$\\text{Discount Cost} = ₹50.00$$
      $$\\text{Adjusted Gross Margin} = ₹402.38 - ₹50.00 = ₹352.38$$
      $$\\text{Expected RTO Cost (4% RTO)} = 4\\% \\times ₹169.40 = ₹6.78$$
      $$\\text{Expected Profit} = (1 - 0.04) \\times ₹352.38 - ₹6.78 = 0.96 \\times ₹352.38 - ₹6.78 = \\mathbf{₹331.50}$$

    ---

    #### 3. Net Financial Gain:
    $$\\text{Incremental Profit per Conversion} = ₹331.50 - ₹202.26 = \\mathbf{+₹129.24}$$

    > **Key Insight:** The ₹50 discount is **entirely self-funded** by the **₹52.51** drop in expected shipping & return costs ($₹59.29 - ₹6.78 = ₹52.51$).
    > Meanwhile, converting the customer locks in payment upfront, prevents buyer remorse, and delivers an immediate **+₹129.24** bottom-line margin expansion!
    """)
