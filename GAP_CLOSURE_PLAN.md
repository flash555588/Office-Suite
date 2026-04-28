# Office Suite 4.0 — 差距收敛后续计划

> 创建日期：2026-04-28  
> 依据：`origin/main` 中的 `GAP_ANALYSIS_REPORT.md`  
> 范围：仅制定计划，不做功能实现。

## 1. 当前判断

差距报告显示：项目已经具备较完整的 DSL -> IR -> 多格式渲染主链路，但实现深度不均衡。

主要现状：

- 核心编译链路已经存在，PPTX/DOCX/XLSX/PDF/HTML 均有渲染器。
- 报告记录 Phase 0 因缺少 `hello_world.yml` 失败。
- P0 功能基本可用，但样式级联位置、渲染器能力声明、模块边界仍需统一。
- P1/P2 功能中有不少属于“骨架可见，但能力未充分落地”。
- Hub、Pipeline、Store、渲染器模块化是当前最大的架构差距。

上下文注意：

当前工作分支此前已经提交删除了：

- `tests/hello_world.yml`
- `tests/test_pagination.yml`
- `world_book_day.yml`

因此，后续不能简单按报告直接恢复 `hello_world.yml`。第一步应先决定这些 YAML 文件到底是测试夹具、示例文件，还是已经废弃的临时样例。

## 2. 总体原则

1. 先稳定测试和夹具，再扩展功能。
2. 优先补齐 P0 的一致性问题，不急着铺开 P2/P3。
3. 渲染器能力声明必须和真实行为一致，不能把占位符伪装成完整支持。
4. 每个阶段都应能以测试、演示输出或结构检查验收。
5. 外部资源、AI、MCP 等能力应先用 fake provider 固化接口，再接真实服务。
6. 不做一次性大重构，所有拆分都应保持现有公开 import 路径兼容。

## 3. 阶段 A：基线对齐

预计时间：1-2 天

目标：让当前分支、差距报告、测试夹具和状态文档保持一致。

任务：

- 确认后续开发基准分支：
  - `main`
  - `fix/pptx-slide-height-16x9`
  - `codex-improve-html-pdf-renderers`
- 明确三个被删除 YAML 文件的归属：
  - 如果是测试夹具，恢复或改写测试。
  - 如果是示例文件，移动到 `examples/`。
  - 如果是废弃样例，保留删除提交。
- 重构 Phase 0 测试策略：
  - 推荐使用内联 YAML 字符串做最小闭环测试。
  - 大型 demo 不应作为单元测试依赖。
- 重新运行完整测试，记录真实测试数量。
- 更新 `STATUS.md`，消除 140、179、180、390 等统计口径不一致的问题。

验收标准：

- 干净 checkout 后 `pytest -q` 通过。
- Phase 0 不依赖含糊的根目录样例文件。
- `STATUS.md` 中测试数量与实际运行结果一致。

风险：

- 直接恢复 YAML 可能和已有删除提交冲突。
- 继续依赖大型 YAML 文件会让测试维护成本升高。

推荐决策：

- Phase 0 使用内联最小 YAML。
- 有保留价值的大 demo 移到 `examples/`。
- 根目录不再放测试依赖型样例文件。

## 4. 阶段 B：P0 架构补强

预计时间：3-5 天

目标：补齐 MVP 层面的架构一致性。

任务：

- 样式级联梳理：
  - 对比当前 `office_suite/ir/cascade.py` 与设计中的 `theme -> document -> slide -> element -> inline`。
  - 决定是否新增 `office_suite/engine/style/cascade.py` 作为样式引擎入口。
  - 如果迁移模块，保留旧 import 的兼容层。
- 渲染器能力声明审计：
  - 检查 PPTX/DOCX/XLSX/PDF/HTML 的 `RendererCapability`。
  - 将真实支持、降级支持、占位符支持区分清楚。
  - 为 fallback 行为补测试。
