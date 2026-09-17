# 部署运维手册（脱敏版）

> 本文记录《剑来》项目的可复用部署流程。主机地址、SSH 用户、密钥路径、证书私钥和内部服务拓扑不得写入 Git；实际值由部署环境变量或私有运维系统提供。

## 安全边界

- Git 只保存部署步骤和配置模板，不保存私钥、证书包、口令、Token 或生产 `.env`。
- SSH 私钥必须位于项目目录之外，并保持 `600` 权限。
- 生产主机、用户和密钥路径通过环境变量注入：
  - `JIANLAI_DEPLOY_HOST`
  - `JIANLAI_DEPLOY_USER`
  - `JIANLAI_SSH_KEY`
- 日志和诊断输出在分享前必须检查是否包含请求头、查询参数或用户数据。

## 连接检查

```bash
test -n "$JIANLAI_DEPLOY_HOST"
test -n "$JIANLAI_DEPLOY_USER"
test -n "$JIANLAI_SSH_KEY"
chmod 600 "$JIANLAI_SSH_KEY"
ssh -i "$JIANLAI_SSH_KEY" \
  "$JIANLAI_DEPLOY_USER@$JIANLAI_DEPLOY_HOST" 'uname -a'
```

不要在命令、脚本或文档里硬编码真实主机、用户和密钥文件名。

## 发布流程

1. 在本地运行数据校验、测试和目标端构建。
2. 生成不可变发布目录或带版本号的制品。
3. 上传到服务器的临时目录。
4. 在服务器端校验文件数量、哈希和权限。
5. 原子切换当前版本链接或发布目录。
6. 检查首页、数据接口、关键静态资源和小程序请求域名。
7. 失败时切回上一版本；不要在失败状态下继续覆盖文件。

示例骨架：

```bash
RELEASE_ID="$(date +%Y%m%d-%H%M%S)"
REMOTE_STAGE="/tmp/jianlai-$RELEASE_ID"

ssh -i "$JIANLAI_SSH_KEY" \
  "$JIANLAI_DEPLOY_USER@$JIANLAI_DEPLOY_HOST" \
  "mkdir -p '$REMOTE_STAGE'"

# 按实际制品目录补充 rsync/scp，并在切换前核验。
```

## HTTPS 与证书续期

生产环境使用 Certbot + Let's Encrypt 自动续期。续期检查应至少覆盖：

```bash
sudo certbot certificates
systemctl status snap.certbot.renew.timer --no-pager
sudo certbot renew --dry-run --run-deploy-hooks
sudo nginx -t
```

续期成功后先执行 `nginx -t`，通过后再 reload。证书私钥路径和证书备份不得复制进项目目录。

线上可用性检查：

```bash
curl -sS -o /dev/null \
  -w "HTTP %{http_code} | TLS %{ssl_verify_result} (0=ok)\n" \
  "https://$JIANLAI_DEPLOY_HOST/"
```

## 回滚要求

- 每次发布前保留上一版本的不可变副本。
- 回滚只切换版本指针，不现场修改旧制品。
- 回滚后重新执行 HTTP、TLS、静态资源和接口检查。
- 旧证书只能用于事故取证，不能作为长期回滚方案。

## 不进入 Git 的运维资料

- 真实公网 IP、SSH 用户和主机清单
- SSH 私钥、证书私钥、证书压缩包
- 生产 `.env`、访问令牌和第三方平台凭证
- 精确内部端口、非公开服务路径和防火墙规则
- 带真实用户内容的生产日志或数据库备份

这些资料应保存在受控的密码库、云密钥服务或私有运维系统中。
