# 技术设计：AntV F6 关系图谱

## 架构概览

在 Taro 小程序环境中使用 `@antv/f6-wx` 进行渲染。由于小程序 Canvas 机制的特殊性，需要处理好 Canvas 宽高的动态获取和事件桥接。

## 数据结构转换

现有数据 (`relations_clean.json`):
```json
{
  "nodes": [{"id": "陈平安", "val": 10}, ...],
  "links": [{"source": "陈平安", "target": "宁姚", "label": "情侣"}, ...]
}
```

AntV F6 需要的数据格式类似，但我们需要在前端进行 **Ego-Centric 过滤**。

### Ego-Centric 算法

为了避免渲染数千个节点，前端应维护一份 Full Graph Data，但只传递 Sub Graph 给渲染引擎。

1.  **State**: `centerNodeId` (默认为 "陈平安")
2.  **Filter Logic**:
    *   找到 `centerNodeId`。
    *   找到所有与 `centerNodeId` 无向连接的 Neighbors。
    *   (可选 Phase 2) 找到 Neighbors 之间的互联关系。
    *   生成包含 Center + Neighbors 的子图数据。
3.  **Update**: 当用户点击 Node B，将 `centerNodeId` 更新为 B，重复上述步骤，并调用 `graph.changeData(newSubGraph)`。

## 组件设计

### `GraphPage` (Smart Component)
*   负责 Fetch 全量 JSON 数据。
*   管理 `centerId`、`filters` 状态。
*   执行子图筛选算法。
*   渲染 UI 控件（底部 Filter Bar，顶部 Search Bar）。

### `F6Canvas` (Dumb Component)
*   封装 F6 初始化逻辑。
*   接收 `data` (SubGraph)。
*   处理 F6 事件 (`node:tap`) 并回调父组件。
*   处理 Canvas 生命周期 (Mount/Unmount)。

## 交互细节

### 点击重定位 (Re-center)
当点击节点时，F6 默认会拖拽节点。我们需要区分“拖拽”和“点击”。
*   监听 `node:click` 或 `node:tap`。
*   动画过渡：F6 支持 `graph.focusItem(item, true)` 平滑移动视角，但如果是数据发生变化（换了中心），建议使用 `graph.changeData()` 配合 `layout.execute()`。为了体验平滑，可以先 focus 到新节点，然后 fade out 旧图，fade in 新图。**MVP 建议直接 changeData 并重新布局，简单直接。**

### 样式映射
*   **节点大小**：基于 PageRank 或 连接数 (Degree) 映射 `size`。
*   **连线颜色**：基于 `label` (如 "师徒", "死敌") 映射 `stroke`。
*   **头像**：F6 支持 `Image` 类型的节点，可以使用人物头像 URL。

## 性能考虑 (Performance)

*   **节点数量控制**：Ego-centric 模式下，单屏节点通常 < 50 个，性能完全无压力。
*   **布局计算**：力导向布局计算量较大，F6 支持 WebWorker 布局（小程序中可能有限制，视情况降级为同步布局或 F6 内置的优化布局）。
*   **资源加载**：首次进入需要加载 `relations_clean.json` (约 250KB)，需显示 Loading 状态。
