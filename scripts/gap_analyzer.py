#!/usr/bin/env python3
"""
gap_analyzer.py
---------------
ComplianceRAG — 差距分析命令行工具

通过 RAGFlow API 调用「差距分析_NIST RMF」Agent，
对输入的企业文档进行合规差距分析，输出结构化 JSON 报告。

用法 / Usage:
    python gap_analyzer.py --input policy.txt
    python gap_analyzer.py --input policy.txt --output report.json
    python gap_analyzer.py --text "公司AI策略内容..."
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests


# ── 配置区 Configuration ────────────────────────────────────────────────────

RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://localhost")
RAGFLOW_API_KEY  = os.getenv("RAGFLOW_API_KEY", "")
AGENT_ID         = os.getenv("GAP_AGENT_ID", "")      # 差距分析_NIST RMF 的 Agent ID

# 超时设置（差距分析较慢，给足时间）
REQUEST_TIMEOUT  = 120  # seconds


# ── RAGFlow API 调用 ─────────────────────────────────────────────────────────

def create_session(agent_id: str) -> str:
    """创建一个新的 Agent 会话，返回 session_id"""
    url = f"{RAGFLOW_BASE_URL}/api/v1/agents/{agent_id}/sessions"
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json={}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"创建会话失败: {data.get('message')}")
    return data["data"]["id"]


def run_gap_analysis(agent_id: str, session_id: str, document_text: str) -> str:
    """
    调用差距分析 Agent，返回原始 content 字符串（JSON 格式）

    RAGFlow Agent completions API:
    POST /api/v1/agents/{agent_id}/completions
    """
    url = f"{RAGFLOW_BASE_URL}/api/v1/agents/{agent_id}/completions"
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "question": document_text,
        "stream": False,
        "session_id": session_id,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"Agent 调用失败: {data.get('message')}")

    # 从响应中提取 answer
    answer = data.get("data", {}).get("answer", "")
    if not answer:
        raise RuntimeError("Agent 返回内容为空，请检查工作流配置。")
    return answer


# ── 结果解析 ─────────────────────────────────────────────────────────────────

def parse_json_output(raw: str) -> dict:
    """
    从 Agent 返回的字符串中提取 JSON。
    处理模型可能在 JSON 前后添加 markdown 代码块的情况。
    """
    # 去掉可能存在的 ```json ... ``` 包裹
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # 去掉首尾的 ``` 行
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"无法解析 Agent 输出为 JSON。\n"
            f"原始输出：\n{raw[:500]}...\n\n"
            f"解析错误：{e}\n\n"
            f"提示：请检查智能体节点的系统提示词是否包含 <output_format> 约束。"
        ) from e


# ── 报告展示 ─────────────────────────────────────────────────────────────────

def print_summary(report: dict) -> None:
    """在终端打印人类可读的摘要"""
    sep = "─" * 60

    print(f"\n{sep}")
    print("  ComplianceRAG — 差距分析报告")
    print(sep)

    print(f"\n📄 文档摘要：{report.get('document_summary', 'N/A')}")
    print(f"📐 对标框架：{report.get('framework', 'N/A')}")

    coverage = report.get("overall_coverage", 0)
    bar_filled = int(coverage * 20)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    print(f"📊 整体覆盖率：[{bar}] {coverage * 100:.0f}%\n")

    status_icon = {"covered": "✅", "partial": "⚠️ ", "missing": "❌"}

    for fn in report.get("functions", []):
        icon = status_icon.get(fn.get("status", "missing"), "❓")
        fn_coverage = fn.get("coverage", 0)
        print(f"{icon} {fn['name']:<10} 覆盖率 {fn_coverage * 100:.0f}%  [{fn.get('status', '').upper()}]")

        matched = fn.get("matched_clauses", [])
        if matched:
            print(f"   匹配条款: {', '.join(matched)}")

        gaps = fn.get("gaps", [])
        if gaps:
            for gap in gaps[:3]:   # 最多展示3条
                print(f"   • {gap}")
            if len(gaps) > 3:
                print(f"   ... 共 {len(gaps)} 条差距，详见 JSON 输出")
        print()

    print("💡 优先建议：")
    for i, rec in enumerate(report.get("top_recommendations", []), 1):
        print(f"   {i}. {rec}")

    print(f"\n{sep}\n")


# ── 主流程 ───────────────────────────────────────────────────────────────────

def analyze(document_text: str, output_path: str | None = None) -> dict:
    """完整差距分析流程，返回结构化报告 dict"""

    # 1. 前置检查
    if not RAGFLOW_API_KEY:
        print("❌ 错误：请设置环境变量 RAGFLOW_API_KEY")
        print("   export RAGFLOW_API_KEY='your-api-key'")
        sys.exit(1)

    if not AGENT_ID:
        print("❌ 错误：请设置环境变量 GAP_AGENT_ID（差距分析 Agent 的 ID）")
        print("   在 RAGFlow → 智能体 → 差距分析_NIST RMF → 管理 → 复制 ID")
        sys.exit(1)

    print(f"🔗 连接 RAGFlow: {RAGFLOW_BASE_URL}")
    print(f"🤖 Agent ID: {AGENT_ID[:8]}...")

    # 2. 创建会话
    print("📋 创建分析会话...")
    try:
        session_id = create_session(AGENT_ID)
        print(f"   Session: {session_id[:12]}...")
    except Exception as e:
        print(f"❌ 创建会话失败: {e}")
        sys.exit(1)

    # 3. 运行差距分析
    print("⏳ 正在分析文档，请稍候（通常需要 30-60 秒）...")
    start = time.time()
    try:
        raw_output = run_gap_analysis(AGENT_ID, session_id, document_text)
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        sys.exit(1)
    elapsed = time.time() - start
    print(f"✅ 分析完成，耗时 {elapsed:.1f}s")

    # 4. 解析 JSON
    try:
        report = parse_json_output(raw_output)
    except ValueError as e:
        print(f"⚠️  {e}")
        print("\n原始输出已保存为 raw_output.txt 供调试")
        Path("raw_output.txt").write_text(raw_output, encoding="utf-8")
        sys.exit(1)

    # 5. 输出结果
    print_summary(report)

    # 6. 保存 JSON
    if output_path:
        out = Path(output_path)
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        out = Path(f"gap_report_{timestamp}.json")

    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"📁 完整报告已保存: {out.resolve()}")

    return report


# ── CLI 入口 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ComplianceRAG 差距分析工具 — 对标 NIST AI RMF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:
  # 分析本地文本文件
  python gap_analyzer.py --input policy.txt

  # 指定输出路径
  python gap_analyzer.py --input policy.txt --output reports/result.json

  # 直接传入文本内容
  python gap_analyzer.py --text "我们公司的AI策略规定所有AI系统须经审批..."

环境变量 / Environment variables:
  RAGFLOW_BASE_URL   RAGFlow 地址，默认 http://localhost
  RAGFLOW_API_KEY    RAGFlow API Key（必填）
  GAP_AGENT_ID       差距分析 Agent 的 ID（必填）
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input", "-i",
        metavar="FILE",
        help="待分析的文档路径（支持 .txt / .md）",
    )
    group.add_argument(
        "--text", "-t",
        metavar="TEXT",
        help="直接输入文档内容字符串",
    )

    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="输出 JSON 报告的路径（默认自动生成文件名）",
    )

    args = parser.parse_args()

    # 读取文档内容
    if args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"❌ 文件不存在: {path}")
            sys.exit(1)
        document_text = path.read_text(encoding="utf-8")
        print(f"📂 读取文件: {path.name} ({len(document_text)} 字符)")
    else:
        document_text = args.text
        print(f"📝 使用输入文本 ({len(document_text)} 字符)")

    if len(document_text.strip()) < 50:
        print("❌ 文档内容太短，请提供至少 50 字的文档内容。")
        sys.exit(1)

    analyze(document_text, args.output)


if __name__ == "__main__":
    main()
