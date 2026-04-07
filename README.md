# ComplianceRAG

> **AI 治理合规知识库问答与差距分析系统**  
> **AI Governance Compliance Q&A and Gap Analysis System**

基于 [RAGFlow](https://github.com/infiniflow/ragflow) 改造，专为 AI 治理合规场景设计的双语知识库问答与差距分析工具。支持 NIST AI RMF、ISO 42001、EU AI Act 等主流框架，帮助企业快速检索合规要求、识别策略文档与框架之间的差距。

Built on [RAGFlow](https://github.com/infiniflow/ragflow), ComplianceRAG is a bilingual Q&A and gap analysis tool purpose-built for AI governance compliance. It supports major frameworks including NIST AI RMF, ISO 42001, and the EU AI Act, enabling organizations to quickly retrieve compliance requirements and identify gaps between their internal policies and framework standards.

---

## ✨ 核心功能 / Key Features

| 功能 | 说明 |
|------|------|
| 🌐 双语问答 | 自动检测语言，中文问题中文回答，英文问题英文回答 |
| 📎 条款引用 | 每条回答附带具体框架条款来源，如 `[Source: NIST AI RMF - GOVERN 1.1]` |
| 📊 差距分析 | 输入企业内部文档，自动输出结构化 JSON 差距报告 |
| 🔍 跨语言检索 | 中文问题可检索英文文档，反之亦然 |
| 🤖 Agent 工作流 | 基于 RAGFlow Agent Canvas 配置，无需修改核心代码 |

| Feature | Description |
|---------|-------------|
| 🌐 Bilingual Q&A | Auto-detects language; responds in Chinese or English accordingly |
| 📎 Clause citation | Every answer cites specific framework clauses, e.g. `[Source: NIST AI RMF - GOVERN 1.1]` |
| 📊 Gap analysis | Input any internal policy doc; receive a structured JSON gap report |
| 🔍 Cross-language retrieval | Chinese queries can surface English documents and vice versa |
| 🤖 Agent workflows | Configured via RAGFlow Agent Canvas — no core code changes required |

---

## 🏗️ 系统架构 / Architecture

```
用户输入 / User Input
        ↓
   [开始节点 / Begin]
        ↓
[知识检索 / Knowledge Retrieval]
  跨语言向量检索 NIST RMF / ISO 42001 / EU AI Act
        ↓
[智能体 / LLM Agent]  ←── System Prompt (bilingual rules + output format)
        ↓
[回复消息 / Reply]
  双语回答 + 条款引用 / Bilingual answer + clause citations
```

**改造层次说明 / Layer description:**

- **Layer 0 — RAGFlow Core**：原版 Docker 部署，不修改 / Vanilla Docker deployment, untouched
- **Layer 1 — 知识库配置**：文档导入、chunking 策略、元数据标签 / Document ingestion, chunking, metadata tagging
- **Layer 2 — Agent 工作流**：双语问答 Agent + 差距分析 Agent / Bilingual Q&A Agent + Gap Analysis Agent
- **Layer 3 — 轻量封装**：Python 调用脚本、批量分析工具 / Python call scripts, batch analysis tools

---

## 🚀 快速开始 / Quick Start

### 前置条件 / Prerequisites

- Docker >= 24.0 & Docker Compose >= v2.26
- RAM >= 16 GB
- 任意 LLM API Key（支持 OpenAI / Claude / DeepSeek / Kimi 等）

### 1. 启动 RAGFlow / Start RAGFlow

```bash
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/docker
docker compose -f docker-compose.yml up -d
```

浏览器访问 `http://localhost`，完成初始账号注册。  
Open `http://localhost` in your browser and complete initial account setup.

### 2. 导入合规文档 / Import compliance documents

在 RAGFlow 中创建 Dataset，命名为 `AI Governance Docs`，上传以下文档：  
Create a Dataset named `AI Governance Docs` in RAGFlow and upload:

| 文档 / Document | 获取方式 / Source |
|-----------------|-------------------|
| NIST AI RMF 1.0 | [nist.gov](https://airc.nist.gov/RMF_Overview) |
| ISO/IEC 42001 摘要 | ISO 官网或摘要版 |
| EU AI Act | [eur-lex.europa.eu](https://eur-lex.europa.eu) |
| 自有 Q&A 文档 | 内部整理 |

**推荐 chunking 设置 / Recommended chunking settings:**
- 策略：`parent-child`
- 开启 TOC 提取（长文档效果更好）
- 相似度阈值：`0.3`
- Top N：`6`（问答）/ `8`（差距分析）

### 3. 配置 Agent 工作流 / Configure Agent workflows

参考 [`docs/agent-setup.md`](docs/agent-setup.md) 中的详细步骤，在 RAGFlow Agent Canvas 中搭建两个工作流：  
Follow the step-by-step instructions in [`docs/agent-setup.md`](docs/agent-setup.md) to build two workflows in RAGFlow Agent Canvas:

- **辅导版双语问答工作流** — 合规问答
- **差距分析_NIST RMF** — 文档差距分析

### 4. 使用 Python 脚本调用 / Call via Python script

```bash
pip install -r requirements.txt

# 差距分析 / Gap analysis
python scripts/gap_analyzer.py --input your_policy.txt

# 批量扫描 / Batch scan
python scripts/batch_scan.py --dir ./docs/policies/
```

---

## 📁 项目结构 / Project Structure

```
compliance-rag/
├── README.md
├── README_zh.md
├── requirements.txt
├── docs/
│   ├── agent-setup.md          # Agent 配置详细步骤
│   └── architecture.png        # 架构图
├── prompts/
│   ├── bilingual_qa.md         # Agent 1 系统提示词
│   └── gap_analysis.md         # Agent 2 系统提示词
├── scripts/
│   ├── gap_analyzer.py         # 差距分析调用脚本
│   └── batch_scan.py           # 批量文档扫描
└── examples/
    ├── sample_policy.txt       # 示例企业文档
    └── sample_output.json      # 示例差距报告输出
```

---

## 📊 差距分析输出示例 / Gap Analysis Output Example

```json
{
  "document_summary": "公司级AI系统采购、部署与使用的审批及安全评估规定",
  "framework": "NIST AI RMF",
  "overall_coverage": 0.25,
  "functions": [
    {
      "name": "GOVERN",
      "coverage": 0.3,
      "status": "partial",
      "matched_clauses": ["GOVERN-1.1", "GOVERN-1.2"],
      "gaps": [
        "缺少AI风险管理政策文件",
        "未建立跨部门治理机构职责",
        "缺少定期治理评审机制"
      ]
    },
    {
      "name": "MAP",
      "coverage": 0.2,
      "status": "partial",
      "matched_clauses": [],
      "gaps": [
        "未建立AI系统分类与上下文描述流程",
        "未识别并记录AI风险与影响"
      ]
    }
  ],
  "top_recommendations": [
    "制定并发布覆盖全生命周期的AI风险管理政策",
    "建立AI系统分类与影响识别流程",
    "定义可量化的AI性能与公平性指标"
  ]
}
```

---

## 🗺️ 路线图 / Roadmap

- [x] NIST AI RMF 差距分析
- [x] 双语问答（中/英）
- [ ] ISO 42001 差距分析
- [ ] EU AI Act 风险分级评估
- [ ] Streamlit 可视化报告界面
- [ ] PDF 报告导出
- [ ] 批量文档扫描 CLI

---

## 🤝 相关项目 / Built With

- [RAGFlow](https://github.com/infiniflow/ragflow) — RAG 引擎底座
- [Kimi API](https://platform.moonshot.cn/) — LLM 推理（可替换）
- [NIST AI RMF](https://airc.nist.gov/RMF_Overview) — 框架来源

---

## 📄 许可证 / License

MIT License — 欢迎 fork 和二次改造 / Feel free to fork and adapt.
