# 故障排查手册

> 从 CLAUDE.md 迁出的故障排查指南。

## 提取失败 (429 错误)

**原因**: Gemini API 速率限制

**解决**:
- 脚本会自动切换到备用端点
- 检查本地 LLM 服务是否正常运行 (`http://127.0.0.1:7861`)
- 降低并发请求频率

## 人物合并错误

**原因**: 别名未在 `CHARACTER_ALIASES` 中定义

**解决**:
1. 打开 `character_merger.py`
2. 在 `CHARACTER_ALIASES` 字典中添加映射
3. 重新运行 `python build_knowledge_base.py`

## 前端数据加载失败

**原因**: 数据文件路径不正确或数据未构建

**解决**:
1. 检查 `data/dist/` 目录是否有数据
2. 确保运行了完整构建流程:
   ```bash
   python build_knowledge_base.py
   python scripts/build_frontend_data.py
   python generate_top_characters.py
   ```
3. 检查 `data/dist/` 产物清单是否完整 (参见 CLAUDE.md "data/dist/ 产物清单")

## 数据质量问题

### 提取质量检查点

在 `prompt_template.md` 模块7 中定义了 AI 自检机制:

1. **实体解析率**: 未识别人物 < 总人物数的 20%
2. **关系完整性**: 每个主要人物至少有 2 条关系
3. **外貌覆盖率**: 主要人物的 appearance 字段非空
4. **证据链**: 所有关系必须有 evidence 原文引用
5. **时态一致性**: state_snapshot 与章节内容一致

### 人工审核要点

- 检查别名解析是否正确 (通过 `character_merger.py` 日志)
- 验证关系方向是否合理 (正向/反向强度)
- 确认修真境界是否符合剧情进展
- 审查外貌描述是否忠于原文

## 热更新上传失败

**原因**: 服务端返回 HTTP 4xx/5xx

**解决**:
1. 检查 `ADMIN_TOKEN` 环境变量是否正确设置
2. 检查 UGC API 服务是否运行 (`http://127.0.0.1:8011`)
3. curl 上传已加 `--fail` 标志，控制台会显示失败的 HTTP 状态码
