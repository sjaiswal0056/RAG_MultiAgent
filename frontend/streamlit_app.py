from __future__ import annotations

import json
import os
from pathlib import Path

import requests
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Policy-Aware Claim Engine", page_icon="🛡️", layout="wide")
st.title("Policy-Aware Claim Decision Engine")
st.caption("Prototype decision support. Policy evidence is authoritative; unsupported claims abstain.")

cases = json.loads((ROOT / "candidate_data" / "public_test_cases.json").read_text(encoding="utf-8"))
mode = st.radio("Claim input", ["Public case", "Upload JSON", "Paste JSON"], horizontal=True)
payload = None
if mode == "Public case":
    selected = st.selectbox("Case", [item["case_id"] for item in cases])
    payload = next(item for item in cases if item["case_id"] == selected)
elif mode == "Upload JSON":
    upload = st.file_uploader("Upload one claim case", type=["json"])
    if upload:
        payload = json.load(upload)
else:
    raw = st.text_area("Paste one claim case as JSON", height=280)
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")

if payload:
    with st.expander("Input", expanded=False):
        st.json(payload)
    if st.button("Analyze claim", type="primary"):
        try:
            response = requests.post(f"{API_BASE_URL}/analyze", json=payload, timeout=120)
            if response.status_code >= 400:
                st.error(f"API rejected the request ({response.status_code}): {response.text}")
            else:
                result = response.json()
                if result["decision"] == "NEEDS_REVIEW":
                    st.warning(f"{result['decision']} - {result.get('reason_code', 'INSUFFICIENT_EVIDENCE')}")
                elif result["decision"] == "NOT_ADMISSIBLE":
                    st.error(result["decision"])
                else:
                    st.success(result["decision"])
                a, b, c = st.columns(3)
                a.metric("Confidence", f"{result['confidence']:.0%}")
                b.metric("Estimated payable", "Not calculated" if result["estimated_payable_inr"] is None else f"INR {result['estimated_payable_inr']:,.0f}")
                c.metric("Validation", result["validation"]["status"])
                st.subheader("Key findings")
                for finding in result["key_findings"]:
                    st.markdown(f"- **{finding['dimension'].replace('_', ' ').title()}** ({finding['status']}): {finding['finding']}")
                st.subheader("Limits and deductions")
                st.json({"applicable_limits": result["applicable_limits"], "deductions": result["deductions"]})
                st.subheader("Missing evidence")
                st.write(result["missing_evidence"] or "None identified")
                st.subheader("Policy citations")
                for citation in result["citations"]:
                    with st.expander(f"Page {citation['page']} - {citation['section']} - {citation['chunk_id']}"):
                        st.write(citation["claim"])
                        st.caption(citation["excerpt"])
                with st.expander("Execution trace"):
                    st.dataframe(result["trace"], use_container_width=True)
                with st.expander("Validation details"):
                    st.json(result["validation"])
        except requests.RequestException as exc:
            st.error(f"Backend connection failed: {exc}. Check API_BASE_URL and backend health.")
