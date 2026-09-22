# Agent 框架与技能连接器大全

> 整理 2026 年最热门的 Agent 框架、MCP 连接器、技能生态项目

---

## 🐝 openJiuwen 系列（华为开源）

### 1. JiuwenSwarm（蜂群多智能体工作台）
- **GitHub**: https://github.com/openJiuwen-ai/jiuwenswarm
- **定位**: 华为开源的多智能体统一工作台
- **核心特性**:
  - 蜂群多智能体协作（Coordination Engineering）
  - HITS（Human in the Swarm）人机协同
  - 支持技能、连接器、插件、专家、专家团五类资产
  - 鸿蒙 PC 版本已发布
- **适用场景**: 复杂任务多 Agent 协作、企业级 Agent 工作流

### 2. JiuwenClaw（龙虾 Agent）
- **GitHub**: https://github.com/openJiuwen-ai/jiuwenclaw
- **定位**: 接入日常通讯工具的 AI Agent 应用
- **核心特性**:
  - 聊天工具里直接调用 AI Agent
  - 支持 Team Skills 团队技能新范式
  - 20 分钟生成 200 页技术 PPT
  - 自主拉起装修团搞定全屋设计
- **适用场景**: 即时通讯 Agent、办公自动化

---

## 🔥 高星 Agent 框架

### 3. DeepMCPAgent（MCP 智能体脚手架）
- **GitHub**: https://github.com/DeepMCP/DeepMCPAgent
- **Star**: ⭐ 8000+
- **定位**: 零代码 MCP 智能体框架
- **核心特性**:
  - 无缝集成 LangChain 生态
  - 轻松构建复杂任务工作流
  - 被称为「MCP 智能体的最佳脚手架」
- **适用场景**: MCP 生态快速开发、零代码 Agent 搭建

### 4. mattpocock/skills（Claude Code 技能库）
- **GitHub**: https://github.com/mattpocock/skills
- **Star**: ⭐ 16.5 万
- **定位**: 前 Vercel TypeScript 布道者的 21 个 Claude Code 技能
- **核心特性**:
  - 小而可组合的设计理念
  - 不走"全流程接管"路线
  - 一堆能自由搭配的技能积木
- **适用场景**: TypeScript 开发、前端工程化、代码质量提升

---

## 🔌 MCP 连接器生态

### 5. GitHub MCP Server（官方）
- **GitHub**: https://github.com/github/github-mcp-server
- **定位**: GitHub 官方 MCP 服务器
- **核心特性**:
  - 51 个工具覆盖完整开发者工作流
  - 仓库管理、Issue/PR 自动化、CI/CD 监控
  - GitHub Projects 管理
- **适用场景**: 代码仓库管理、CI/CD 自动化、PR 审查

### 6. Playwright MCP（浏览器自动化）
- **GitHub**: https://github.com/microsoft/playwright
- **定位**: 浏览器自动化 MCP 连接器
- **核心特性**:
  - 稳定的浏览器上下文、定位器、页面操作
  - 截图、追踪、调试工具
- **适用场景**: Web 自动化、爬虫、UI 测试、网页交互

### 7. n8n MCP（工作流自动化）
- **GitHub**: https://github.com/n8n-io/n8n
- **定位**: 低代码工作流自动化平台
- **核心特性**:
  - 原生实例级 MCP 服务器（2026 年 4 月公开预览）
  - MCP 客户端节点
  - 双向 MCP 支持
- **适用场景**: 企业级工作流自动化、SaaS 集成

### 8. Dify MCP（LLM 应用开发平台）
- **GitHub**: https://github.com/langgenius/dify
- **定位**: LLM 应用开发平台
- **核心特性**:
  - 双向 MCP 支持
  - 调用外部 MCP 服务器作为工具
  - 暴露 Dify Agent/工作流为 MCP 服务器
- **适用场景**: LLM 应用开发、RAG、Agent 编排

---

## 🛠️ 技能管理工具

### 9. skill-mcp（技能包管理器）
- **定位**: 把 AI 技能当成有版本、有元数据、可权限控制的软件包来管理
- **核心特性**:
  - 版本控制、元数据、权限控制
  - 通过标准 MCP 协议暴露给任意 AI 客户端
- **适用场景**: 企业级技能资产管理、团队技能复用

---

## 📊 2026 Agent 生态趋势

| 趋势 | 说明 |
|------|------|
| 🔄 CLI+Skills 替代 MCP (stdio) | Perplexity 公开弃用 MCP (stdio) |
| 🔀 MCP(HTTP) 留存企业 | 企业级还是走 HTTP MCP |
| 🧩 Skills 崛起 | 渐进式披露解决 Context 问题 |
| 🤝 Subagent 兴起 | 多 Agent 协作成为主流 |
| 📦 技能资产化 | 技能变成可发布、可安装、可复用的资产 |

---

## 🚀 快速上手

### 入门级
1. 先玩 Dify / n8n 低代码平台
2. 体验 GitHub MCP Server
3. 试试 mattpocock/skills 的 21 个技能

### 进阶级
1. 用 DeepMCPAgent 搭建自己的 Agent
2. 接入 Playwright MCP 做浏览器自动化
3. 研究 JiuwenSwarm 的多 Agent 协作

### 大师级
1. 基于 openJiuwen 搭建企业级 Agent 平台
2. 设计自己的技能体系和连接器
3. 贡献开源技能到社区

---

## 📚 参考链接

- [openJiuwen 官网](https://www.openjiuwen.com/)
- [Agentic Hub](https://agentichub.openjiuwen.com/)
- [Swarm Skills Hub](https://swarmskills.openjiuwen.com/)
- [MCP 官方文档](https://modelcontextprotocol.io/)
