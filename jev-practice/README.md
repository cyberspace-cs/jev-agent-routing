# Jev Practice - 实战项目

基于程序员鱼皮的 Jev 教程实战项目集合。

## 🎯 项目列表

### 1. Jev 调试广场（playground.html）

中文版在线体验 Jev 三种 AI 原语：

- **Noul 判断题**：是不是？返回 0-1 概率
- **Choice 选择题**：选哪个？返回选项概率分布
- **Score 打分题**：打几分？返回自定义量表评分

**打开方式**：直接在浏览器打开 `playground.html`

---

### 2. 数字华容道（games/huarongdao.html）

4x4 滑块拼图游戏，每一步决策都交给 Jev：

- 输入：当前棋盘状态（4x4 数字矩阵）
- Jev 决策：空位应该往哪个方向移动（上/下/左/右）
- 输出：步数统计、总耗时、Jev 单次决策耗时

**核心思路**：Jev 不直接生成动作，而是基于结构化状态做决策判断。

---

### 3. 批量邮件分类（email-classifier.html）

模拟 1000 封邮件批量分类：

- **优先级判断**：紧急 / 普通 / 低优先级
- **部门路由**：财务 / 技术 / 销售
- 统计：总耗时、已分类数量、总成本

**鱼皮实测数据**：
- Jev：15.6 秒处理 1000 封，$0.0177
- DeepSeek：48.9 秒处理 1000 封，$0.0207

---

## 📚 参考文章

- [刚刚，全网刷屏的 Jev 模型正式开放！一手实战测评 + 保姆级教程](https://mp.weixin.qq.com/s/tKzLooBWfsNQ3xcFVQOjCw) - 程序员鱼皮

## 🚀 部署

直接用浏览器打开 HTML 文件即可体验。

接入真实 Jev API 需要：
1. 注册 TypeSafe 账号：https://console.typesafe.ai/
2. 获取 API Key
3. 配置环境变量 `JEV_API_KEY`
