# 剑来小程序数据架构与运行逻辑说明书 (V3版本编撰)

本文档整理了在近期 V3 版本头像及 UGC 功能更新中，总结出的小程序当前核心运行逻辑、数据生命周期以及防坑指南。供后续维护与二次开发参考。

## 1. 核心架构与数据流转路径

小程序的绝大部分数据（人物志、首页榜单、梗概等）属于**强依赖预编译的静态资源**，而非实时拉取数据库。

整体生命周期为：**本地源数据 -> 构建脚本处理 -> 本地产物库 -> Rysnc 上云 -> Nginx 静态托管 -> 小程序端拉取与强缓存**。

### 1.1 本地源数据 (Source of Truth)
- `/data/src/`: 存放最原始的结构化录入数据（如 `merged_jianlai.json` 等原始定义集合）。
- `/data/build/character_images/`: 大量由 AI 等方式预先生成的历史版本高清静态头像大库。
- `/taro-app/public/data/img/avatars/`: UGC 系统审核通过后，落地保存在此的真实用户自定义头像图片。

### 1.2 构建流 (Build Scripts)
- **`/scripts/build_frontend_data.py`**：核心打薄及关联脚本。
  - 读取源 JSON 数据。
  - 为所有几千名角色裁切所需的显示字段。
  - **核心：执行“头像地址判定与分配”逻辑（详见第二节）。**
  - 在 `/data/dist/chars/` 下生成每一个角色的独立详情 JSON 文件（如 `丁婴.json`）。
  - 生成汇总版的 `/data/dist/characters_lite.json`。
- **`/scripts/generate_top_characters.py`**：首页榜单脚本。
  - 依赖上述的 `characters_lite.json`，根据特定排序逻辑，抽取出首页常驻/热门角色，输出为 `/data/dist/characters_top.json`。

### 1.3 部署层 (Deployment)
无论改动了任何图片、或者是通过后台通过了任何 UGC 请求。如果不触发编译并使用 `rsync` 同步，线上绝对不会生效：
```bash
# 全量同步打包产物至服务器Nginx静态目录：
# 1. 详情页单体人物资料
rsync -avz --delete data/dist/chars/ ubuntu@shushu.host:/var/www/jianlai/data/chars/
# 2. 核心大表与首页榜单
rsync -avz data/dist/*.json ubuntu@shushu.host:/var/www/jianlai/data/
```
*注：由于 Nginx 的 `markdown-ssr.conf` 配置，`/jianlai/data/` 目录将直接由服务器的 `/var/www/jianlai/data/` 提供静态文件响应服务。*

---

## 2. 三重坠落式头像路由策略 (核心避坑区)

为了保证展示优先级（UGC 定制 > 官方高质生成图 > 前端古董自带图），构建脚本 `build_frontend_data.py` 严格遵守以下串行短路判定逻辑：

### 第一重：UGC 本地物理定格 (Highest Priority)
当循环诊断某个人物时，去 `taro-app/public/data/img/avatars/` 寻访是否存在该名字命名的文件（如 `裴钱.jpg`, `老秀才.png`）。
- **如果存在**：说明用户上传并已通过审核，该人物在生成的 JSON 中取得绝对路径：`https://shushu.host/jianlai/img/avatars/{name}.{ext}`。
- *此路径由 Nginx 在服务器层代理读取真实产生的 UGC 图。*

### 第二重：V3 历史生成库图底 (Fallback 1)
当不存在 UGC图 时，引擎去探测老版本的精美图库产金矿 `/data/dist/img/avatars/` (由 `data/build/character_images/` 拷入)。
- **如果存在**：说明有系统批量生成的画作兜底。JSON 取得绝对路径：`https://shushu.host/jianlai/data/img/avatars/{name}.{ext}`。

### 第三重：小程序客户端内置保底 (Fallback 2 - The Abyss)
如果一、二重都未命中物理图片，脚本**必须强制将变量清空 `avatar_url = ""`**（⚠️不可漏除，否则 Python 的循环变量污染会让后续所有人强制戴上前一个人的面具！）。
- 将 `""` 下发到 JSON 给客户端后。
- 客户端在 `/taro-app/src/data/useData.ts` 中感知到无外链传入，自动启用 `ASSET_BASE/LOCAL_AVATARS` 写死的备用旧字典，或展示姓氏纯色单字头像兜底。

---

## 3. 前端客户端缓存暴政 (为什么更新了没反应？)

在小程序源码 `/taro-app/src/data/useData.ts` 内，挂载了名为 `CACHE_DURATION` 的极强生命周期常数：
```typescript
const CACHE_KEY_PREFIX = 'jianlai_data_v3_';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 强无敌的 24 小时本地冷存
```

### 3.1 缓存逻辑
在任意一处调用 `loadData`（例如请求 `characters_top.json` 或单体 `裴钱.json`），微信小程序会优先截获：
1. 先查阅微信 Storage 是否存在该 Key。
2. 一旦存在，且未超过 24 小时，**坚决不发真实的 HTTPS 网络请求**，直接把本地陈旧数据丢给 UI 渲染。
3. 也就是：只要没满 24 小时，你在服务器把大天说破，手机端也看不见新头像！

### 3.2 破除缓存之法
- **超级测试环境**：微信开发者工具中，反复点击顶部工具栏的“清缓存 -> 全部清除”。
- **C端真实用户**：没有任何静默刷新办法，除非用户在微信任务栏将“剑来”小程序**长按并删除**，再重新搜索进入，彻底击杀 Storage 存储空间。

### 3.3 迭代建议
如果未来需要在 UGC 审核通过后“立等可取”可见反馈，建议重构 `useData.ts`：
- 修改为依靠服务器返回 Etag/Last-Modified 头的 304 协商缓存。
- 或在 HTTP URL 尾巴追加时间戳 `?v=2026xxxx` 打爆缓存。
- 或在小程序内部为热点数据（如详情本身）取消或极大程度缩短这 24 小时的强缓存策略。

---
*文档编制依据：2026.02 全服头像同化灾难的故障解剖与抢救复盘记录。*
