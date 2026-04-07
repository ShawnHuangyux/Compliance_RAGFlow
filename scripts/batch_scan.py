#!/usr/bin/env python3
"""
batch_scan.py
-------------
ComplianceRAG — 批量文档差距分析工具

对一个目录下的所有 .txt / .md 文件依次运行差距分析，
汇总输出一份 CSV 总览报告。

用法 / Usage:
    python batch_scan.py --dir ./policies/
    python batch_scan.py --dir ./policies/ --output summary.csv
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

# 复用 gap_analyzer 的核心逻辑
sys.path.insert(0, str(Path(__file__).parent))
from gap_analyzer import analyze


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def scan_directory(dir_path: Path) -> list[Path]:
    """扫描目录，返回所有支持格式的文件列表"""
    files = [
        f for f in sorted(dir_path.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return files


def report_to_csv_row(filename: str, report: dict) -> dict:
    """把单份报告提炼为一行 CSV 数据"""
    row = {
        "文件名": filename,
        "文档摘要": report.get("document_summary", ""),
        "整体覆盖率": f"{report.get('overall_coverage', 0) * 100:.0f}%",
    }
    for fn in report.get("functions", []):
        name = fn["name"]
        row[f"{name}_覆盖率"] = f"{fn.get('coverage', 0) * 100:.0f}%"
        row[f"{name}_状态"] = fn.get("status", "")
        row[f"{name}_差距数"] = len(fn.get("gaps", []))

    recs = report.get("top_recommendations", [])
    row["首要建议"] = recs[0] if recs else ""
    return row


def main():
    parser = argparse.ArgumentParser(
        description="ComplianceRAG 批量差距分析 — 对标 NIST AI RMF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:
  python batch_scan.py --dir ./policies/
  python batch_scan.py --dir ./policies/ --output reports/summary.csv

环境变量 / Environment variables:
  RAGFLOW_BASE_URL   RAGFlow 地址，默认 http://localhost
  RAGFLOW_API_KEY    RAGFlow API Key（必填）
  GAP_AGENT_ID       差距分析 Agent 的 ID（必填）
        """,
    )
    parser.add_argument("--dir", "-d", required=True, metavar="DIR",
                        help="包含待分析文档的目录路径")
    parser.add_argument("--output", "-o", metavar="FILE",
                        help="CSV 汇总报告输出路径（默认自动生成）")
    parser.add_argument("--delay", type=float, default=3.0,
                        help="每份文档分析之间的间隔秒数，避免 API 限流（默认 3s）")
    args = parser.parse_args()

    dir_path = Path(args.dir)
    if not dir_path.is_dir():
        print(f"❌ 目录不存在: {dir_path}")
        sys.exit(1)

    files = scan_directory(dir_path)
    if not files:
        print(f"⚠️  目录中未找到 .txt 或 .md 文件: {dir_path}")
        sys.exit(0)

    print(f"\n📂 找到 {len(files)} 份文档，开始批量分析...\n")

    results = []
    failed = []

    for i, filepath in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 分析: {filepath.name}")
        try:
            document_text = filepath.read_text(encoding="utf-8")
            # 每份文档保存独立 JSON 报告
            json_out = filepath.parent / f"{filepath.stem}_gap_report.json"
            report = analyze(document_text, output_path=str(json_out))
            results.append(report_to_csv_row(filepath.name, report))
            print(f"   ✅ 完成，整体覆盖率: {report.get('overall_coverage', 0)*100:.0f}%\n")
        except SystemExit:
            failed.append(filepath.name)
            print(f"   ❌ 分析失败，跳过\n")

        # 间隔，避免触发 API 限流
        if i < len(files):
            time.sleep(args.delay)

    # 写入 CSV 汇总
    if results:
        if args.output:
            csv_path = Path(args.output)
            csv_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            csv_path = Path(f"batch_summary_{timestamp}.csv")

        fieldnames = list(results[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"\n{'─'*60}")
        print(f"📊 批量分析完成")
        print(f"   成功: {len(results)} 份  失败: {len(failed)} 份")
        print(f"   汇总报告: {csv_path.resolve()}")
        if failed:
            print(f"   失败文件: {', '.join(failed)}")
        print(f"{'─'*60}\n")
    else:
        print("\n❌ 所有文件分析均失败，请检查配置。")


if __name__ == "__main__":
    main()
