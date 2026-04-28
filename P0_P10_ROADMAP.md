# Office Suite 4.0 — P0 到 P10 后续路线表

> 创建日期：2026-04-28  
> 依据：`GAP_ANALYSIS_REPORT.md` 与当前项目状态  
> 范围：规划文档，不包含实现改动。

## 总览

| 优先级 | 阶段名称 | 核心目标 | 预计周期 | 前置条件 | 主要产出 |
|---|---|---|---|---|---|
| P0 | 基线对齐与测试夹具修复 | 统一当前分支、测试、状态文档和样例文件策略 | 1-2 天 | 确定后续基准分支 | Phase 0 稳定、`STATUS.md` 同步、夹具策略明确 |
| P1 | MVP 架构补强 | 补齐样式级联、能力声明、尺寸一致性等 P0 架构问题 | 3-5 天 | P0 完成 | 样式级联测试、能力矩阵、README/STATUS 更新 |
| P2 | PPTX 渲染器模块化 | 拆分 PPTX 大文件，保持行为不变 | 3-5 天 | P1 完成 | `slide.py`/辅助模块、兼容 `deck.py` facade |
| P3 | DOCX/XLSX 渲染器模块化 | 拆分 DOCX/XLSX 结构，提升可维护性 | 1 周 | P2 或可并行启动 | `section.py`/`block.py`/`sheet.py`/`chart.py` 等模块规划落地 |
| P4 | DOCX/XLSX 功能深度增强 | 从“能生成文件”升级到“结构和样式可用” | 1-2 周 | P3 完成 | DOCX 节/段落/表格增强，XLSX 图表/公式/格式增强 |
| P5 | Hub 与资源系统完善 | 把 provider 骨架变成可靠资源获取与降级链 | 2-3 周 | P1 完成 | Provider 合同、fake MCP/AI 测试、缓存与 fallback 流程 |
| P6 | Pipeline DAG 可靠性 | 完善文档生成 DAG，而不是通用工作流平台 | 1-2 周 | P5 部分完成 | 拓扑排序、并发、retry、cycle detection、render nodes |
| P7 | Store 与可追溯产物 | 建立 artifact/history 持久化与可追踪输出 | 3-5 天 | P5/P6 基础稳定 | Artifact metadata、history records、source/output hash |
| P8 | 布局引擎深化 | 完善 Grid/Flex/Constraint，形成跨渲染器一致布局 | 2-4 周 | P1 完成 | 支持子集定义、布局快照测试、跨渲染器位置校验 |
| P9 | 视觉效果与媒体能力 | 推进 OKLCH、Filter、路径文字、视频/音频 fallback | 2-4 周 | P4/P8 稳定 | 色彩转换、duotone、路径文字矩阵、媒体占位/嵌入策略 |
| P10 | 开发体验、预览与质量门禁 | 完善预览、linter、依赖管理、性能和视觉 smoke test | 持续，首轮 1 周 | P0-P4 基础稳定 | `pyproject`、本地 HTTP 预览、CI 门禁、benchmark |

## P0：基线对齐与测试夹具修复

| 项目 | 内容 |
|---|---|
| 核心问题 | `GAP_ANALYSIS_REPORT.md` 基于 `main`，当前分支已删除部分 YAML 样例，测试夹具策略不一致 |
| 主要任务 | 确认基准分支；决定 `hello_world.yml`、`test_pagination.yml`、`world_book_day.yml` 去留；修复或改写 Phase 0 |
| 推荐做法 | Phase 0 使用内联最小 YAML；大型 demo 移到 `examples/`；根目录不放测试依赖样例 |
| 验收标准 | `pytest -q` 在干净 checkout 通过；`STATUS.md` 测试数量与实际一致 |
| 风险 | 盲目恢复 YAML 会和已有删除提交冲突；大型 fixture 会增加维护成本 |

## P1：MVP 架构补强

| 项目 | 内容 |
|---|---|
| 核心问题 | P0 功能可用，但样式级联、能力声明、尺寸常量仍需统一 |
| 主要任务 | 审计 `ir/cascade.py`；决定是否引入 `engine/style/cascade.py`；校准 renderer capability；检查 16:9 尺寸一致性 |
| 推荐做法 | 先补测试和文档，再移动模块；能力声明分为真实支持、降级支持、暂不支持 |
| 验收标准 | cascade 覆盖 theme/document/slide/element/inline；每个 renderer 有支持和降级测试 |
| 风险 | 过早移动 cascade 可能造成大范围 import churn |

## P2：PPTX 渲染器模块化

| 项目 | 内容 |
|---|---|
| 核心问题 | `renderer/pptx/deck.py` 过大，slide/shape/chart/text 边界不清晰 |
| 主要任务 | 抽出 slide 创建、背景、布局逻辑；拆出稳定 shape/text/image/table/chart helper；保留 `deck.py` 入口 |
| 推荐做法 | 一次只拆一组职责，不混入行为变更 |
| 验收标准 | 拆分前后测试结果一致；现有 import 路径不变 |
| 风险 | 没有结构测试时，拆分可能引入隐性 PPTX XML 回归 |

## P3：DOCX/XLSX 渲染器模块化

| 项目 | 内容 |
|---|---|
| 核心问题 | DOCX/XLSX 目前集中在单文件，后续增强会快速膨胀 |
| 主要任务 | DOCX 拆 `section.py`/`block.py`/`style.py`；XLSX 拆 `sheet.py`/`chart.py`/后续 `conditional.py` |
| 推荐做法 | 先补内部结构测试，再拆模块 |
| 验收标准 | DOCX 测试检查段落/表格/图片结构；XLSX 测试检查 cell/sheet/chart |
| 风险 | 只用文件大小判断生成成功，无法保护重构质量 |

