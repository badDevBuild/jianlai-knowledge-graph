# Taro 迁移架构设计

## 设计决策

### 1. 框架选择：Taro 3.x + React

**理由**：
- 现有代码基于 React，迁移成本最低
- Taro 3.x 对 React Hooks 支持完善
- 一套代码可输出小程序 + H5

**替代方案（未选用）**：
- uni-app：需学习 Vue，成本高
- 原生小程序：无法复用代码，工作量大

---

### 2. 数据层复用策略

现有 H5 通过 `fetch /jianlai/data/*.json` 获取数据。

**Taro 方案**：使用 `Taro.request` 替代 `fetch`，API 完全兼容。

```typescript
// H5 原代码
const response = await fetch('/jianlai/data/characters_top.json');

// Taro 迁移后
const response = await Taro.request({
  url: 'https://shushu.host/jianlai/data/characters_top.json'
});
```

---

### 3. 样式迁移策略

| H5 方案 | Taro 方案 |
|---------|----------|
| TailwindCSS | SCSS + 手写样式 或 NutUI 组件 |
| `className="..."` | `className="..."` (兼容) |

**处理方式**：
- 简单页面：手动转换 Tailwind 为 SCSS
- 复杂页面：使用 NutUI 组件简化

---

### 4. 路由迁移

| H5 (React Router) | Taro |
|-------------------|------|
| `<Route path="/character/:id">` | `app.config.ts` + `Taro.navigateTo` |
| `useNavigate()` | `Taro.navigateTo()` |
| `useParams()` | `getCurrentInstance().router.params` |

---

### 5. 组件迁移对照

| H5 组件 | Taro 组件 |
|---------|----------|
| `<div>` | `<View>` |
| `<span>` | `<Text>` |
| `<img>` | `<Image>` |
| `<button onClick>` | `<Button onClick>` |
| `<input>` | `<Input>` |

---

## 目录结构设计

```
taro-app/
├── src/
│   ├── app.config.ts          # 小程序配置
│   ├── app.tsx                 # 入口
│   ├── app.scss
│   ├── pages/
│   │   ├── index/              # 首页
│   │   ├── characters/         # 人物列表
│   │   ├── character-detail/   # 人物详情
│   │   ├── factions/           # 宗派列表
│   │   ├── artifacts/          # 法宝列表
│   │   ├── locations/          # 地点列表
│   │   ├── search/             # 搜索
│   │   └── quotes/             # 语录
│   ├── components/
│   │   ├── Navigation/         # 底部导航
│   │   └── CharacterCard/      # 人物卡片
│   └── data/
│       ├── useData.ts          # 数据 Hooks
│       └── dataTypes.ts        # 类型定义
├── project.config.json
└── package.json
```

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| Canvas 图谱不兼容 | 第一阶段不迁移，后续使用 echarts-for-taro |
| 样式差异 | 逐页面调试，参考小程序设计规范 |
| 编译问题 | 使用 Taro 官方模板，减少自定义配置 |