- 坐标与尺寸一致性审计：
  - 确认 PPTX、PDF、HTML、IR 编译器都使用一致的 16:9 尺寸。
  - 如果重复常量继续增多，再考虑抽共享常量模块。
- 文档同步：
  - README 中命令应和当前可用环境一致。
  - 增加简短的渲染器支持矩阵。

验收标准：

- P0 特性矩阵不再出现“部分支持但无说明”的状态。
- 样式级联覆盖 theme、document、命名样式、元素样式、inline override。
- 每个渲染器至少有一个支持能力测试和一个降级能力测试。

## 5. 阶段 C：渲染器模块化

预计时间：1-2 周

目标：拆分大文件，但不改变外部行为。

推荐顺序：

1. PPTX
2. DOCX
3. XLSX
4. HTML/PDF 样式辅助模块

PPTX 任务：

- 将幻灯片创建、背景、布局逻辑拆到 `renderer/pptx/slide.py`。
- 将形状、文本、图片、表格、图表的稳定辅助逻辑逐步拆分。
- 仅在切换效果语义明确后新增 `transition.py`。
- 保持 `deck.py` 作为现有入口。

DOCX 任务：

- 新增 `renderer/docx/section.py` 管理节、分页、页面设置。
- 新增 `renderer/docx/block.py` 管理段落、表格、图片、形状降级。
- 新增 `renderer/docx/style.py` 管理 Word 样式转换。
- 测试应检查 DOCX 内部结构，而不只是文件大小。

XLSX 任务：

- 新增 `renderer/xlsx/sheet.py` 管理 sheet 创建和表格写入。
- 新增 `renderer/xlsx/chart.py` 管理 Excel 图表构建。
- 在条件格式 DSL 明确后新增 `conditional.py`。
- 测试应检查单元格值、图表对象和 sheet 名称。

HTML/PDF 任务：

- HTML 中 CSS 辅助逻辑稳定后再抽 `renderer/html/css.py`。
- PDF 中字体 fallback 和字体嵌入规则明确后再抽 `renderer/pdf/font.py`。

验收标准：

- 公开 renderer 类 import 路径不变。
- 抽文件 PR 不混入功能行为变更。
- 每次拆分前后测试结果一致。

## 6. 阶段 D：DOCX/XLSX 功能深度增强

预计时间：1-2 周

目标：让 DOCX/XLSX 从“能生成文件”提升到“内容结构可用、样式可控”。

DOCX 优先级：

- 真实 section/page 处理：
  - 分页
  - 标题层级
  - 页边距
  - 文档级样式
- 块级渲染增强：
  - 段落间距
  - 列表
  - 表格样式
  - 图片尺寸
- 降级策略：
  - 图表降级为图片或结构化表格。
  - WordArt 降级为普通样式文本。
  - 动画忽略但记录 warning。

XLSX 优先级：

- 数据模型映射：
  - 表格 range
  - 数值类型
  - 公式
  - 数字格式
- 图表增强：
  - bar/column/line/pie 一致支持。
  - 坐标轴、系列名、标题。
- 条件格式：
  - 色阶
  - 数据条
  - 阈值高亮

验收标准：

- 测试检查生成文档内部结构。
- 模板在 DOCX/XLSX 中输出有实际信息价值。
- 不支持的视觉能力有明确、可用的降级结果。

## 7. 阶段 E：Hub、资源与 Store 完善

预计时间：2-3 周

目标：把 provider 骨架推进为可靠的资源流。

Hub 任务：

- 明确 provider 合同：
  - 输入 schema
  - 返回结构
  - cache key
  - fallback reason
  - retry 行为
- Local provider：
  - 相对路径基于 DSL 文件目录解析。
  - MIME/type 检测。
  - 图片有效性检查。
- MCP provider：
  - 明确外部 caller 注册方式。
  - 使用 fake MCP caller 做确定性测试。
