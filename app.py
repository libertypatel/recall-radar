import streamlit as st
from extract import extract_listing
from pipeline import check_details, merge_details

st.set_page_config(page_title="Recall Radar", page_icon="🔎")

RESULT_STYLE = {
    "match_supported": ("error", "Recall match supported"),
    "info_needed": ("warning", "Possible match: information needed"),
    "outside_scope": ("info", "Outside this recall's scope"),
}


def show_report(report):
    """Display the overall summary and one card per recall notice."""
    if report.get("error"):
        st.error(report["summary"])
        st.caption(report["error"])
        return

    st.subheader(report["summary"])
    st.caption("Results describe recall evidence only, never general product safety.")
    st.caption("Source: " + report.get("source", ""))

    for r in report["results"]:
        kind, label = RESULT_STYLE[r["result"]]
        with st.container(border=True):
            getattr(st, kind)(label)
            st.markdown(f"**[{r['title']}]({r['url']})**")
            for reason in r["reasons"]:
                st.write("- " + reason)
            if r["questions"]:
                st.markdown("**Ask the seller:**")
                for q in r["questions"]:
                    st.code(q, language=None, wrap_lines=True)
            with st.expander("Evidence from the recall notice"):
                for key in ["affected_models", "dates", "identification", "remedy"]:
                    for item in r["scope"].get(key, []):
                        mark = "Verified" if item.get("supported") else "Not verified"
                        st.markdown(f"*{key.replace('_', ' ').title()}* ({mark}): \"{item.get('quote')}\"")


st.title("Recall Radar")
st.write("Before you buy used, find relevant recall evidence and learn exactly what to ask the seller.")

listing = st.text_area("Paste the listing text", height=120,
                       placeholder="Example: Voomf crib mattress, white with balloon print, fits pack n play. $15.")

if st.button("Check for recalls", type="primary") and listing.strip():
    with st.spinner("Reading the listing and checking CPSC recall notices..."):
        details = extract_listing(listing)
        st.session_state.report = check_details(details)
        st.session_state.conflicts = []

if "report" in st.session_state:
    report = st.session_state.report
    with st.expander("Details read from the listing"):
        st.json(report["details"])
    show_report(report)

    if any(r["result"] == "info_needed" for r in report.get("results", [])):
        st.divider()
        st.markdown("### Got a reply from the seller?")
        reply = st.text_area("Paste the seller's reply", height=100)
        if st.button("Update the result") and reply.strip():
            with st.spinner("Reading the reply and rechecking..."):
                merged, conflicts = merge_details(report["details"], extract_listing(reply))
                st.session_state.conflicts = conflicts
                if not conflicts:
                    st.session_state.report = check_details(merged)
                    st.rerun()

    for c in st.session_state.get("conflicts", []):
        st.warning(f"The listing says {c['field'].replace('_', ' ')} **{c['listing']}**, "
                   f"but the seller's reply says **{c['reply']}**. Please confirm with the seller "
                   "before relying on either. The result above still uses the listing's value.")