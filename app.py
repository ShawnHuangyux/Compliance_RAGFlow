"""
ComplianceRAG — 差距分析可视化报告界面
Streamlit dashboard for gap analysis results

运行方式 / Run:
    streamlit run app.py
"""

import json
import os
import sys
import time
from pathlib import Path

import plotly.graph_objects as go
import requests
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ComplianceRAG · Gap Analysis",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.02em;
}

/* Main background */
.stApp {
    background-color: #0d0f14;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #111318;
    border-right: 1px solid #1e2028;
}

/* Cards */
.metric-card {
    background: #111318;
    border: 1px solid #1e2028;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.metric-card:hover {
    border-color: #2e3248;
}

/* Status badges */
.badge-covered  { background:#0e3a2a; color:#34d399; border:1px solid #065f46; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:500; }
.badge-partial  { background:#3a2a0a; color:#fbbf24; border:1px solid #92400e; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:500; }
.badge-missing  { background:#3a0e0e; color:#f87171; border:1px solid #991b1b; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:500; }

/* Coverage bar */
.cov-bar-bg  { background:#1e2028; border-radius:6px; height:8px; margin: 8px 0 4px; }
.cov-bar-fill { border-radius:6px; height:8px; }

/* Gap item */
.gap-item {
    background: #0d0f14;
    border-left: 3px solid #f87171;
    padding: 8px 14px;
    margin: 6px 0;
    border-radius: 0 6px 6px 0;
    font-size: 13px;
    color: #94a3b8;
}

/* Clause tag */
.clause-tag {
    display: inline-block;
    background: #1e293b;
    color: #60a5fa;
    border: 1px solid #1e40af;
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 11px;
    margin: 2px 3px 2px 0;
}

/* Rec item */
.rec-item {
    background: #111318;
    border: 1px solid #1e2028;
    border-left: 3px solid #34d399;
    padding: 10px 16px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
    font-size: 13px;
    color: #cbd5e1;
    line-height: 1.6;
}

/* Header area */
.page-header {
    padding: 24px 0 8px;
    border-bottom: 1px solid #1e2028;
    margin-bottom: 28px;
}

/* Divider */
hr { border-color: #1e2028 !important; }

/* Input areas */
.stTextArea textarea {
    background: #111318 !important;
    border: 1px solid #1e2028 !important;
    color: #e2e8f0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 13px !important;
    border-radius: 8px !important;
}

/* Buttons */
.stButton > button {
    background: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-weight: 500 !important;
    padding: 10px 24px !important;
    transition: background 0.2s !important;
}
.stButton > button:hover {
    background: #1d4ed8 !important;
}

/* Demo button */
.demo-btn > button {
    background: #111318 !important;
    border: 1px solid #1e2028 !important;
    color: #94a3b8 !important;
}
.demo-btn > button:hover {
    border-color: #2e3248 !important;
    color: #e2e8f0 !important;
}

/* Metric numbers */
.big-number {
    font-family: 'Syne', sans-serif;
    font-size: 42px;
    font-weight: 800;
    line-height: 1;
    color: #e2e8f0;
}
.big-label {
    font-size: 11px;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

# ── Sample data (today's actual test output) ──────────────────────────────────

SAMPLE_REPORT = {
    "document_summary": "公司级AI系统采购、部署与使用的审批及安全评估规定，涵盖数据、供应商与培训要求。",
    "framework": "NIST AI RMF",
    "overall_coverage": 0.25,
    "functions": [
        {
            "name": "GOVERN",
            "coverage": 0.3,
            "status": "partial",
            "matched_clauses": ["GOVERN-1.1（高层责任）", "GOVERN-1.2（AI风险管理纳入企业治理）"],
            "gaps": [
                "缺少AI风险管理政策文件",
                "未建立跨部门治理机构职责",
                "缺少定期治理评审机制",
                "未设定AI伦理与公平性治理目标",
                "缺少利益相关方沟通机制",
                "无持续改进治理流程",
            ],
        },
        {
            "name": "MAP",
            "coverage": 0.2,
            "status": "partial",
            "matched_clauses": [],
            "gaps": [
                "未建立AI系统分类与上下文描述流程",
                "未识别并记录AI风险与影响",
                "缺少利益相关方与使用场景映射",
                "未对数据与模型来源进行风险梳理",
                "无系统边界与假设文档",
            ],
        },
        {
            "name": "MEASURE",
            "coverage": 0.2,
            "status": "partial",
            "matched_clauses": [],
            "gaps": [
                "缺少AI系统性能与风险指标定义",
                "无持续测试/验证方法",
                "未规定偏差与公平性评估",
                "缺少第三方评估与透明度报告",
                "未建立事件与异常监测机制",
            ],
        },
        {
            "name": "MANAGE",
            "coverage": 0.3,
            "status": "partial",
            "matched_clauses": ["MANAGE-1.2（常规/高风险场景区分管理）"],
            "gaps": [
                "未建立AI风险应对与缓解策略",
                "缺少模型更新/退役流程",
                "未规定事件响应与恢复程序",
                "未对供应商进行持续风险跟踪",
                "无定期管理评审与改进记录",
            ],
        },
    ],
    "top_recommendations": [
        "制定并发布覆盖全生命周期的AI风险管理政策，明确跨部门治理机构职责与定期评审机制",
        "建立AI系统分类、上下文与影响识别流程，形成统一的风险与使用场景映射文档",
        "定义可量化的AI性能、公平性、安全与透明度指标，并配套持续测试与第三方评估机制",
    ],
}

SAMPLE_DOC = """【XX科技有限公司 AI系统使用规范 v1.2】

1. 总则
本公司所有AI系统的采购、部署和使用须经IT部门审批。
AI相关决策须由业务负责人签字确认。

2. 风险管理
对于高风险AI应用场景（如信贷评分、人脸识别），
须在上线前完成内部安全评估。

3. 数据使用
训练数据须经数据治理委员会审批。
禁止使用未脱敏的个人数据训练模型。

4. 供应商管理
采购AI服务须签订数据处理协议（DPA）。
供应商须提供安全合规证明（如ISO 27001认证）。

5. 员工培训
所有使用AI工具的员工须完成年度AI伦理培训。"""

# ── RAGFlow API helpers ───────────────────────────────────────────────────────

def call_ragflow_agent(base_url: str, api_key: str, agent_id: str, document_text: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # 1. Create session
    sess_resp = requests.post(
        f"{base_url}/api/v1/agents/{agent_id}/sessions",
        headers=headers, json={}, timeout=30,
    )
    sess_resp.raise_for_status()
    sess_data = sess_resp.json()
    if sess_data.get("code") != 0:
        raise RuntimeError(f"Session creation failed: {sess_data.get('message')}")
    session_id = sess_data["data"]["id"]

    # 2. Run analysis
    comp_resp = requests.post(
        f"{base_url}/api/v1/agents/{agent_id}/completions",
        headers=headers,
        json={"question": document_text, "stream": True, "session_id": session_id},
        timeout=120,
        stream=True,
    )
    comp_resp.raise_for_status()

    # 3. 累加所有 message 事件的 data.content
    full_answer = ""

    for raw_line in comp_resp.iter_lines():
        if not raw_line:
            continue
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if payload in ("", "[DONE]"):
            continue
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue

        if chunk.get("event") == "message":
            fragment = chunk.get("data", {}).get("content", "")
            if fragment:
                full_answer += fragment  # 增量累加

    if not full_answer:
        raise RuntimeError("Agent returned empty response.")

    # 4. 剥离 markdown 代码块标记
    text = full_answer.strip()
    if text.startswith("```"):
        lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    return json.loads(text)


# ── Visualisations ────────────────────────────────────────────────────────────

def make_radar(report: dict) -> go.Figure:
    functions = report.get("functions", [])
    names  = [f["name"] for f in functions]
    values = [f.get("coverage", 0) * 100 for f in functions]
    names_closed  = names  + [names[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed, theta=names_closed,
        fill="toself",
        fillcolor="rgba(37,99,235,0.15)",
        line=dict(color="#3b82f6", width=2),
        marker=dict(color="#3b82f6", size=6),
        name="Coverage %",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#111318",
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(color="#475569", size=10),
                            gridcolor="#1e2028", linecolor="#1e2028"),
            angularaxis=dict(tickfont=dict(color="#94a3b8", size=12, family="Syne"),
                             gridcolor="#1e2028", linecolor="#1e2028"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        height=320,
    )
    return fig


def make_bar(report: dict) -> go.Figure:
    functions = report.get("functions", [])
    names    = [f["name"] for f in functions]
    coverage = [f.get("coverage", 0) * 100 for f in functions]
    gaps_cnt = [len(f.get("gaps", [])) for f in functions]

    STATUS_COLOR = {"covered": "#34d399", "partial": "#fbbf24", "missing": "#f87171"}
    colors = [STATUS_COLOR.get(f.get("status", "missing"), "#f87171") for f in functions]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=coverage,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:.0f}%" for v in coverage],
        textposition="outside",
        textfont=dict(color="#94a3b8", size=13, family="DM Mono"),
        hovertemplate="<b>%{x}</b><br>Coverage: %{y:.0f}%<extra></extra>",
        name="Coverage",
    ))
    fig.update_layout(
        xaxis=dict(tickfont=dict(color="#94a3b8", size=12, family="Syne"),
                   gridcolor="#1e2028", linecolor="#1e2028"),
        yaxis=dict(range=[0, 115], tickfont=dict(color="#475569", size=10),
                   gridcolor="#1e2028", linecolor="#1e2028", showgrid=True),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d0f14",
        margin=dict(l=10, r=10, t=20, b=10),
        height=280,
        showlegend=False,
        bargap=0.35,
    )
    return fig


def coverage_bar_html(pct: float, color: str) -> str:
    width = int(pct * 100)
    return f"""
    <div class="cov-bar-bg">
      <div class="cov-bar-fill" style="width:{width}%; background:{color};"></div>
    </div>
    """


BADGE_STYLES = {
    "covered": "background:#0e3a2a;color:#34d399;border:1px solid #065f46",
    "partial":  "background:#3a2a0a;color:#fbbf24;border:1px solid #92400e",
    "missing":  "background:#3a0e0e;color:#f87171;border:1px solid #991b1b",
}
def status_badge(status: str) -> str:
    style = BADGE_STYLES.get(status, BADGE_STYLES["missing"])
    return f'<span style="{style};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500">{status.upper()}</span>'


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🛡️ ComplianceRAG")
    st.markdown("<p style='color:#475569;font-size:12px;margin-top:-8px'>Gap Analysis Dashboard</p>", unsafe_allow_html=True)
    st.divider()

    mode = st.radio("分析模式 / Mode", ["🧪 Demo（示例数据）", "🔴 Live（调用 RAGFlow）"],
                    help="Demo 模式无需配置，直接展示示例结果")

    if "Live" in mode:
        st.divider()
        st.markdown("**RAGFlow 连接配置**")
        ragflow_url = st.text_input("Base URL", value="http://localhost", placeholder="http://localhost")
        api_key     = st.text_input("API Key", type="password", placeholder="ragflow-...")
        agent_id    = st.text_input("Agent ID", placeholder="差距分析_NIST RMF 的 ID")
        st.caption("在 RAGFlow → 智能体 → 管理 页面复制 Agent ID")
    else:
        ragflow_url = api_key = agent_id = ""

    st.divider()
    st.markdown("<p style='color:#334155;font-size:11px'>Built on RAGFlow · NIST AI RMF</p>",
                unsafe_allow_html=True)


# ── Main content ──────────────────────────────────────────────────────────────

st.markdown("""
<div class="page-header">
  <h1 style="color:#e2e8f0;margin:0;font-size:28px;">AI 合规差距分析报告</h1>
  <p style="color:#475569;margin:6px 0 0;font-size:13px;">NIST AI Risk Management Framework · Gap Analysis Dashboard</p>
</div>
""", unsafe_allow_html=True)

# ── Input area ────────────────────────────────────────────────────────────────

if "Live" in mode:
    st.markdown("#### 📄 待评估文档")

    # ── FIX: 在 text_area 渲染前取出预填内容，避免 widget key 冲突 ──
    # 若有预填内容，直接写入 widget 的 session_state key
    if "_doc_prefill" in st.session_state:
        st.session_state["doc_input"] = st.session_state.pop("_doc_prefill")

    doc_text = st.text_area(
        label="粘贴企业内部AI策略文档内容",
        height=180,
        placeholder="将企业 AI 策略、安全规范、风险管理制度等文档内容粘贴到此处...",
        label_visibility="collapsed",
        key="doc_input",   # ← 显式 key，Streamlit 会从 session_state["doc_input"] 读值
    )

    col_run, col_demo = st.columns([1, 5])
    with col_run:
        run_btn = st.button("▶  开始分析", use_container_width=True)
    with col_demo:
        st.markdown('<div class="demo-btn">', unsafe_allow_html=True)
        demo_btn = st.button("载入示例文档", use_container_width=False)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── FIX: 写入独立中间 key，rerun 后在 text_area 渲染前读取 ──
    if demo_btn:
        st.session_state["_doc_prefill"] = SAMPLE_DOC
        st.rerun()

    report = None
    if run_btn:
        if not doc_text or len(doc_text.strip()) < 50:
            st.error("请输入至少 50 字的文档内容。")
        elif not all([ragflow_url, api_key, agent_id]):
            st.error("请在左侧填写完整的 RAGFlow 连接配置。")
        else:
            with st.spinner("⏳ 正在分析，通常需要 30–60 秒..."):
                try:
                    report = call_ragflow_agent(ragflow_url, api_key, agent_id, doc_text)
                    st.success("✅ 分析完成")
                except Exception as e:
                    st.error(f"❌ 分析失败：{e}")

else:
    # Demo mode — use embedded sample data
    report = SAMPLE_REPORT
    st.info("🧪 当前为 Demo 模式，展示示例分析结果。切换侧边栏为 Live 模式可接入真实 RAGFlow。", icon="ℹ️")


# ── Results ───────────────────────────────────────────────────────────────────

if report:
    st.divider()

    # ── Row 1: Summary metrics ──────────────────────────────────────────────

    col1, col2, col3, col4 = st.columns(4)
    overall = report.get("overall_coverage", 0)
    functions = report.get("functions", [])
    total_gaps = sum(len(f.get("gaps", [])) for f in functions)
    covered_count = sum(1 for f in functions if f.get("status") == "covered")

    STATUS_COLOR = {"covered": "#34d399", "partial": "#fbbf24", "missing": "#f87171"}

    with col1:
        color = "#34d399" if overall >= 0.7 else "#fbbf24" if overall >= 0.4 else "#f87171"
        st.html(f"""
        <div class="metric-card">
          <div class="big-number" style="color:{color}">{overall*100:.0f}%</div>
          <div class="big-label">整体覆盖率</div>
        </div>
        """)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
          <div class="big-number">{total_gaps}</div>
          <div class="big-label">识别差距总数</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
          <div class="big-number">{len(functions)}</div>
          <div class="big-label">评估职能数</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
          <div class="big-number">{covered_count}</div>
          <div class="big-label">完全覆盖职能</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 2: Charts ───────────────────────────────────────────────────────

    st.markdown("#### 📊 框架覆盖率概览")
    chart_col1, chart_col2 = st.columns([1, 1])

    with chart_col1:
        st.markdown("<p style='color:#475569;font-size:12px;margin-bottom:4px'>覆盖率雷达图</p>", unsafe_allow_html=True)
        st.plotly_chart(make_radar(report), use_container_width=True, config={"displayModeBar": False})

    with chart_col2:
        st.markdown("<p style='color:#475569;font-size:12px;margin-bottom:4px'>职能覆盖率对比</p>", unsafe_allow_html=True)
        st.plotly_chart(make_bar(report), use_container_width=True, config={"displayModeBar": False})

    # ── Row 3: Function details ─────────────────────────────────────────────

    st.divider()
    st.markdown("#### 🔍 职能差距详情")

    fn_cols = st.columns(2)
    for i, fn in enumerate(functions):
        col = fn_cols[i % 2]
        status  = fn.get("status", "missing")
        cov_pct = fn.get("coverage", 0)
        color   = STATUS_COLOR.get(status, "#f87171")
        clauses = fn.get("matched_clauses", [])
        gaps    = fn.get("gaps", [])

        clause_html = "".join(
            f'<span style="display:inline-block;background:#1e293b;color:#60a5fa;border:1px solid #1e40af;padding:2px 9px;border-radius:4px;font-size:11px;margin:2px 3px 2px 0">{c}</span>'
            for c in clauses
        ) if clauses else '<span style="color:#334155;font-size:12px">暂无匹配条款</span>'
        
        gaps_html = "".join(
            f'<div style="background:#0d0f14;border-left:3px solid #f87171;padding:8px 14px;margin:6px 0;border-radius:0 6px 6px 0;font-size:13px;color:#94a3b8">• {g}</div>'
            for g in gaps
        )

        with col:
            st.html(f"""
            <style>
              .fn-card {{ background:#111318; border:1px solid #1e2028; border-radius:12px; padding:20px 24px; margin-bottom:12px; }}
              .cov-bar-bg {{ background:#1e2028; border-radius:6px; height:8px; margin:8px 0 4px; }}
              .cov-bar-fill {{ border-radius:6px; height:8px; }}
            </style>
            <div class="fn-card">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <span style="font-size:16px;font-weight:700;color:#e2e8f0">{fn['name']}</span>
                {status_badge(status)}
              </div>
              <div style="font-size:13px;color:{color};font-weight:500">{cov_pct*100:.0f}% 覆盖</div>
              <div class="cov-bar-bg"><div class="cov-bar-fill" style="width:{int(cov_pct*100)}%;background:{color}"></div></div>
              <div style="margin:12px 0 6px;font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:.08em">匹配条款</div>
              <div>{clause_html}</div>
              <div style="margin:12px 0 6px;font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:.08em">识别差距</div>
              {gaps_html}
            </div>
            """)

    # ── Row 4: Recommendations ──────────────────────────────────────────────

    st.divider()
    st.markdown("#### 💡 优先改进建议")
    recs = report.get("top_recommendations", [])
    for i, rec in enumerate(recs, 1):
        st.html(f"""
        <div class="rec-item">
          <span style="color:#34d399;font-weight:500;margin-right:10px">{i:02d}</span>{rec}
        </div>
        """)

    # ── Row 5: Export ───────────────────────────────────────────────────────

    st.divider()
    st.markdown("#### 📁 导出报告")
    exp_col1, exp_col2 = st.columns([1, 5])
    with exp_col1:
        json_str = json.dumps(report, ensure_ascii=False, indent=2)
        st.download_button(
            label="⬇  下载 JSON",
            data=json_str,
            file_name=f"gap_report_{time.strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )
