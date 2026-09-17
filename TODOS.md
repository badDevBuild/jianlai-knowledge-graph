# TODOS

## P2 — 重要但不紧急

### 为数据工具函数补充单元测试
- **What**: 为 normalizers (character_merger, cultivation_normalizer 等) 和 build_knowledge_base.py 补充 pytest 单元测试
- **Why**: 零测试是最大的技术债务。数据管道修改后无法验证正确性，只能靠人工检查
- **Effort**: M (human: ~1周 / CC: ~30分钟)
- **Depends on**: 无

### 卡片生成器通用化重构
- **What**: 从 cardGenerator.ts 和 quoteCardGenerator.ts 提取 generateEntityCard 通用函数
- **Why**: 新增法宝/势力/对比卡片后会有 5 个生成器，代码重复度高。通用化后新增卡片类型只需传参
- **Effort**: S (human: ~2天 / CC: ~15分钟)
- **Depends on**: 完成分享卡片全覆盖 (#4) 后再重构

## P3 — 可延后

### 深度分析 SDK 接入
- **What**: 接入第三方分析 SDK (如 Sensors Data 小程序 SDK) 替代 wx.reportAnalytics
- **Why**: wx.reportAnalytics 只提供聚合计数，无法做漏斗分析（分享→扫码→打开的归因链）
- **Effort**: M (human: ~1周 / CC: ~1小时)
- **Depends on**: 先用 wx.reportAnalytics 跑一段时间，确认确实需要深度分析
