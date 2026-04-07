[agent-setup.md](https://github.com/user-attachments/files/26321566/agent-setup.md)
# Agent 配置详细步骤

本文档记录两个 Agent 工作流的完整搭建过程，可作为部署参考。

---

## Agent 1 — 双语问答工作流

### 节点结构

```
开始（对话式）→ 知识检索_0 → 智能体_0 → 回复消息_0
```

### Step 1：创建 Agent

进入 RAGFlow → 智能体 → 创建智能体，命名为「辅导版双语问答工作流」。

### Step 2：配置「知识检索_0」节点

从「开始」节点连出，选择「基础 → 知识检索」。

右侧配置面板：

| 配置项 | 值 |
|--------|-----|
| 查询变量 | `开始输入 / sys.query` |
| 检索来源 | 知识库 |
| 知识库 | AI Governance Docs |
| 相似度阈值 | 0.3 |
| Top N | 6 |
| 跨语言搜索 | English + Chinese |
| 空回复 | 抱歉，在当前知识库中未找到相关合规信息。请尝试换一种问法，或确认该问题是否在 AI 治理框架范围内。 |

### Step 3：配置「智能体_0」节点

从「知识检索_0」连出，选择「基础 → 智能体」。

**系统提示词**：复制 [`prompts/bilingual_qa.md`](../prompts/bilingual_qa.md) 中的内容。

**用户提示词**（通过 `{x}` 插入变量）：

```
以下是从知识库中检索到的相关合规内容，请基于此内容回答用户问题：

{知识检索_0.formalized_content}

用户问题：{sys.query}
```

### Step 4：配置「回复消息_0」节点

从「智能体_0」连出，选择「对话 → 回复消息」。

消息内容引用变量：`智能体_0 / content`

### Step 5：保存并测试

点击「运行」，在聊天框输入测试问题：

```
NIST AI RMF 中 GOVERN 职能的核心要求是什么？
```

---

## Agent 2 — 差距分析工作流

### 节点结构

```
开始（对话式）→ 知识检索_0 → 智能体_0 → 回复消息_0
```

### Step 1：创建 Agent

进入 RAGFlow → 智能体 → 创建智能体，命名为「差距分析_NIST RMF」。

### Step 2：配置「知识检索_0」节点

| 配置项 | 值 |
|--------|-----|
| 查询变量 | 手动输入固定文本（不使用变量）：`NIST AI RMF GOVERN MAP MEASURE MANAGE requirements` |
| 知识库 | AI Governance Docs |
| 相似度阈值 | 0.3 |
| Top N | 8 |
| 跨语言搜索 | English + Chinese |

> ⚠️ 注意：查询变量使用固定文本而非 `sys.query`，目的是每次都拉取完整的 NIST RMF 条款作为参照标准。

### Step 3：配置「智能体_0」节点

**系统提示词**：复制 [`prompts/gap_analysis.md`](../prompts/gap_analysis.md) 中的内容。

**用户提示词**：

```
以下是NIST AI RMF框架的参考条款（来自知识库）：

{知识检索_0.formalized_content}

以下是用户提交的待评估文档内容：

{sys.query}

请对该文档进行差距分析，严格按照JSON格式输出结果。
```

### Step 4：配置「回复消息_0」节点

消息内容引用变量：`智能体_0 / content`

### Step 5：保存并测试

点击「运行」，将 [`examples/sample_policy.txt`](../examples/sample_policy.txt) 的内容粘贴到聊天框发送。

预期输出：结构化 JSON，包含 GOVERN / MAP / MEASURE / MANAGE 四大职能的覆盖率与差距列表。

---

## 获取 Agent ID（用于 Python 脚本调用）

1. 进入「智能体」列表，找到「差距分析_NIST RMF」
2. 点击右上角「管理」
3. 复制页面 URL 中的 ID 段，或在管理页面直接复制 Agent ID

```bash
export GAP_AGENT_ID="your-agent-id-here"
```

## 获取 API Key

RAGFlow 右上角头像 → API → 创建 API Key

```bash
export RAGFLOW_API_KEY="your-api-key-here"
```
