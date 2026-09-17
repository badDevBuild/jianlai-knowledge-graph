# 迁移至 Taro 原生小程序

## 背景

现有的《剑来光阴》采用 `web-view` 嵌入 H5 的方案，但**个人类型小程序不支持 web-view 组件**，导致无法正常运行。
为解决此限制，需要将现有 React H5 应用迁移至 **Taro 跨端框架**，生成原生微信小程序。

## 目标

1. 使用 Taro 框架重写前端应用
2. 保留现有数据 API（直接 fetch 服务器 JSON 文件）
3. 生成原生微信小程序，绕过 web-view 限制
4. 可选：同时输出 H5 版本（一套代码多端运行）

## 用户审核项

> [!IMPORTANT]
> **技术选型**：选用 Taro + React，保留现有 React 代码风格，降低学习成本。

### 决策确认

| 项目 | 选择 | 说明 |
|-----|------|------|
| **框架** | Taro 3.x | 支持 React 语法 |
| **UI 库** | NutUI (可选) | Taro 官方推荐 |
| **样式** | SCSS | 类似现有 CSS，易迁移 |
| **数据层** | 复用现有 JSON API | 无需后端改造 |

---

## 技术方案

### 架构对比

| 方案 | 现有 (web-view) | 新方案 (Taro) |
|------|----------------|---------------|
| 运行方式 | H5 嵌入小程序 | 原生小程序 |
| 个人小程序 | ❌ 不支持 | ✅ 支持 |
| 性能 | 受限于 WebView | 原生性能 |
| 代码复用 | 100% | ~70% (需适配) |

### 迁移范围

| 页面 | 原文件 | Taro 对应 |
|------|--------|----------|
| 首页 | `Home.tsx` | `pages/index/index.tsx` |
| 人物列表 | `Characters.tsx` | `pages/characters/index.tsx` |
| 人物详情 | `Characters.tsx` | `pages/character-detail/index.tsx` |
| 宗派列表 | `Compendium.tsx` | `pages/factions/index.tsx` |
| 法宝列表 | `Compendium.tsx` | `pages/artifacts/index.tsx` |
| 地点列表 | `Compendium.tsx` | `pages/locations/index.tsx` |
| 搜索 | `Search.tsx` | `pages/search/index.tsx` |
| 语录 | `Lore.tsx` | `pages/quotes/index.tsx` |
| 时间线 | `Lore.tsx` | `pages/timeline/index.tsx` |

### 不迁移的功能

| 功能 | 原因 |
|------|------|
| 关系图谱 (ForceGraph) | 依赖 Canvas 库，小程序兼容性差，后续支持 |
| 世界地图 | 同上 |

---

## 验证计划

1. **开发阶段**：Taro 开发者工具预览
2. **真机测试**：扫码测试核心页面
3. **功能验收**：首页人物展示、列表页面、详情页面正常
4. **发布上线**：提交微信审核

---

## 变更范围

### 新增目录

| 目录 | 说明 |
|------|------|
| `taro-app/` | Taro 项目根目录 |
| `taro-app/src/pages/` | 页面文件 |
| `taro-app/src/components/` | 公共组件 |
| `taro-app/src/data/` | 数据 Hooks (从 H5 迁移) |

### 废弃目录

| 目录 | 说明 |
|------|------|
| `miniprogram/` | 原 web-view 壳项目，迁移完成后移除 |
