# HW9 Specification Agent

这是一个面向 OO Unit 3 HW9 的最小规格分析智能体。它读取官方 Java 接口中的
JML，把方法规格拆成结构化信息，再执行一致性检查并生成测试义务。

确定性代码负责接口 grounding、解析和基础检查；四阶段自动运行使用 DeepSeek API。
密钥只从环境变量读取，不写入仓库。

仓库还提供 4 个阶段 Prompt 与 HW9 专用 Skill。可以人工逐阶段调用模型，也可以先
用 `prepare` 命令组装包含真实接口上下文的完整输入。

## 快速开始

```powershell
cd Agent
python -m hw9_agent inspect `
  --source-root "D:\01_OO\Learn\Unit3\_code\u3_hw9" `
  --method queryMutualFollowingSum
```

查看全部方法：

```powershell
python -m hw9_agent list --source-root "D:\01_OO\Learn\Unit3\_code\u3_hw9"
```

输出 JSON：

```powershell
python -m hw9_agent inspect --source-root "...\u3_hw9" --method followUser --json
```

当方法名在多个接口中重复时，可追加 `--interface UserInterface`。

组装 `followUser` Analyzer 输入：

```powershell
python -m hw9_agent prepare `
  --source-root "D:\01_OO\Learn\Unit3\_code\u3_hw9" `
  --case-dir "cases\follow_user" `
  --stage analyzer `
  --method followUser `
  --output "outputs\follow_user\01-analyzer-input.md"
```

将阶段改为 `planner`、`generator`、`critic` 即可生成后续输入。组装器会读取案例目录
中的上游产物，并在缺失时立即报错。

## DeepSeek 自动运行

在当前 PowerShell 会话设置密钥：

```powershell
$env:DEEPSEEK_API_KEY = "你的密钥"
```

执行完整四阶段：

```powershell
python -m hw9_agent run `
  --source-root "D:\01_OO\Learn\Unit3\_code\u3_hw9" `
  --case-dir "cases\follow_user" `
  --method followUser `
  --output-dir "outputs\deepseek-follow-user"
```

默认使用 `deepseek-chat` 和 `https://api.deepseek.com`。可以通过 `--model`、`--base-url`
或 `DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL` 覆盖。每阶段的完整输入和模型输出都会保存，
便于复现实验和统计人工修改量。

## 学生 JML 填空审查

离线检查示例提交是否填完、框架是否被破坏：

```powershell
python -m hw9_agent exercise `
  --source-root "D:\01_OO\Learn\Unit3\_code\u3_hw9" `
  --exercise-dir "exercises\follow_user" `
  --submission "exercises\follow_user\samples\incomplete.jml" `
  --offline
```

启动 DeepSeek 多轮学习对话：

```powershell
python -m hw9_agent exercise `
  --source-root "D:\01_OO\Learn\Unit3\_code\u3_hw9" `
  --exercise-dir "exercises\follow_user" `
  --mode hint
```

进入后粘贴完整 JML，以 `/submit` 提交。支持 `/template`、`/requirement`、
`/mode hint|review|solution` 和 `/quit`。默认 `hint` 不给出完整答案；`review` 指出具体
语义问题；`solution` 适合教师展示参考修复。

题目目录中的 `rubric.json` 在当前原型中是本地文件。正式给学生部署时应放在服务端，
避免学生直接读取隐藏评分点。

## Web 学习界面

```powershell
$env:DEEPSEEK_API_KEY = "你的密钥"

python -m hw9_agent web `
  --source-root "D:\01_OO\Learn\Unit3\_code\u3_hw9" `
  --exercise-dir "exercises\follow_user" `
  --port 8000
```

浏览器访问 `http://127.0.0.1:8000`。页面提供逐空填写、完整 JML 实时预览、
Hint/Review/Solution 模式、多轮提交记录和一键重置。DeepSeek 密钥与隐藏 rubric 只在
本地后端使用，不会通过题目 API 发送给浏览器。

## 第一版流水线

1. `InterfaceLoader`：定位 `*Interface.java`。
2. `JmlParser`：抽取 model、invariant、requires、assignable、ensures、signals 和方法标记。
3. `SpecificationCritic`：检查 pure/frame、异常条件、正常行为与规格完整性。
4. `TestObligationGenerator`：生成正常、异常、边界和 side-effect 测试义务。

## Demo 资产

- `skills/`：JML、HW9 领域、规格模式和 critic 清单。
- `prompts/`：Analyzer、Planner、Generator、Critic。
- `cases/follow_user/`：需求、IR、计划、JML 和审查报告的端到端参考链路。
- `outputs/`：由 `prepare` 生成的可投喂模型输入，不保存模型密钥。

## 已知边界

- 这是面向课程 JML Level 0 风格的轻量解析器，不是完整 JML 编译器。
- 当前分析对象是官方接口规格，不判断学生实现是否满足规格。
- 下一步会加入“自然语言需求 → 结构化 IR → JML 草案”，以及实现/JUnit 验证器。
