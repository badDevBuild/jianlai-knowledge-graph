# 任务清单

## 阶段 1: 基础集成 (MVP)

- [x] 1.1 安装依赖 `@antv/f6-wx` 到 `taro-app`
- [x] 1.2 创建适配器 `graph-adapter.ts`: 实现 JSON -> F6 Data 转换逻辑 (含 Ego-centric 过滤)
- [x] 1.3 创建 F6 组件 `F6Graph.tsx`: 封装 Canvas 初始化
- [x] 1.4 实现图谱页 `pages/graph/index.tsx`: 集成组件并加载真实数据
- [x] 1.5 验证: 开发者工具预览，确保点击节点能切换中心

## 阶段 2: 交互优化 (V1.1)

- [x] 2.1 样式优化: 节点根据 PageRank 调整大小，边根据类型着色
- [x] 2.2 实现底部 Filter Bar: 切换关系类型显隐
- [x] 2.3 增加 Loading 状态和错误处理 (数据加载失败时)
- [x] 2.4 视觉重构 (V1.2): 适配全站水墨风 (FilterBar & Loading 样式)

## 阶段 3: 高级特性 (V2.0 - 暂缓)

- [ ] 3.1 实现双击/长按呼出详情 BottomSheet
- [ ] 3.2 实现两点寻路算法
- [ ] 3.3 实现时间轴筛选
