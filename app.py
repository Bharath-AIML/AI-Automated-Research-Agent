# =============================================================================
# app.py — AI Research Assistant | B2B Enterprise UI
# =============================================================================
# Design system: Black (#0a0a0a) + White (#f5f5f5) + Gold (#C9A84C)
# Typography: Space Grotesk — clean, modern, professional
# No emojis. No gradients. No decorations. Just clarity.

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from agents.controller import Controller
from utils.helpers import (
    format_paper_meta, score_to_color, verdict_emoji,
    compute_summary_stats, load_session
)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Intelligence Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design System ─────────────────────────────────────────────────────────────
GOLD   = "#C9A84C"
BLACK  = "#0a0a0a"
WHITE  = "#f5f5f5"
GREY1  = "#1a1a1a"   # card background
GREY2  = "#2a2a2a"   # border / divider
GREY3  = "#6b6b6b"   # muted text
GREY4  = "#3a3a3a"   # subtle border

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

*, html, body, [class*="css"] {{
    font-family: 'Space Grotesk', sans-serif !important;
}}

/* ── Global background ── */
.stApp {{
    background-color: {BLACK};
    color: {WHITE};
}}

/* ── Remove Streamlit default padding ── */
.block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {GREY1};
    border-right: 1px solid {GREY2};
}}
section[data-testid="stSidebar"] * {{
    color: {WHITE} !important;
}}