## P4：DOCX/XLSX 功能深度增强

| 项目 | 内容 |
|---|---|
| 核心问题 | 目前更偏“能生成”，还不够“业务可用” |
| 主要任务 | DOCX 增强节、分页、标题、段落、列表、表格、图片；XLSX 增强公式、格式、图表、条件格式 |
| 推荐做法 | 以模板输出质量为目标，逐个补真实业务场景 |
| 验收标准 | 12 个模板在 DOCX/XLSX 输出中具有可读结构和样式；不支持特性有明确降级 |
| 风险 | DOCX 排版和 XLSX 图表 API 差异大，容易出现格式碎片化 |

## P5：Hub 与资源系统完善

| 项目 | 内容 |
|---|---|
| 核心问题 | MCP/AI/Skill provider 目前主要是接口或适配层，缺少完整可测闭环 |
| 主要任务 | 定义 provider 合同；完善 Local provider；增加 fake MCP/AI/Skill provider；完善 cache/fallback |
| 推荐做法 | 先用 fake provider 固化接口，再接真实外部服务 |
| 验收标准 | 无网络测试可通过；资源失败时返回 fallback reason；缓存行为确定可测 |
| 风险 | 过早接真实 API 会让测试不稳定、成本不可控 |

## P6：Pipeline DAG 可靠性

| 项目 | 内容 |
|---|---|
| 核心问题 | Pipeline 有基础结构，但距离声明式 DAG 调度仍有差距 |
| 主要任务 | 拓扑排序、依赖校验、环检测、有界并发、retry/backoff、变量解析、render nodes |
| 推荐做法 | 控制范围，只服务文档生成，不演变成 Airflow 类平台 |
| 验收标准 | 串行 DAG、fan-out/fan-in、retry、cycle detection 都有确定性测试 |
| 风险 | DAG 功能容易过度工程化，需要坚持“三不原则” |

## P7：Store 与可追溯产物

| 项目 | 内容 |
|---|---|
| 核心问题 | Artifact/history store 需要从基础实现升级为可追踪记录 |
| 主要任务 | artifact id、输出元数据、content hash、source hash、run history、输出列表 |
| 推荐做法 | 先本地文件存储，暂不引入数据库 |
| 验收标准 | 每次生成能追踪输入 DSL、输出文件、渲染器、时间和 hash |
| 风险 | Store 设计过重会偏离构建工具定位 |

## P8：布局引擎深化

| 项目 | 内容 |
|---|---|
| 核心问题 | Constraint/Flex/Grid 有骨架，但还不够可靠可用 |
| 主要任务 | 定义 constraint 支持子集；完善 flex direction/gap/justify/align；定义 12/24 栅格 API |
| 推荐做法 | 布局输出统一落到 IRPosition，再交给各 renderer |
| 验收标准 | 同一布局在 PPTX/PDF/HTML 中位置误差可控；无效约束渲染前报错 |
| 风险 | 自研 Cassowary 复杂度高，可能需要引入成熟库 |

## P9：视觉效果与媒体能力

| 项目 | 内容 |
|---|---|
| 核心问题 | OKLCH、Filter、路径文字、视频/音频属于 P2/P3，当前多为骨架或未实现 |
| 主要任务 | OKLCH -> sRGB；duotone/opacity；路径文字支持矩阵；视频/音频 metadata 和 placeholder |
| 推荐做法 | 先定义支持矩阵和降级行为，再做真实嵌入 |
| 验收标准 | 每个效果明确支持哪些 renderer，不支持时如何降级 |
| 风险 | 不同格式能力差异很大，强行统一会导致低质量输出 |

## P10：开发体验、预览与质量门禁

| 项目 | 内容 |
|---|---|
| 核心问题 | 依赖管理、预览、linter、性能基准和视觉检查仍需工程化 |
| 主要任务 | 增加 `pyproject.toml`；HTML 本地 HTTP 预览；DSL linter；benchmark；PDF/HTML/PPTX smoke check |
| 推荐做法 | 先服务开发者本地体验，再接 CI |
| 验收标准 | 新贡献者可按 README 安装并测试；CI 防止生成物和缓存目录误提交 |
| 风险 | 环境差异可能导致浏览器/PDF 视觉测试不稳定 |

## 推荐执行顺序

| 顺序 | 建议 PR 名称 | 覆盖优先级 | 说明 |
|---|---|---|---|
| 1 | `test-fixtures-phase0-cleanup` | P0 | 统一夹具策略，修复 Phase 0，更新状态文档 |
| 2 | `cascade-and-capability-audit` | P1 | 增加 cascade 测试，对齐 renderer capability |
| 3 | `pptx-renderer-extraction` | P2 | 拆 PPTX helper，不做行为变更 |
| 4 | `docx-xlsx-verification-tests` | P3/P4 | 先增强内部结构测试，再推进模块化和功能增强 |
| 5 | `hub-provider-contract` | P5 | 固化 provider 合同和 fake provider 测试 |
| 6 | `pipeline-dag-reliability` | P6 | 补 DAG、retry、cycle detection |
| 7 | `artifact-history-store` | P7 | 完善产物和历史记录 |
| 8 | `layout-engine-subsets` | P8 | 定义并实现 Grid/Flex/Constraint 支持子集 |
| 9 | `visual-effects-support-matrix` | P9 | 明确效果和媒体支持矩阵，先做降级策略 |
| 10 | `developer-experience-quality-gates` | P10 | 依赖、预览、linter、benchmark、CI |