- AI provider：
  - 真实外部 AI 保持可选。
  - 用 fake caller 测试图片/文本生成流程。
- Skill provider：
  - 定义调用接口。
  - 增加一个确定性测试 provider。

Store 任务：

- Artifact store：
  - 稳定 artifact id。
  - 输出文件元数据。
  - 内容 hash。
- History store：
  - 运行记录。
  - 源 DSL hash。
  - 输出物列表。

验收标准：

- 本地图片缺失不会中断生成，并记录 fallback reason。
- 缓存命中行为可重复测试。
- MCP/AI fake provider 不依赖网络即可跑通。

## 8. 阶段 F：Pipeline DAG 可靠性

预计时间：1-2 周

目标：让 Pipeline 真正符合“文档生成 DAG”，但不演变成通用工作流平台。

任务：

- Scheduler：
  - 拓扑排序
  - 依赖校验
  - 环检测
  - 有界并发
- Retry：
  - 重试次数
  - backoff
  - 可重试/不可重试错误区分
- Context：
  - 变量解析
  - artifact 传递
  - 结构化节点输出
- Pipeline parser：
  - 明确 YAML schema
  - 提供可读错误
- Render nodes：
  - `to_pptx`
  - `to_docx`
  - `to_xlsx`
  - `to_pdf`
  - `to_html`

验收标准：

- 3 节点串行 pipeline 通过。
- fan-out/fan-in pipeline 通过。
- retry 用“先失败后成功”的确定性节点覆盖。
- 环依赖能输出可读错误。

## 9. 阶段 G：布局引擎深化

预计时间：2-4 周

目标：让布局引擎可预测、可测试、跨渲染器一致。

约束布局：

- 决定保留自研简化 solver，还是接入成熟 Cassowary 实现。
- 明确支持的约束子集。
- 测试覆盖等宽、对齐、间距、min/max。

Flex 布局：

- 明确支持子集：
  - direction
  - gap
  - justify
  - align
  - wrap 可后置
- 增加确定性布局快照。

Grid 布局：

- 定义 12/24 列 API。
- 支持 gutter 和 column span。
- 覆盖报表、仪表盘等常见布局。

验收标准：

- 布局输出为 renderer-independent IR positions。
- PPTX/PDF/HTML 输出位置在允许误差内一致。
- 无效约束在渲染前失败。

## 10. 阶段 H：色彩、效果与媒体

预计时间：2-4 周

目标：核心渲染稳定后，再推进高级视觉能力。

OKLCH：

- 实现 OKLCH -> sRGB 转换。
- 定义超出色域时的 fallback。
- 增加对比度辅助函数和测试。

Filter：

- 先支持 duotone 和 opacity。
- 图片预处理优先放在 Hub 或 media engine 中。
- 渲染器不支持时记录明确 fallback。

路径文字：

- 明确支持矩阵：
  - PPTX：原生或 XML 注入。
  - HTML：SVG。
  - PDF：路径文字近似绘制。
  - DOCX：降级。

视频/音频：

- 作为 P2/P3 后置。
- 先定义 metadata 和 placeholder 行为。
- 只在确实支持的渲染器中做真实嵌入。

验收标准：

- 每个视觉效果都有支持矩阵。
- 不支持的输出格式有明确、文档化的降级。

## 11. 阶段 I：预览与开发体验

预计时间：1-2 周

目标：降低生成、检查和调试成本。

任务：

- 改进 `tools/preview.py`：
  - 通过本地 HTTP 服务预览 HTML。
  - 可选自动打开浏览器。
  - 不依赖 `file://`。
- 改进 `tools/linter.py`：
  - 缺失 position。
  - 渲染器不支持的特性。
  - 无效 data_ref。
  - 对比度 warning。
- 改进 `tools/generate.py`：
  - 更可靠的路径解析。
  - 清晰输出路径。
  - 更好的错误信息。
