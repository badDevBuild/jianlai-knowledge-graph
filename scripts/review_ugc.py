import sqlite3
import os
import json
import shutil
import urllib.request
import subprocess
from pathlib import Path
from openai import OpenAI

# ======= API及同步配置 =======
API_BASE = os.getenv("UGC_API_URL", "http://127.0.0.1:8002/jianlai/api/ugc")
# [#1] 安全：ADMIN_TOKEN 不再提供默认值
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    print("❌ 致命错误：必须设置 ADMIN_TOKEN 环境变量！请在 ~/.zshrc 中配置。")
    exit(1)
# ============================

# ======= LLM 配置 =======
# 接入本地 gcli2api 代理服务 (OpenAI 兼容格式)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:7861/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3-pro-preview")

try:
    if not LLM_API_KEY:
        raise RuntimeError("未设置 LLM_API_KEY")
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    print(f"✅ 大模型已接入: {LLM_BASE_URL} (模型: {LLM_MODEL})")
except Exception as e:
    client = None
    print(f"⚠️ 大模型初始化失败，润色功能将不可用 ({e})")
# ========================

UGC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ugc_data')
DB_PATH = os.path.join(UGC_DIR, 'submissions.db')
PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'build', 'profiles_v3')
LOCAL_IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'taro-app', 'public', 'images')

def get_pending_submissions():
    req = urllib.request.Request(f"{API_BASE}/admin/pending", headers={"X-Admin-Token": ADMIN_TOKEN})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"⚠️ 拉取云端待审数据失败 ({API_BASE}): {e}")
        return []

