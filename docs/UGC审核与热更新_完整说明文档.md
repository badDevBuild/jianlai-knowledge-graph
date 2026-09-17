# 剑来百科 - UGC与热更新全链路手册

本文档记录了基于 C/S 架构与大模型协同的《剑来》百科全书 UGC (用户生成内容) 审核机制，以及服务器端零停机热更加载的部署细节。

---

## 一、 系统架构概览

新版架构彻底弃用了繁重的 Git CI/CD 流程，改为以下高能效链路：

1. **终端数据采集 (Taro 小程序)**：
   用户在词条详情页对应版块点击“纠错/补充”，前端收集 `entryName`、`field` 及用户文本/图片，通过 HTTPS POST 发往服务器的 FastAPI 接管口。

2. **云端收集与待命 (服务器 API 层)**：
   运行在 `ubuntu@shushu.host` 上的 `/var/www/jianlai-api` 会将所有数据入库至本地 SQLite (`ugc.db`)，状态标记为 `pending`。图片存储至 `data/images`。

3. **本地决策大脑 (终端 Python 审核)**：
   管理员在本地 Mac 执行 `review_ugc.py`。该脚本通过鉴权接口远程拉取 `pending` 记录。
   - **涉及文字**：向大模型 (如 Kimi/ DeepSeek) 下发 Prompt，结合原词条上下文进行丝滑的语义融合与整理。
   - **涉及鉴黄/纯图**：绕过大模型，管理员直接审批。
   
4. **瞬间反推与热更新 (增量上传机制)**：
   在管理员敲击 `Y` 批准所有单条数据后，脚本在本地静默进行构建 (Build)，打包最新的几条变更 JSON（极小体积）。然后利用服务器的 `/admin/upload_data` 接口，用 cURL 将被更改的词条文件精准拍到线上 `/var/www/jianlai/` 前端资源目录下。

**效果：从用户提达到管理员同意修改，全链路闭环，CDN 实时生效体验不足 10 秒。**

---

## 二、 服务端部署清单 (参考)

在您之后如果有迁服或灾备的需求，请按以下步骤在一台全新的 Ubuntu 服务器上拉起整个后勤体系：

### 1. 资源就位
```bash
sudo mkdir -p /var/www/jianlai-api/data/images
sudo chown -R ubuntu:ubuntu /var/www/jianlai-api
# 将本地的 api_ugc.py 传入 /var/www/jianlai-api/
cd /var/www/jianlai-api
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-multipart
```

### 2. 神殿骑士 (Systemd 守护进程)
新增文件：`/etc/systemd/system/jianlai-api.service`
```ini
[Unit]
Description=Jianlai UGC API Server
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/jianlai-api
Environment=PATH=/var/www/jianlai-api/venv/bin:/usr/bin:/usr/local/bin
Environment=DEPLOY_DIR=/var/www/jianlai
EnvironmentFile=/etc/jianlai-api.env
ExecStart=/var/www/jianlai-api/venv/bin/uvicorn api_ugc:app --host 127.0.0.1 --port 8011 --workers 2

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
管理员 Token 必须在仓库外生成和保存，例如在服务器上执行
`openssl rand -hex 32`，将结果写入仅服务账号可读的
`/etc/jianlai-api.env`，格式为 `ADMIN_TOKEN=<随机值>`，并将文件权限设置为
`0600`。不要把真实 Token 写入本文档、Shell 历史或任何 Git 文件。

启动命令：`sudo systemctl daemon-reload && sudo systemctl enable --now jianlai-api`

### 3. Nginx 流量网关
在您的主配置中拦截以 `/jianlai/api/` 开头的流量池，转发内网 8011 端口，并开放文件限制。
```nginx
location /jianlai/api/ {
    proxy_pass http://127.0.0.1:8011;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    client_max_body_size 50m; # 允许大图通过
}
```

---

## 三、 日常审核人员操作指引

作为大权在握的审核官，您唯一需要做的，是在本地任意拉取了仓库代码的终端下执行：

```bash
# 前置环境变量准备；敏感值从密码管理器或本机私密配置读取
export UGC_API_URL="https://shushu.host/jianlai/api/ugc"
export ADMIN_TOKEN
export OPENAI_API_KEY

# 开启审阅流程
python scripts/review_ugc.py
```

### 审批快捷键指南
- `Y` (接受)：合并内容；如果是文字，调用 AI，生成最佳文本；随后进入最终发布序列。
- `N` (拒绝)：该条意见被标记废弃。
- `S` (跳过)：暂时挂起，以后再议。
- `Q` (退出)：主动结束本次批阅，**所有被您 Y 过的词条将在按下 Q 后启动静默重编译，5秒后完成全网云端热发布。**