/* ── Inputs & selects ── */
.stTextInput input,
.stSelectbox select,
div[data-baseweb="select"] * {{
    background-color: {GREY1} !important;
    color: {WHITE} !important;
    border: 1px solid {GREY2} !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
div[data-baseweb="select"] svg {{ fill: {GREY3} !important; }}

/* ── Slider ── */
.stSlider [data-testid="stThumbValue"] {{ color: {GOLD} !important; }}
.stSlider [role="slider"] {{ background-color: {GOLD} !important; }}

/* ── Primary button ── */
.stButton > button[kind="primary"] {{
    background-color: {GOLD} !important;
    color: {BLACK} !important;
    border: none !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em;
    border-radius: 4px !important;
    padding: 0.55rem 1.2rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: opacity 0.15s ease;
}}
.stButton > button[kind="primary"]:hover {{ opacity: 0.85 !important; }}

/* ── Secondary button ── */
.stButton > button:not([kind="primary"]) {{
    background-color: transparent !important;
    color: {WHITE} !important;
    border: 1px solid {GREY2} !important;
    border-radius: 4px !important;
}}

/* ── Tab bar ── */
.stTabs [data-baseweb="tab-list"] {{
    background: transparent !important;
    border-bottom: 1px solid {GREY2} !important;
    gap: 0;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {GREY3} !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.4rem !important;
    border-bottom: 2px solid transparent !important;
}}
.stTabs [aria-selected="true"] {{
    color: {GOLD} !important;
    border-bottom: 2px solid {GOLD} !important;
}}

/* ── Metrics ── */
[data-testid="stMetric"] {{
    background-color: {GREY1} !important;
    border: 1px solid {GREY2} !important;
    border-radius: 4px !important;
    padding: 1rem !important;
}}
[data-testid="stMetric"] label {{ color: {GREY3} !important; font-size: 0.75rem !important; letter-spacing: 0.06em !important; text-transform: uppercase !important; }}
[data-testid="stMetricValue"] {{ color: {WHITE} !important; font-weight: 600 !important; }}

/* ── Expander ── */
.streamlit-expanderHeader {{
    background-color: {GREY1} !important;
    border: 1px solid {GREY2} !important;
    border-radius: 4px !important;
    color: {WHITE} !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}}
.streamlit-expanderContent {{
    background-color: {GREY1} !important;
    border: 1px solid {GREY2} !important;
    border-top: none !important;
}}

/* ── Alerts / info ── */
.stInfo    {{ background-color: {GREY1} !important; border-color: {GREY2} !important; color: {WHITE} !important; }}
.stWarning {{ background-color: {GREY1} !important; border-color: {GOLD}  !important; color: {WHITE} !important; }}
.stSuccess {{ background-color: {GREY1} !important; border-color: {GOLD}  !important; color: {WHITE} !important; }}
.stError   {{ background-color: {GREY1} !important; border-color: #ff4444 !important; color: {WHITE} !important; }}

/* ── Progress bar ── */
.stProgress > div > div {{ background-color: {GOLD} !important; }}

/* ── Caption / small text ── */
.stCaption {{ color: {GREY3} !important; }}

/* ── Plotly modal fix ── */
.js-plotly-plot .plotly .modebar {{ background: {GREY1} !important; }}

/* ── Multiselect ── */
span[data-baseweb="tag"] {{
    background-color: {GREY2} !important;
    color: {WHITE} !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Reusable HTML Components ──────────────────────────────────────────────────

def page_header(title: str, subtitle: str = ""):
    sub = f'<p style="color:{GREY3};font-size:0.85rem;letter-spacing:0.04em;margin:0.3rem 0 0 0;">{subtitle}</p>' if subtitle else ""
    return f"""
<div style="padding:0 0 1.5rem 0; border-bottom:1px solid {GREY2}; margin-bottom:1.5rem;">
    <h1 style="color:{GOLD};font-size:1.6rem;font-weight:700;letter-spacing:-0.02em;margin:0;">
        {title}
    </h1>
    {sub}
</div>"""

def section_label(text: str):
    return f'<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin:1.5rem 0 0.6rem 0;">{text}</p>'

def score_chip(score: float) -> str:
    if score >= 8:   color = "#22c55e"
    elif score >= 5: color = GOLD
    elif score >= 3: color = "#f97316"
    else:            color = "#ef4444"
    return (f'<span style="display:inline-block;background:{color}20;border:1px solid {color};'
            f'color:{color};font-size:0.78rem;font-weight:600;letter-spacing:0.04em;'
            f'padding:0.15rem 0.6rem;border-radius:2px;">{score}/10</span>')

def verdict_chip(verdict: str) -> str:
    v = verdict.lower()
    if "accept"  in v: color, label = "#22c55e", "ACCEPT"
    elif "minor" in v: color, label = GOLD,      "MINOR REVISION"
    elif "major" in v: color, label = "#f97316", "MAJOR REVISION"
    else:              color, label = "#ef4444",  "REJECT"
    return (f'<span style="display:inline-block;background:{color}18;border:1px solid {color};'
            f'color:{color};font-size:0.72rem;font-weight:600;letter-spacing:0.08em;'
            f'padding:0.2rem 0.7rem;border-radius:2px;">{label}</span>')

def cat_badge(label: str) -> str:
    colors = {"Claim": "#60a5fa", "Method": "#34d399", "Result": GOLD, "Limitation": "#f87171"}
    c = colors.get(label, GREY3)
    return (f'<span style="display:inline-block;background:{c}18;border:1px solid {c}20;'
            f'color:{c};font-size:0.7rem;font-weight:600;letter-spacing:0.08em;'
            f'padding:0.1rem 0.5rem;border-radius:2px;">{label.upper()}</span>')

def card_start(padding="1.2rem 1.4rem"):
    return f'<div style="background:{GREY1};border:1px solid {GREY2};border-radius:4px;padding:{padding};margin-bottom:0.8rem;">'

def card_end():
    return "</div>"

def divider():
    return f'<hr style="border:none;border-top:1px solid {GREY2};margin:1.2rem 0;"/>'


# ── Session State ─────────────────────────────────────────────────────────────
if "results"    not in st.session_state: st.session_state.results    = []
if "query"      not in st.session_state: st.session_state.query      = ""
if "controller" not in st.session_state: st.session_state.controller = None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:1.2rem 0 1.5rem 0; border-bottom:1px solid {GREY2}; margin-bottom:1.2rem;">
        <p style="color:{GOLD};font-size:0.7rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;margin:0 0 0.3rem 0;">Research Intelligence</p>
        <p style="color:{WHITE};font-size:1.15rem;font-weight:700;margin:0;">Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;">Query</p>', unsafe_allow_html=True)
    query = st.text_input(
        "query", label_visibility="collapsed",
        placeholder="e.g. transformer attention mechanism",
    )

    st.markdown(f'<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin:1rem 0 0.4rem 0;">Max Papers</p>', unsafe_allow_html=True)
    max_papers = st.slider("max_papers", 1, 10, 4, label_visibility="collapsed")

    st.markdown(f'<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin:1rem 0 0.4rem 0;">Classifier Mode</p>', unsafe_allow_html=True)
    classifier_mode = st.selectbox(
        "classifier_mode", label_visibility="collapsed",
        options=["keyword", "hybrid", "transformer"],
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    search_btn = st.button("Run Analysis", type="primary", use_container_width=True)

    if st.session_state.results:
        stats = compute_summary_stats(st.session_state.results)
        st.markdown(f'{divider()}<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.8rem;">Session</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Papers", stats.get("num_papers", 0))
        c2.metric("Avg Score", f"{stats.get('avg_score', 0)}")

    st.markdown(f"""
    {divider()}
    <p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.8rem;">Sources</p>
    <p style="color:{GREY3};font-size:0.8rem;line-height:1.6;margin:0;">arXiv API<br/>Semantic Scholar API</p>
    """, unsafe_allow_html=True)


# ── Pipeline Execution ────────────────────────────────────────────────────────
if search_btn and query.strip():
    st.session_state.query = query.strip()

    with st.spinner("Initialising agents..."):
        if (st.session_state.controller is None
                or getattr(st.session_state.controller.classifier, "mode", None) != classifier_mode):
            st.session_state.controller = Controller(classifier_mode=classifier_mode)

    progress = st.progress(0, text="Fetching papers...")

    try:
        ctrl       = st.session_state.controller
        papers_raw = ctrl.research_agent.fetch_papers(query.strip())
        progress.progress(20, text="Running NLP pipeline...")

        results = []
        total   = min(len(papers_raw), max_papers)

        if total == 0:
            st.warning("No papers found. Try a different query.")
            progress.empty()
        else:
            for idx, paper in enumerate(papers_raw[:total]):
                if not paper.get("abstract"):
                    continue
                pct = 20 + int(70 * (idx + 1) / total)
                progress.progress(pct, text=f"Analysing paper {idx+1} of {total}...")

                paper      = ctrl.preprocessor.preprocess_paper(paper)
                classified = ctrl.classifier.classify_sentences(paper.get("sentences", []))
                defence    = ctrl.defender.defend(paper, classified)
                critique   = ctrl.critic.critique(paper, classified)
                verdict    = ctrl.judge.judge(paper, defence, critique, classified)

                results.append({
                    "paper":      {k: paper[k] for k in ("title","authors","abstract","year","source","url") if k in paper},
                    "classified": classified,
                    "defence":    defence,
                    "critique":   critique,
                    "verdict":    verdict,
                })

            progress.progress(100, text="Complete")
            import time as _t; _t.sleep(0.4)
            progress.empty()

            st.session_state.results = results
            st.success(f"Analysis complete — {len(results)} papers processed.")

    except Exception as e:
        progress.empty()
        st.error(f"Pipeline error: {e}")
        st.exception(e)

elif search_btn:
    st.warning("Enter a query to begin.")


# ── Main Tabs ─────────────────────────────────────────────────────────────────
results = st.session_state.results

if results:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "PAPERS", "CLASSIFICATION", "DEBATE", "DASHBOARD", "HISTORY"
    ])

    # ── TAB 1: Papers ─────────────────────────────────────────────────────────
    with tab1:
        st.markdown(page_header("Papers", f"Query: {st.session_state.query}"), unsafe_allow_html=True)

        for i, r in enumerate(results):
            meta  = format_paper_meta(r["paper"])
            score = r["verdict"]["score"]
            verdict_str = r["verdict"]["verdict"]

            st.markdown(card_start(), unsafe_allow_html=True)
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.6rem;">
                <span style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">
                    {i+1:02d} &nbsp;·&nbsp; {meta['source']} &nbsp;·&nbsp; {meta['year']}
                </span>
                <div style="display:flex;gap:0.5rem;">
                    {score_chip(score)}
                    {verdict_chip(verdict_str)}
                </div>
            </div>
            <p style="color:{WHITE};font-size:1rem;font-weight:600;margin:0 0 0.4rem 0;line-height:1.4;">{meta['title']}</p>
            <p style="color:{GREY3};font-size:0.8rem;margin:0 0 0.8rem 0;">{meta['authors']}</p>
            <p style="color:#c0c0c0;font-size:0.85rem;line-height:1.65;margin:0;">{meta['abstract']}</p>
            """, unsafe_allow_html=True)

            if meta["url"]:
                st.markdown(
                    f'<a href="{meta["url"]}" target="_blank" '
                    f'style="color:{GOLD};font-size:0.8rem;text-decoration:none;'
                    f'letter-spacing:0.04em;font-weight:500;">View Paper &rarr;</a>',
                    unsafe_allow_html=True,
                )
            st.markdown(card_end(), unsafe_allow_html=True)

    # ── TAB 2: Classification ─────────────────────────────────────────────────
    with tab2:
        st.markdown(page_header("Sentence Classification", "NLP pipeline output — each sentence labelled by category"), unsafe_allow_html=True)

        paper_names  = [f"{i+1:02d}  {r['paper']['title'][:65]}..." for i, r in enumerate(results)]
        sel_idx      = st.selectbox("Select paper", range(len(results)), format_func=lambda i: paper_names[i])
        selected     = results[sel_idx]
        classified   = selected["classified"]

        cat_counts = {c: 0 for c in config.SENTENCE_CATEGORIES}
        for c in classified:
            if c["label"] in cat_counts:
                cat_counts[c["label"]] += 1

        st.markdown("<br/>", unsafe_allow_html=True)
        cols = st.columns(4)
        for col, (cat, cnt) in zip(cols, cat_counts.items()):
            col.metric(cat, cnt)

        st.markdown(section_label("Sentence Breakdown"), unsafe_allow_html=True)

        cat_filter = st.multiselect(
            "Filter categories", options=config.SENTENCE_CATEGORIES,
            default=config.SENTENCE_CATEGORIES, label_visibility="collapsed"
        )

        cat_colors = {"Claim": "#60a5fa", "Method": "#34d399", "Result": GOLD, "Limitation": "#f87171"}

        for item in classified:
            if item["label"] not in cat_filter:
                continue
            c  = cat_colors.get(item["label"], GREY3)
            st.markdown(f"""
<div style="background:{GREY1};border:1px solid {GREY2};border-left:3px solid {c};
            border-radius:4px;padding:0.6rem 0.9rem;margin-bottom:0.4rem;">
    <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
        {cat_badge(item['label'])}
        <span style="color:{GREY3};font-size:0.72rem;">confidence {item['confidence']:.0%}</span>
    </div>
    <p style="color:#c8c8c8;font-size:0.85rem;margin:0;line-height:1.55;">{item['sentence']}</p>
</div>
""", unsafe_allow_html=True)

        try:
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Bar(
                x=list(cat_counts.keys()),
                y=list(cat_counts.values()),
                marker_color=[cat_colors[c] for c in cat_counts],
                marker_line_width=0,
                text=list(cat_counts.values()),
                textposition="outside",
                textfont=dict(color=WHITE, size=12),
            )])
            fig.update_layout(
                title=dict(text="Category Distribution", font=dict(color=GOLD, size=13, family="Space Grotesk"), x=0),
                plot_bgcolor=GREY1, paper_bgcolor=GREY1,
                font=dict(color=WHITE, family="Space Grotesk"),
                xaxis=dict(showgrid=False, color=GREY3),
                yaxis=dict(showgrid=True, gridcolor=GREY2, color=GREY3),
                margin=dict(l=0, r=0, t=40, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

    # ── TAB 3: Debate ─────────────────────────────────────────────────────────
    with tab3:
        st.markdown(page_header("Multi-Agent Debate", "Defender vs Critic — arbitrated by the Judge"), unsafe_allow_html=True)

        for i, r in enumerate(results):
            with st.expander(f"{i+1:02d}  {r['paper']['title'][:70]}...", expanded=(i == 0)):
                vd    = r["verdict"]
                score = vd["score"]

                # Verdict banner
                if score >= 8:   bcolor = "#22c55e"
                elif score >= 5: bcolor = GOLD
                elif score >= 3: bcolor = "#f97316"
                else:            bcolor = "#ef4444"

                st.markdown(f"""
<div style="background:{GREY1};border:1px solid {bcolor}40;border-top:2px solid {bcolor};
            border-radius:4px;padding:1.2rem 1.4rem;margin-bottom:1.2rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 0.3rem 0;">Judge Verdict</p>
            <p style="color:{bcolor};font-size:1.8rem;font-weight:700;margin:0;letter-spacing:-0.02em;">{score}<span style="font-size:1rem;color:{GREY3};font-weight:400;"> / 10</span></p>
        </div>
        <div style="text-align:right;">
            {verdict_chip(vd['verdict'])}
            <p style="color:{GREY3};font-size:0.8rem;margin:0.5rem 0 0 0;max-width:260px;">{vd['recommendation']}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

                # Sub-scores
                bd = vd.get("breakdown", {})
                if bd:
                    bc1, bc2, bc3, bc4 = st.columns(4)
                    bc1.metric("Claim",    f"{bd.get('claim_score',0)}/10")
                    bc2.metric("Method",   f"{bd.get('method_score',0)}/10")
                    bc3.metric("Result",   f"{bd.get('result_score',0)}/10")
                    bc4.metric("Sentences",bd.get("total_sentences",0))

                st.markdown(divider(), unsafe_allow_html=True)

                # Defender / Critic columns
                left, right = st.columns(2)

                with left:
                    st.markdown(f"""
<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 0.4rem 0;">Defender — Strengths</p>
<p style="color:{GREY3};font-size:0.78rem;margin:0 0 0.8rem 0;">{r['defence']['overall_stance']}</p>
""", unsafe_allow_html=True)
                    for arg in r["defence"]["arguments"]:
                        clean = arg.lstrip("✅ ").lstrip("⚠️ ").lstrip("❌ ").strip()
                        st.markdown(f"""
<div style="background:{GREY1};border:1px solid {GREY2};border-left:2px solid #22c55e;
            border-radius:3px;padding:0.5rem 0.75rem;margin-bottom:0.35rem;">
    <p style="color:#c8c8c8;font-size:0.82rem;margin:0;line-height:1.5;">{clean}</p>
</div>""", unsafe_allow_html=True)

                with right:
                    st.markdown(f"""
<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 0.4rem 0;">Critic — Weaknesses</p>
<p style="color:{GREY3};font-size:0.78rem;margin:0 0 0.8rem 0;">{r['critique']['overall_stance']}</p>
""", unsafe_allow_html=True)
                    for crit in r["critique"]["criticisms"]:
                        clean = crit.lstrip("✅ ").lstrip("⚠️ ").lstrip("❌ ").strip()
                        st.markdown(f"""
<div style="background:{GREY1};border:1px solid {GREY2};border-left:2px solid #ef4444;
            border-radius:3px;padding:0.5rem 0.75rem;margin-bottom:0.35rem;">
    <p style="color:#c8c8c8;font-size:0.82rem;margin:0;line-height:1.5;">{clean}</p>
</div>""", unsafe_allow_html=True)

                st.markdown(divider(), unsafe_allow_html=True)
                st.markdown(f'<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 0.6rem 0;">Judge — Summary</p>', unsafe_allow_html=True)
                summary_html = vd["summary"].replace("\n\n", "<br/><br/>").replace("\n", " ")
                st.markdown(f"""
<div style="background:{GREY1};border:1px solid {GREY4};border-left:2px solid {GOLD};
            border-radius:3px;padding:1rem 1.2rem;">
    <p style="color:#c8c8c8;font-size:0.85rem;margin:0;line-height:1.7;">{summary_html}</p>
</div>""", unsafe_allow_html=True)

    # ── TAB 4: Dashboard ──────────────────────────────────────────────────────
    with tab4:
        st.markdown(page_header("Dashboard", "Aggregate metrics across all analysed papers"), unsafe_allow_html=True)

        stats = compute_summary_stats(results)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Papers Analysed", stats["num_papers"])
        k2.metric("Average Score",   f"{stats['avg_score']}/10")
        k3.metric("Highest Score",   f"{stats['max_score']}/10")
        k4.metric("Lowest Score",    f"{stats['min_score']}/10")

        try:
            import plotly.graph_objects as go
            import plotly.express as px

            layout_base = dict(
                plot_bgcolor=GREY1, paper_bgcolor=GREY1,
                font=dict(color=WHITE, family="Space Grotesk", size=11),
                margin=dict(l=0, r=0, t=44, b=0),
            )

            cl, cr = st.columns(2)

            with cl:
                titles = [r["paper"]["title"][:28] + "..." for r in results]
                scores = [r["verdict"]["score"] for r in results]
                bar_colors = ["#22c55e" if s >= 8 else GOLD if s >= 5 else "#f97316" if s >= 3 else "#ef4444" for s in scores]
                fig_s = go.Figure(data=[go.Bar(
                    x=titles, y=scores,
                    marker_color=bar_colors, marker_line_width=0,
                    text=scores, textposition="outside",
                    textfont=dict(color=WHITE, size=11),
                )])
                fig_s.update_layout(
                    title=dict(text="Score Per Paper", font=dict(color=GOLD, size=12), x=0),
                    yaxis=dict(range=[0, 12], showgrid=True, gridcolor=GREY2, color=GREY3, tickfont=dict(color=GREY3)),
                    xaxis=dict(showgrid=False, color=GREY3, tickfont=dict(color=GREY3, size=10)),
                    **layout_base,
                )
                st.plotly_chart(fig_s, use_container_width=True)

            with cr:
                lbl_counts = stats["label_counts"]
                cat_colors_list = ["#60a5fa", "#34d399", GOLD, "#f87171"]
                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(lbl_counts.keys()),
                    values=list(lbl_counts.values()),
                    marker=dict(colors=cat_colors_list, line=dict(color=GREY1, width=2)),
                    hole=0.55,
                    textfont=dict(size=11, color=WHITE),
                )])
                fig_pie.update_layout(
                    title=dict(text="Sentence Categories", font=dict(color=GOLD, size=12), x=0),
                    legend=dict(font=dict(color=WHITE), bgcolor="rgba(0,0,0,0)"),
                    **layout_base,
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            vdict = stats.get("verdict_counts", {})
            if vdict:
                fig_v = go.Figure(data=[go.Bar(
                    x=list(vdict.keys()), y=list(vdict.values()),
                    marker_color=GOLD, marker_line_width=0,
                    text=list(vdict.values()), textposition="outside",
                    textfont=dict(color=WHITE, size=11),
                )])
                fig_v.update_layout(
                    title=dict(text="Verdict Distribution", font=dict(color=GOLD, size=12), x=0),
                    yaxis=dict(showgrid=True, gridcolor=GREY2, color=GREY3),
                    xaxis=dict(showgrid=False, color=GREY3, tickfont=dict(color=GREY3, size=10)),
                    **layout_base,
                )
                st.plotly_chart(fig_v, use_container_width=True)

        except ImportError:
            for r in results:
                st.write(f"{r['paper']['title'][:60]}: {r['verdict']['score']}/10")

    # ── TAB 5: History ────────────────────────────────────────────────────────
    with tab5:
        st.markdown(page_header("History", "Previous analysis sessions"), unsafe_allow_html=True)
        history = load_session()

        if not history:
            st.markdown(f"""
<div style="background:{GREY1};border:1px solid {GREY2};border-radius:4px;
            padding:2rem;text-align:center;color:{GREY3};font-size:0.85rem;">
    No history found. Run an analysis to record sessions here.
</div>""", unsafe_allow_html=True)
        else:
            for entry in reversed(history[-10:]):
                with st.expander(f"{entry.get('timestamp','')}  ·  {entry.get('query','?')}"):
                    for v in entry.get("verdicts", []):
                        st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.5rem 0;border-bottom:1px solid {GREY2};">
    <span style="color:#c8c8c8;font-size:0.85rem;">{v.get('title','?')[:70]}</span>
    <div style="display:flex;gap:0.5rem;">
        {score_chip(v.get('score', 0))}
        {verdict_chip(v.get('verdict','?'))}
    </div>
</div>""", unsafe_allow_html=True)

else:
    # ── Landing State ─────────────────────────────────────────────────────────
    st.markdown(page_header("Research Intelligence Platform", "Multi-agent debate system for automated research critique"), unsafe_allow_html=True)

    st.markdown(f'<p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">How It Works</p>', unsafe_allow_html=True)

    cols = st.columns(4)
    steps = [
        ("01", "Research Agent",     "Fetches papers from arXiv and Semantic Scholar APIs"),
        ("02", "NLP Pipeline",       "Cleans, tokenises, and classifies each sentence"),
        ("03", "Debate Agents",      "Defender builds the case for the paper. Critic challenges it."),
        ("04", "Judge Verdict",      "Synthesises both sides into a score and recommendation"),
    ]
    for col, (num, title, desc) in zip(cols, steps):
        col.markdown(f"""
<div style="background:{GREY1};border:1px solid {GREY2};border-radius:4px;padding:1.2rem;">
    <p style="color:{GOLD};font-size:0.72rem;font-weight:700;letter-spacing:0.1em;margin:0 0 0.5rem 0;">{num}</p>
    <p style="color:{WHITE};font-size:0.95rem;font-weight:600;margin:0 0 0.4rem 0;">{title}</p>
    <p style="color:{GREY3};font-size:0.82rem;line-height:1.55;margin:0;">{desc}</p>
</div>""", unsafe_allow_html=True)

    st.markdown(f"""
<br/>
<div style="background:{GREY1};border:1px solid {GREY2};border-radius:4px;padding:1.2rem 1.5rem;margin-top:0.5rem;">
    <p style="color:{GREY3};font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 0.5rem 0;">Get Started</p>
    <p style="color:{WHITE};font-size:0.88rem;margin:0;">Enter a research topic in the sidebar and click <strong style="color:{GOLD};">Run Analysis</strong>.</p>
</div>""", unsafe_allow_html=True)
