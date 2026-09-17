# 关系图谱实现方案 (AntV F6)

## 背景

《剑来》人物关系极其复杂，现有的 ForceGraph Web 实现无法在小程序端运行（Canvas/DOM 限制）。移动端屏幕尺寸限制了展示数百个节点的能力。
为了提供流畅的用户体验，我们需要基于 **"渐进式披露" (Progressive Disclosure)** 原则，在 Taro 小程序中实现高性能的交互式关系图谱。

## 目标

1.  **移动端原生体验**：在微信小程序中流畅渲染人物关系图。
2.  **以我为中心 (Ego-Centric)**：点击人物切换视角，避免信息过载。
3.  **高性能渲染**：使用 AntV F6 引擎，支持手势缩放、平移。
4.  **清晰的关系展示**：支持筛选器（师承、敌对等）和路径发现。

## 核心交互设计

1.  **初始状态**：展示核心人物（如“陈平安”）的一级关系网。
2.  **交互动作**：
    *   **单击**：节点移动到屏幕中心，动态加载其一级关系，重组视图。
    *   **双击/长按**：呼出半屏详情卡片。
3.  **筛选器**：底部 Chips 切换关系类型（如只看“问剑”）。
4.  **寻路 (V1.1)**：输入起终点，高亮最短路径。

## 技术选型

*   **可视化引擎**：AntV F6 (专门针对移动端/小程序的图可视化库)
*   **布局算法**：Force Directed Layout (力导向图)
*   **前端框架**：Taro + React

## 实施阶段

> [!IMPORTANT]
> 本提案采用 MVP 策略，优先交付基础体验。

### Phase 1: MVP (核心体验)
*   集成 AntV F6 到 Taro。
*   实现 "以我为中心" 的力导向图。
*   实现单击重置中心 (Re-center) 交互。
*   数据源：复用现有的 `relations_clean.json` 并进行格式转换。

### Phase 2: 增强交互 (V1.1)
*   增加关系筛选器 (Filter)。
*   增加双击/长按呼出详情卡片。
*   优化节点样式（头像裁切、不同身份颜色）。

### Phase 3: 高级功能 (V2.0, Future)
*   寻路模式 (Pathfinding)。
*   语义缩放 (Semantic Zooming - 势力视图)。
*   时间轴回忆 (Timeline Slider)。

## 变更范围

### 新增文件
*   `taro-app/src/pages/graph/index.tsx` (替换占位页)
*   `taro-app/src/components/Graph/` (封装 F6 组件)
*   `taro-app/src/utils/graph-adapter.ts` (数据转换逻辑)

### 数据流
现有 `relations_clean.json` -> 客户端 Fetch -> Adapter 转换为 F6 Graph Data -> 渲染。