- 增加 `pyproject.toml` 或依赖清单。

验收标准：

- 新贡献者能按 README 安装依赖并运行测试。
- HTML 预览通过本地 HTTP 打开。
- linter 能在渲染前发现常见 DSL 错误。

## 12. 阶段 J：性能与质量门禁

预计时间：持续进行，首轮 3-5 天

任务：

- 定义 benchmark 夹具：
  - 10 页 PPT
  - 100 页 PPT
  - 图片密集文档
  - 表格密集工作簿
- 记录指标：
  - 渲染时间
  - 输出文件大小
  - 内存使用，若可行
- 增加视觉 smoke check：
  - PDF 渲染为 PNG。
  - HTML 浏览器截图。
  - PPTX 结构检查。
- 增加 CI 门禁：
  - 单元测试
  - 关键集成测试
  - 防止生成物和缓存目录误提交

验收标准：

- 100 页 PPTX benchmark 可重复运行。
- PDF/HTML smoke artifacts 可本地生成。
- CI 能拦截误提交输出文件和缓存目录。

## 13. 推荐里程碑

里程碑 1：基线与 P0 清理

- 统一测试夹具策略。
- 修复或替换 Phase 0 失败点。
- 同步 `STATUS.md`。
- 增加样式级联测试。

里程碑 2：渲染器可靠性

- PPTX 模块化拆分。
- DOCX/XLSX 内部结构测试增强。
- 必要时抽取稳定的样式/图表辅助模块。

里程碑 3：资源与 Pipeline

- 完成 Hub fake provider 流程。
- 增加 artifact/history store 持久化。
- 覆盖串行、并行、retry、环检测 pipeline 测试。

里程碑 4：布局引擎

- 完成 grid/flex 支持子集。
- 决定 constraint solver 方案。
- 增加 renderer-independent 布局测试。

里程碑 5：P2 视觉与媒体能力

- OKLCH 转换。
- duotone/filter 管线。
- 路径文字支持矩阵和首个实现。
- 视频/音频 metadata 与 fallback。

## 14. 跟踪清单

- [ ] 确认后续 PR 的基准分支。
- [ ] 决定 YAML 样例/夹具策略。
- [ ] 让 Phase 0 测试确定性通过。
- [ ] 同步 `STATUS.md` 与实际测试数量。
- [ ] 审计 renderer capability。
- [ ] 增加 cascade 测试。
- [ ] 规划 PPTX 拆分 PR。
- [ ] 规划 DOCX 拆分 PR。
- [ ] 规划 XLSX 拆分 PR。
- [ ] 定义 Hub provider 合同。
- [ ] 定义 Pipeline DAG schema。
- [ ] 定义布局引擎支持子集。
- [ ] 增加依赖清单。
- [ ] 增加视觉 smoke-check 流程。

## 15. 下个 Sprint 不做的事

- 不做 WYSIWYG 编辑器。
- 不在 fake provider 合同稳定前接真实外部 AI/MCP 网络调用。
- 不在降级策略明确前实现视频/音频嵌入。
- 不把所有渲染器一次性拆成大量文件。
- 不在没有迁移说明和测试的情况下改 DSL 语法。

## 16. 推荐 PR 顺序

1. `test-fixtures-phase0-cleanup`
   - 明确夹具策略。
   - 修复 Phase 0。
   - 更新状态文档。

2. `cascade-and-capability-audit`
   - 增加 cascade 测试。
   - 对齐能力声明和真实渲染行为。

3. `pptx-renderer-extraction`
   - 在保持 `deck.py` facade 的前提下拆分 PPTX helper。
   - 不做行为变更。

4. `docx-xlsx-verification-tests`
   - 强化生成文档内部结构测试。
   - 为 DOCX/XLSX 模块化做准备。

5. `hub-provider-contract`
   - 固化 provider 接口。
   - 增加确定性 fake provider 测试。

