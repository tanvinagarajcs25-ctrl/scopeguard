"""ScopeGuard's three-panel Streamlit dashboard."""

import streamlit as st

import api


st.set_page_config(page_title="ScopeGuard", page_icon="🛡️", layout="wide")


def as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("messages", "items", "data", "results"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def money(value, currency="USD"):
    try:
        amount = float(value or 0)
    except (ValueError, TypeError):
        amount = 0
    return f"{currency} {amount:,.0f}"


if "messages" not in st.session_state:
    st.session_state.messages = api.get_messages(mock=True)
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None

with st.sidebar:
    st.title("🛡️ ScopeGuard")
    st.caption("Keep client work inside the lines.")
    memory_on = st.toggle("Memory", value=True, help="Use retained context and past decisions during analysis.")
    mode = st.radio("Connection", ["Mock", "Live"], horizontal=True)
    api_url = st.text_input("API URL", value=api.DEFAULT_API_URL, disabled=(mode == "Mock"))
    mock = mode == "Mock"
    if st.button("Load Data", use_container_width=True):
        result = api.load_data(mock=mock, api_url=api_url)
        if isinstance(result, dict) and result.get("error"):
            st.error(result["error"])
        else:
            st.session_state.messages = as_list(api.get_messages(mock=mock, api_url=api_url))
            st.session_state.analysis = None
            st.success(result.get("message", "Data loaded.") if isinstance(result, dict) else "Data loaded.")
    if st.button("Reset", use_container_width=True):
        result = api.reset(mock=mock, api_url=api_url)
        st.session_state.messages = as_list(api.get_messages(mock=mock, api_url=api_url))
        st.session_state.analysis = None
        st.session_state.selected_id = None
        if isinstance(result, dict) and result.get("error"):
            st.error(result["error"])
        else:
            st.success(result.get("message", "Reset complete.") if isinstance(result, dict) else "Reset complete.")

st.title("Client inbox")
ledger_result = api.get_ledger(mock=mock, api_url=api_url)
if isinstance(ledger_result, dict) and ledger_result.get("error"):
    st.warning(ledger_result["error"])
    ledger_result = {}
currency = ledger_result.get("currency", "USD") if isinstance(ledger_result, dict) else "USD"
left_metric, right_metric, status_metric = st.columns([1, 1, 2])
left_metric.metric("Unpaid extra asks", ledger_result.get("unpaid_extra_asks", 0) if isinstance(ledger_result, dict) else 0)
right_metric.metric("Total value", money(ledger_result.get("total_value", 0), currency) if isinstance(ledger_result, dict) else money(0, currency))
status_metric.caption("Tracked from client requests reviewed by ScopeGuard")
st.divider()

inbox, analyzer, memory_panel = st.columns([1.1, 1.6, 1.3], gap="large")

with inbox:
    st.subheader("Inbox")
    messages = as_list(st.session_state.messages)
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
            with st.spinner("Analyzing request…"):
                st.session_state.analysis = api.analyze(item, memory=memory_on, mock=mock, api_url=api_url)
            st.rerun()
        st.caption(item.get("received", item.get("date", "")))

with analyzer:
    st.subheader("Analyzer")
    selected = next((m for i, m in enumerate(messages) if isinstance(m, dict) and str(m.get("id", m.get("message_id", i))) == str(st.session_state.selected_id)), None)
    if selected:
        st.markdown(f"**{selected.get('subject', selected.get('title', 'Selected request'))}**")
        st.write(selected.get("body", selected.get("text", selected.get("preview", ""))))
        if st.button("Analyze request", type="primary", use_container_width=True):
            with st.spinner("Comparing request with the agreement…"):
                st.session_state.analysis = api.analyze(selected, memory=memory_on, mock=mock, api_url=api_url)
    else:
        st.info("Choose a message from the inbox to review it.")
    result = st.session_state.analysis
    if isinstance(result, dict) and result.get("error"):
        st.error(result["error"])
    elif isinstance(result, dict):
        verdict = str(result.get("verdict", "REVIEW")).upper()
        colors = {"OUT_OF_SCOPE": ("#fff0ed", "#a83220"), "OUT OF SCOPE": ("#fff0ed", "#a83220"), "IN_SCOPE": ("#eaf7ef", "#216e39"), "IN SCOPE": ("#eaf7ef", "#216e39"), "UNCERTAIN": ("#fff7e6", "#8a5a00")}
        bg, fg = colors.get(verdict, ("#eef2ff", "#334155"))
        label = result.get("title", verdict.replace("_", " ").title())
        st.markdown(f"<div style='background:{bg};border-left:5px solid {fg};padding:16px;border-radius:8px;color:{fg}'><strong>{label}</strong><br>{result.get('summary', '')}</div>", unsafe_allow_html=True)
        st.caption(f"Confidence: {float(result.get('confidence', 0)):.0%}" if isinstance(result.get("confidence"), (int, float)) else "")
        if result.get("reason"):
            st.write(result["reason"])
        if result.get("sow_reference"):
            st.caption(f"Agreement: {result['sow_reference']}")
        if result.get("memory_note"):
            st.info(result["memory_note"])
        value = result.get("estimated_value", 0)
        hours = result.get("estimated_hours")
        st.write(f"**Suggested charge:** {money(value, result.get('currency', currency))}" + (f" · {hours:g} hours" if isinstance(hours, (int, float)) else ""))
        if result.get("suggested_reply"):
            with st.expander("Suggested reply"):
                st.write(result["suggested_reply"])
        b1, b2, b3 = st.columns(3)
        message_id = str(selected.get("id", selected.get("message_id", ""))) if selected else ""
        if b1.button("Charge", key="charge", use_container_width=True):
            feedback = api.send_feedback(message_id, "charge", result, mock=mock, api_url=api_url)
            st.success(feedback.get("message", "Decision saved.")) if not feedback.get("error") else st.error(feedback["error"])
        if b2.button("Waive", key="waive", use_container_width=True):
            feedback = api.send_feedback(message_id, "waive", result, mock=mock, api_url=api_url)
            st.success(feedback.get("message", "Decision saved.")) if not feedback.get("error") else st.error(feedback["error"])
        if b3.button("Edit", key="edit", use_container_width=True):
            st.session_state.editing_reply = result.get("suggested_reply", "")
        if "editing_reply" in st.session_state:
            edited = st.text_area("Edit suggested reply", value=st.session_state.editing_reply, key="reply_editor")
            if st.button("Save edited reply"):
                st.session_state.editing_reply = edited
                st.success("Reply updated.")

with memory_panel:
    st.subheader("Memory Panel")
    reflect = api.get_reflect(mock=mock, api_url=api_url)
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