def update_status(sub_id, status):
    data = json.dumps({"id": sub_id, "status": status}).encode('utf-8')
    req = urllib.request.Request(f"{API_BASE}/admin/resolve", data=data, 
                                 headers={"X-Admin-Token": ADMIN_TOKEN, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            pass
    except Exception as e:
        print(f"⚠️ 同步状态失败: {e}")

# [#6] 审核完成后，通知服务器清理暂存的预览图片
def cleanup_server_image(sub_id):
    """调用服务端接口清理该条提交对应的暂存图片"""
    data = json.dumps({"id": sub_id}).encode('utf-8')
    req = urllib.request.Request(f"{API_BASE}/admin/cleanup_image", data=data,
                                 headers={"X-Admin-Token": ADMIN_TOKEN, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"🗑️ 服务器: {result.get('message', '清理完成')}")
    except Exception as e:
        print(f"⚠️ 清理服务器暂存图片失败: {e}")

def apply_image_update(entry_name, image_path, local_preview_path=None):
    if not image_path:
        return False
        
    filename = os.path.basename(image_path)
    
    # 避免二次下载：如果已经有了提前拉取的本地预览图，直接沿用
    local_tmp = local_preview_path
    if not local_tmp or not os.path.exists(local_tmp):
        req = urllib.request.Request(f"{API_BASE}/admin/image/{filename}", headers={"X-Admin-Token": ADMIN_TOKEN})
        try:
            local_tmp = f"/tmp/{filename}"
            with urllib.request.urlopen(req) as response, open(local_tmp, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            print(f"⚠️ 获取云端图片失败: {e}")
            return False
            
    try:
        # 借助 Pillow 进行图片缩放压缩与格式转换 (采用 optimize-images 策略)
        target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'taro-app', 'public', 'data', 'img', 'avatars')
        os.makedirs(target_dir, exist_ok=True)
        
        # 统一输出为 webp 格式
        output_ext = "webp"
        local_target_path = os.path.join(target_dir, f"{entry_name}.{output_ext}")
        
        try:
            from PIL import Image
            with Image.open(local_tmp) as img:
                if img.mode == 'P':
                    img = img.convert('RGBA')
                
                max_width = 800 # 控制在适合小程序的高清且小体积边界
                w, h = img.size
                if w > max_width:
                    new_h = int(h * (max_width / w))
                    img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
                
                img.save(local_target_path, 'WEBP', quality=85)
            print(f"✅ 图片已压缩转码为 WebP，并防爆入库: {local_target_path}")
        except ImportError:
            # 兼容极端降级
            print("⚠️ 未安装 Pillow，回退至无损原图直传策略..")
            ext = filename.split('.')[-1]
            local_target_path = os.path.join(target_dir, f"{entry_name}.{ext}")
            output_ext = ext
            shutil.copy2(local_tmp, local_target_path)
            print(f"✅ 图片已暂存在本地(未压缩): {local_target_path}")
        
        # 将图片即刻推回生产服务器的图片分发区
        subpath = f"img/avatars/{entry_name}.{output_ext}"
        print(f"🚀 正在将优化后的图片推送至云端 {subpath}...")
        res = subprocess.run([
            "curl", "-s", "--fail", "-w", "\n%{http_code}", "-X", "POST",
            f"{API_BASE}/admin/upload_data",
            "-H", f"X-Admin-Token: {ADMIN_TOKEN}",
            "-F", f"subpath={subpath}",
            "-F", f"file=@{local_target_path}"
        ], capture_output=True, text=True)
        if res.returncode == 0:
            print("✅ 云端配图同步完成！")
        else:
            http_code = res.stdout.strip().split('\n')[-1] if res.stdout else 'unknown'
            print(f"⚠️ 云端配图上传失败 (HTTP {http_code})")
            return False
        return True
    except Exception as e:
        print(f"⚠️ 获取或同步图片失败: {e}")
        return False

# [#7] 智能设置嵌套值：检查原字段类型，避免用字符串覆盖数组
def set_nested_value(data_dict, path, value):
    keys = path.split('.')
    current = data_dict
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    final_key = keys[-1]
    original_value = current.get(final_key)
    
    # 如果原字段是数组，尝试将 LLM 输出解析为 JSON 数组或追加为单项
    if isinstance(original_value, list):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                current[final_key] = parsed
            else:
                current[final_key].append(parsed)
        except (json.JSONDecodeError, TypeError):
            # LLM 输出不是合法 JSON，作为单个字符串追加
            current[final_key].append(value)
        return
    
    # 如果原字段是数字，尝试转换
    if isinstance(original_value, (int, float)):
        try:
            current[final_key] = type(original_value)(value)
            return
        except (ValueError, TypeError):
            pass
    
    # 默认：直接覆盖为字符串
    current[final_key] = value

def ask_llm_for_update(original_data_str: str, field: str, user_suggestion: str):
    prompt = f"""
你是一个《剑来》百科词条数据维护助手。
这是该词条当前的 JSON 数据（部分或全部）：
```json
{original_data_str}
```

用户针对字段 `{field}` 提出了如下修改/补充建议：
"{user_suggestion}"

请你分析用户的建议，并结合原数据，输出**专门针对该字段的最新内容**。
- 如果是纯文本字段（如 bio, description），请输出润色合并后的完整段落。
- 如果是数组追加（如 quotes），请判断应该增加什么字符串，或整理为合法 JSON 片段输出。
- 如果建议极不合理，请回复"拒绝"。

注意：你只需要输出处理后的新文本内容或局部数据，**不要输出多余的解释、不要包裹 Markdown 代码块符号**。直接给我最终能替换/追加入那个字段的纯粹内容。
"""
    if not client:
        return f"[MockAI辅助润色结果] {user_suggestion}"
        
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ LLM 调用失败: {e}")
        return None

def apply_text_update(entry_name, field, content, suggestion_type):
    # 支持多数据源查找：人物(独立JSON) / 地点·法宝·势力(大文件dict)
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'build')
    target_file = os.path.join(PROFILES_DIR, f"{entry_name}.json")
    collection_key = None  # 如果在大文件中找到，记录键名

    if not os.path.exists(target_file):
        # 在 locations/items/factions 大文件中搜索
        for json_name in ['locations.json', 'items.json', 'factions.json']:
            json_path = os.path.join(base_dir, json_name)
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    collection = json.load(f)
                if entry_name in collection:
                    target_file = json_path
                    collection_key = entry_name
                    print(f"📍 在 {json_name} 中找到词条「{entry_name}」")
                    break
        else:
            print(f"⚠️ 找不到词条「{entry_name}」的本地数据（已搜索 profiles_v3/、locations、items、factions），需手动处理。")
            return False
        
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        # 如果是大文件中的词条，提取子对象
        if collection_key:
            data = file_data[collection_key]
        else:
            data = file_data
            
        print("\n✨ 正在呼叫大模型进行自动分析与润色...")
        # 为了不撑爆 Context，我们尽力只传特定的 field 附近的数据，或者传整个（如果不大）
        original_context = json.dumps(data.get(field) or data, ensure_ascii=False, indent=2)[:1500] 
        
        llm_suggestion = ask_llm_for_update(original_context, field, content)
        
        if not llm_suggestion or llm_suggestion == "拒绝":
            print("🤖 大模型认为该建议不合理或解析失败，需要您手动处理。")
            return False
            
        print(f"\n🤖 大模型给出的 [{field}] 最终合并建议：\n\033[92m{llm_suggestion}\033[0m\n")
        
        confirm = input("是否直接应用大模型的合并结果？[Y:是 | N:否(仅暂存在ugc_notes，不触发发布)] ").strip().upper()
        
        if confirm == 'Y':
            set_nested_value(data, field, llm_suggestion)
            # 写回：大文件需更新子对象，独立文件直接写
            if collection_key:
                file_data[collection_key] = data
            else:
                file_data = data
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已成功将 AI 结果覆盖到字段 `{field}`。")
            return True
        else:
            if 'ugc_notes' not in data:
                data['ugc_notes'] = []
            data['ugc_notes'].append(f"[{field}] 用户提议:{content} | AI润色:{llm_suggestion}")
            if collection_key:
                file_data[collection_key] = data
            else:
                file_data = data
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已将建议与 AI 润色结果存入 ugc_notes（不会触发构建发布）。")
            return False
    except Exception as e:
        print(f"写入 JSON 失败: {e}")
        return False


def deploy_built_data(approved_entries: set):
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'dist')
    if not os.path.exists(build_dir):
        print("未找到编译输出目录。")
        return
        
    print(f"🚀 正在仅将改动的 {len(approved_entries)} 个词条及全局索引推送至云端热部署区...")
    
    # 需要上传的核心全局索引文件
    global_files = ["characters_lite.json", "quotes.json", "relations.json", "characters_top.json",
                     "locations.json", "factions.json", "items_lite.json", "items.json",
                     "search_index.json", "timeline.json"]
    
    files_to_upload = []
    
    for gf in global_files:
        path = os.path.join(build_dir, gf)
        if os.path.exists(path):
            files_to_upload.append((path, f"data/{gf}"))
            
    # 需要上传的个体文件 (人物 chars/ 和物品 items/)
    for entry in approved_entries:
        char_path = os.path.join(build_dir, "chars", f"{entry}.json")
        if os.path.exists(char_path):
            files_to_upload.append((char_path, f"data/chars/{entry}.json"))
        item_path = os.path.join(build_dir, "items", f"{entry}.json")
        if os.path.exists(item_path):
            files_to_upload.append((item_path, f"data/items/{entry}.json"))
            
    success_count = 0
    for local_path, subpath in files_to_upload:
        try:
            res = subprocess.run([
                "curl", "-s", "--fail", "-w", "\n%{http_code}", "-X", "POST",
                f"{API_BASE}/admin/upload_data",
                "-H", f"X-Admin-Token: {ADMIN_TOKEN}",
                "-F", f"subpath={subpath}",
                "-F", f"file=@{local_path}"
            ], capture_output=True, text=True)
            if res.returncode == 0:
                success_count += 1
            else:
                http_code = res.stdout.strip().split('\n')[-1] if res.stdout else 'unknown'
                print(f"  ❌ {subpath} 上传失败 (HTTP {http_code})")
        except Exception as e:
            print(f"⚠️ {subpath} 上传失败: {e}")
            
    print(f"✨ 增量热部署完毕 (共更新 {success_count} 个文件)！CDN 用户下次刷新即可享用最新数据！")

def main():
    print("=== 剑来小程序 UGC 跨端审核系统 (C/S版) ===")
    submissions = get_pending_submissions()
    
    if not submissions:
        print("🍾 暂无待审核的词条贡献，去喝杯茶吧！")
        return

    print(f"发现 {len(submissions)} 条待审记录。")
    
    approved_count = 0
    approved_entries = set()
    for sub in submissions:
        # [#6 修复] 在循环开头初始化，避免引用上一条记录的残留变量
        local_preview_path = None
        
        print("\n" + "="*40)
        print(f"👤 用户: {sub['openid']}")
        print(f"📝 词条: 【{sub['entry_name']}】 [{sub['suggestion_type']}]")
        print(f"🎯 溯源位置(Field): {sub.get('field') or '通用'}")
        print(f"🕰 时间: {sub['created_at']}")
        print("-" * 15 + " 内容 " + "-" * 15)
        print(sub['content'] or "(无文字内容)")
        
        # 处理图片预览，自动拉取至本地
        if sub['image_path']:
            filename = os.path.basename(sub['image_path'])
            preview_dir = "temp_images"
            os.makedirs(preview_dir, exist_ok=True)
            local_preview_path = os.path.join(preview_dir, filename)
            
            try:
                req = urllib.request.Request(f"{API_BASE}/admin/image/{filename}", headers={"X-Admin-Token": ADMIN_TOKEN})
                with urllib.request.urlopen(req) as response, open(local_preview_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                print(f"📷 附带图片: {os.path.abspath(local_preview_path)} (按住Cmd/Ctrl双击打开查看)")
            except Exception as e:
                print(f"📷 附带图片 (云端): {sub['image_path']} (自动下载预览图失败: {e})")
                local_preview_path = None
                
        print("="*40)
        
        while True:
            choice = input("\n审核动作 [Y:接受 | N:拒绝 | S:跳过 | Q:退出]: ").strip().upper()
            if choice == 'Q':
                print(f"退出审核。本次共通过 {approved_count} 条。")
                # 清理本条的本地临时文件
                if local_preview_path and os.path.exists(local_preview_path):
                    os.remove(local_preview_path)
                break
            elif choice == 'S':
                print("已跳过。")
                break
            elif choice == 'N':
                update_status(sub['id'], 'rejected')
                # [#6] 拒绝后也清理服务器上该条的暂存图片
                if sub['image_path']:
                    cleanup_server_image(sub['id'])
                print("❌ 已拒绝此条建议。")
                break
            elif choice == 'Y':
                # 应用更新 (先处理图片——更易失败，避免文字已写入但图片失败导致脏数据)
                success = True
                if sub['image_path']:
                    success = apply_image_update(sub['entry_name'], sub['image_path'], local_preview_path)
                if success and sub['content']:
                    field_key = sub.get('field') or 'ugc_notes'
                    if field_key == '通用': field_key = 'ugc_notes'
                    success = apply_text_update(sub['entry_name'], field_key, sub['content'], sub['suggestion_type'])
                
                if success:
                    update_status(sub['id'], 'approved')
                    approved_count += 1
                    approved_entries.add(sub['entry_name'])
                    # [#6] 审核通过后清理服务器上该条的暂存图片
                    if sub['image_path']:
                        cleanup_server_image(sub['id'])
                else:
                    print("⚠️ 自动合并似乎有些问题，已标记为 pending 暂不修改状态。")
                break
            else:
                print("输入有误，请重新输入。")
        
        # 清理本条审批遗留的本地预览临时文件
        if local_preview_path and os.path.exists(local_preview_path):
            try:
                os.remove(local_preview_path)
            except Exception:
                pass
        
        # 如果用户按了 Q，跳出大循环
        if choice == 'Q':
            break

    print(f"\n审核完毕，本次共通过 {approved_count} 条。")
    if approved_count > 0:
        print("正在本地触发自动化构建以生成最新轻量数据缓存文件...")
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run(["python", "scripts/build_frontend_data.py"], cwd=root_dir)
        subprocess.run(["python", "generate_top_characters.py"], cwd=root_dir)
        print("构建完成！")
        deploy_built_data(approved_entries)

if __name__ == "__main__":
    main()
