"""ScopeGuard dashboard for reviewing Sharma Retail app requests."""

import streamlit as st

import api


RATE_INR_PER_HOUR = 1500
VERDICT_STYLE = {
    "in_scope": ("#eaf7ef", "#216e39", "In scope"),
    "out_of_scope": ("#fff0ed", "#a83220", "Out of scope"),
    "grey_area": ("#fff7e6", "#8a5a00", "Grey area"),
}

st.set_page_config(page_title="ScopeGuard", page_icon="🛡️", layout="wide")


def as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("messages", "items", "data", "results"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def money_inr(value):
    try:
        amount = float(value or 0)
    except (ValueError, TypeError):
        amount = 0
    return f"₹{amount:,.0f}"


def refresh_review_data(mock, api_url):
    st.session_state.ledger = api.get_ledger(mock=mock, api_url=api_url)
    st.session_state.reflect = api.get_reflect(mock=mock, api_url=api_url)


if "messages" not in st.session_state:
    st.session_state.messages = api.get_messages(mock=True)
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None

with st.sidebar:
    st.title("🛡️ ScopeGuard")
    st.caption("Sharma Retail · E-commerce mobile app")
    memory_on = st.toggle("Memory", value=True, help="Use retained context and past decisions during analysis.")
    mode = st.radio("Connection", ["Mock", "Live"], horizontal=True)
    mock = mode == "Mock"
    api_url = st.text_input("API URL", value=api.DEFAULT_API_URL, disabled=mock)
    health = api.health(mock=mock, api_url=api_url)
    if isinstance(health, dict) and not health.get("error"):
        st.caption("API status: Connected" if health.get("status") in ("ok", "healthy") else f"API status: {health.get('status', 'Available')}")
    else:
        st.caption("API status: Unavailable" if not mock else "API status: Mock mode")
    if st.button("Load Data", use_container_width=True):
        loaded = api.load_data(mock=mock, api_url=api_url)
        if isinstance(loaded, dict) and loaded.get("error"):
            st.error(loaded["error"])
        else:
            fetched = api.get_messages(mock=mock, api_url=api_url)
            if isinstance(fetched, dict) and fetched.get("error"):
                st.error(fetched["error"])
            else:
                st.session_state.messages = as_list(fetched)
                st.session_state.analysis = None
                refresh_review_data(mock, api_url)
                st.success(loaded.get("message", "Data loaded.") if isinstance(loaded, dict) else "Data loaded.")
    if st.button("Reset", use_container_width=True):
        reset_result = api.reset(mock=mock, api_url=api_url)
        st.session_state.analysis = None
        st.session_state.selected_id = None
        st.session_state.messages = as_list(api.get_messages(mock=mock, api_url=api_url))
        refresh_review_data(mock, api_url)
        if isinstance(reset_result, dict) and reset_result.get("error"):
            st.error(reset_result["error"])
        else:
            st.success(reset_result.get("message", "Reset complete.") if isinstance(reset_result, dict) else "Reset complete.")

st.title("Client inbox")
if "ledger" not in st.session_state or mock:
    st.session_state.ledger = api.get_ledger(mock=mock, api_url=api_url)
if "reflect" not in st.session_state or mock:
    st.session_state.reflect = api.get_reflect(mock=mock, api_url=api_url)
ledger = st.session_state.ledger
if isinstance(ledger, dict) and ledger.get("error"):
    st.warning(ledger["error"])
    ledger = {}
ledger_total = ledger.get("total_value_inr", ledger.get("total_value", 0)) if isinstance(ledger, dict) else 0
m1, m2, m3 = st.columns([1, 1, 2])
m1.metric("Unpaid extra asks", ledger.get("unpaid_extra_asks", 0) if isinstance(ledger, dict) else 0)
m2.metric("Total value", money_inr(ledger_total))
m3.caption(f"Extra work rate · {money_inr(RATE_INR_PER_HOUR)}/hr")
st.divider()

inbox, analyzer, memory_panel = st.columns([1.1, 1.6, 1.3], gap="large")
messages = as_list(st.session_state.messages)

with inbox:
    st.subheader("Inbox")
    if not messages:
        st.info("No messages loaded yet. Use Load Data to fetch inbox messages.")
    for index, item in enumerate(messages):
        if not isinstance(item, dict):
            continue
        message_id = str(item.get("id", item.get("message_id", index)))
        title = item.get("subject", item.get("title", item.get("client", f"Message {index + 1}")))
        sender = item.get("sender", item.get("client", "Client"))
        preview = item.get("preview", item.get("body", item.get("text", "")))
        if st.button(f"**{sender}** · {title}\n\n{preview}", key=f"message_{message_id}", use_container_width=True):
            st.session_state.selected_id = message_id
            with st.spinner("Comparing request with the SOW…"):
                st.session_state.analysis = api.analyze(
                    message_id, item.get("body", item.get("text", preview)), memory_on,
                    mock=mock, api_url=api_url,
                )
            st.rerun()
        st.caption(item.get("received", item.get("date", "")))

with analyzer:
    st.subheader("Analyzer")
    selected = next((m for i, m in enumerate(messages) if isinstance(m, dict) and str(m.get("id", m.get("message_id", i))) == str(st.session_state.selected_id)), None)
    if selected:
        selected_text = selected.get("body", selected.get("text", selected.get("preview", "")))
        st.markdown(f"**{selected.get('subject', selected.get('title', 'Selected request'))}**")
        st.write(selected_text)
        if st.button("Analyze request", type="primary", use_container_width=True):
            with st.spinner("Comparing request with the SOW…"):
                st.session_state.analysis = api.analyze(
                    str(selected.get("id", selected.get("message_id", ""))), selected_text, memory_on,
                    mock=mock, api_url=api_url,
                )
    else:
        st.info("Choose a message from the inbox to review it.")

    result = st.session_state.analysis
    if isinstance(result, dict) and result.get("error"):
        st.error(result["error"])
    elif isinstance(result, dict):
        verdict = str(result.get("verdict", "grey_area")).lower()
        bg, fg, verdict_label = VERDICT_STYLE.get(verdict, VERDICT_STYLE["grey_area"])
        st.markdown(
            f"<div style='background:{bg};border-left:5px solid {fg};padding:16px;border-radius:8px;color:{fg}'>"
            f"<strong>{verdict_label}</strong><br>{result.get('reasoning', '')}</div>",
            unsafe_allow_html=True,
        )
        clauses = result.get("sow_clause_ids", [])
        if clauses:
            st.caption("SOW clauses: " + ", ".join(str(clause) for clause in clauses))
        hours = result.get("estimated_hours", 0) or 0
        cost = result.get("estimated_cost_inr", float(hours) * RATE_INR_PER_HOUR) or 0
        st.write(f"**Estimate:** {hours:g} hours · {money_inr(cost)}")
        if result.get("recalled_memories"):
            st.markdown("**Recalled memories**")
            for memory in result["recalled_memories"] if isinstance(result["recalled_memories"], list) else [result["recalled_memories"]]:
                st.write(f"• {memory}")
        if result.get("evidence"):
            with st.expander("Evidence"):
                for evidence in result["evidence"] if isinstance(result["evidence"], list) else [result["evidence"]]:
                    st.write(f"• {evidence}")
        st.caption("Scope creep detected" if result.get("creep") is True else "No scope creep detected" if result.get("creep") is False else "Scope creep assessment is uncertain")
        note = st.text_input("Decision note", key="feedback_note")
        b1, b2, b3 = st.columns(3)
        selected_id = str(selected.get("id", selected.get("message_id", ""))) if selected else ""
        for button, decision in ((b1, "charge"), (b2, "waive")):
            label = "Charge" if decision == "charge" else "Waive"
            if button.button(label, key=f"{decision}_button", use_container_width=True):
                response = api.feedback(
                    selected_id, selected_text if selected else "", verdict, float(hours), float(cost), decision, note,
                    mock=mock, api_url=api_url,
                )
                if isinstance(response, dict) and response.get("error"):
                    st.error(response["error"])
                else:
                    refresh_review_data(mock, api_url)
                    st.success(response.get("message", "Decision saved.") if isinstance(response, dict) else "Decision saved.")
                    st.rerun()
        if b3.button("Edit", key="edit_button", use_container_width=True):
            st.session_state.editing_note = note
        if result.get("error"):
            st.error(str(result["error"]))

with memory_panel:
    st.subheader("Memory Panel")
    reflect = st.session_state.reflect
    if isinstance(reflect, dict) and reflect.get("error"):
        st.error(reflect["error"])
    else:
        tabs = st.tabs(["Retained", "Recalled", "Learned"])
        for tab, key in zip(tabs, ("retained", "recalled", "learned")):
            with tab:
                entries = reflect.get(key, []) if isinstance(reflect, dict) else []
                if not entries:
                    st.caption("Nothing here yet.")
                for entry in entries if isinstance(entries, list) else []:
                    if isinstance(entry, dict):
                        st.markdown(f"**{entry.get('source', key.title())}** · {entry.get('date', '')}")
                        st.write(entry.get("text", entry.get("content", str(entry))))
                    else:
                        st.write(entry)
                    st.divider()
