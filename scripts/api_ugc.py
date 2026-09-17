import sqlite3
import os
import uuid
from datetime import datetime
import zipfile
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Header, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# 数据库和文件存储路径配置
UGC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ugc_data')
DB_PATH = os.path.join(UGC_DIR, 'submissions.db')
IMAGES_DIR = os.path.join(UGC_DIR, 'pending_images')

# [#1] 安全：ADMIN_TOKEN 不再提供默认值，必须通过环境变量配置
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    import sys
    print("❌ 致命错误：必须设置 ADMIN_TOKEN 环境变量！")
    sys.exit(1)

DEPLOY_DIR = os.getenv("DEPLOY_DIR", "/var/www/jianlai")

# [#8] 合法的图片扩展名白名单
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff'}
# 图片 magic bytes 前缀检测
IMAGE_MAGIC_BYTES = {
    b'\xff\xd8\xff': 'jpg',       # JPEG
    b'\x89PNG': 'png',             # PNG
    b'GIF8': 'gif',                # GIF
    b'RIFF': 'webp',              # WebP (RIFF....WEBP)
    b'BM': 'bmp',                  # BMP
    b'II': 'tiff',                 # TIFF (little-endian)
    b'MM': 'tiff',                 # TIFF (big-endian)
}

def is_valid_image(content_bytes: bytes, filename: str) -> bool:
    """通过 magic bytes 和扩展名双重校验文件是否为合法图片"""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False
    # 检查 magic bytes
    for magic, _ in IMAGE_MAGIC_BYTES.items():
        if content_bytes[:len(magic)] == magic:
            return True
    return False

# 确保目录存在
os.makedirs(UGC_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def verify_admin(x_admin_token: str = Header(None), token: str = Query(None)):
    req_token = x_admin_token or token
    if req_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

# [#5] 数据库上下文管理器，确保异常时也能正确关闭连接
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                openid TEXT NOT NULL,
                entry_name TEXT NOT NULL,
                suggestion_type TEXT NOT NULL,
                field TEXT,
                content TEXT,
                image_path TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    finally:
        conn.close()

init_db()

app = FastAPI(title="Jianlai UGC API")

# 允许跨域（小程序开发版可能会用到）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UGCSubmitRequest(BaseModel):
    openid: str
    entry_name: str
    suggestion_type: str
    entry_type: Optional[str] = ""  # [#9] 新增：词条类型（人物/地点/势力/法宝）
    field: Optional[str] = ""
    content: Optional[str] = ""

# [#10] 防刷判定使用北京时间 (UTC+8)
RATE_LIMIT_SQL = """
    SELECT COUNT(*) FROM submissions 
    WHERE openid = ? AND date(created_at, '+8 hours') = date('now', '+8 hours')
"""

@app.post("/jianlai/api/ugc/submit_text")
async def submit_text(request: UGCSubmitRequest):
    sub_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        # [#10] 防刷判定使用北京时间
        cursor.execute(RATE_LIMIT_SQL, (request.openid,))
        count = cursor.fetchone()[0]
        if count >= 10:
            raise HTTPException(status_code=429, detail="今日提交次数已达上限")
            
        cursor.execute('''
            INSERT INTO submissions (id, openid, entry_name, suggestion_type, field, content)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sub_id, request.openid, request.entry_name, request.suggestion_type, request.field, request.content))
        conn.commit()
    finally:
        conn.close()
    
    return {"message": "提交成功，感谢为浩然天下添砖加瓦", "id": sub_id}

@app.post("/jianlai/api/ugc/upload_image")
async def upload_image(
    openid: str = Form(...),
    entry_name: str = Form(...),
    suggestion_type: str = Form(...),
    field: str = Form(""),
    content: str = Form(""),
    file: UploadFile = File(...)
):
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        # [#10] 防刷判定使用北京时间
        cursor.execute(RATE_LIMIT_SQL, (openid,))
        count = cursor.fetchone()[0]
        if count >= 10:
            raise HTTPException(status_code=429, detail="今日提交次数已达上限")

        sub_id = str(uuid.uuid4())
        
        # [#8] 读取文件并验证是否为合法图片
        content_bytes = await file.read()
        if not is_valid_image(content_bytes, file.filename or ''):
            raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp/bmp 格式的图片文件")
        
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in (file.filename or '') else 'jpg'
        safe_filename = f"{sub_id}.{ext}"
        file_path = os.path.join(IMAGES_DIR, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(content_bytes)
            
        cursor.execute('''
            INSERT INTO submissions (id, openid, entry_name, suggestion_type, field, content, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (sub_id, openid, entry_name, suggestion_type, field, content, file_path))
        conn.commit()
    finally:
        conn.close()
    
    return {"message": "图片及补充资料提交成功", "id": sub_id}

# ================= 管理员 API (C/S 架构后端) =================

@app.get("/jianlai/api/ugc/admin/pending")
async def get_pending_submissions(admin=Depends(verify_admin)):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE status = 'pending' ORDER BY created_at ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/jianlai/api/ugc/admin/image/{filename}")
async def get_pending_image(filename: str, admin=Depends(verify_admin)):
    # 防止路径遍历
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

class ResolveRequest(BaseModel):
    id: str
    status: str # 'approved', 'rejected'

VALID_STATUSES = {'approved', 'rejected', 'pending'}

@app.post("/jianlai/api/ugc/admin/resolve")
async def resolve_submission(req: ResolveRequest, admin=Depends(verify_admin)):
    if req.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {req.status}")
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE submissions SET status = ? WHERE id = ?", (req.status, req.id))
        conn.commit()
    finally:
        conn.close()
    return {"message": "Success"}

class CleanupRequest(BaseModel):
    id: str

# [#6] 管理员审核通过某条后，清理该条对应的服务器端暂存图片
@app.post("/jianlai/api/ugc/admin/cleanup_image")
async def cleanup_pending_image(req: CleanupRequest, admin=Depends(verify_admin)):
    """审核完成后清理服务器上的暂存图片"""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT image_path FROM submissions WHERE id = ?", (req.id,))
        row = cursor.fetchone()
        if row and row['image_path']:
            image_path = row['image_path']
            if os.path.exists(image_path):
                os.remove(image_path)
                return {"message": f"已清理暂存图片: {os.path.basename(image_path)}"}
            return {"message": "图片文件已不存在"}
    finally:
        conn.close()
    return {"message": "该记录无关联图片"}

@app.post("/jianlai/api/ugc/admin/upload_data")
async def upload_deploy_data(
    subpath: str = Form(...),
    file: UploadFile = File(...),
    admin=Depends(verify_admin)
):
    # [#2] 安全性校验：使用 realpath 防止路径遍历（包括 URL 编码绕过等）
    if ".." in subpath or subpath.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid subpath")

    # 文件类型白名单：只允许数据文件和图片
    ALLOWED_DEPLOY_EXTENSIONS = {'json', 'webp', 'jpg', 'jpeg', 'png'}
    ext = subpath.rsplit('.', 1)[-1].lower() if '.' in subpath else ''
    if ext not in ALLOWED_DEPLOY_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不允许上传 .{ext} 类型文件")
    
    target_path = os.path.realpath(os.path.join(DEPLOY_DIR, subpath))
    deploy_real = os.path.realpath(DEPLOY_DIR)
    if not target_path.startswith(deploy_real + os.sep) and target_path != deploy_real:
        raise HTTPException(status_code=400, detail="路径越界，拒绝写入")
        
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    content_bytes = await file.read()
    with open(target_path, "wb") as f:
        f.write(content_bytes)
        
    return {"message": f"Successfully uploaded to {subpath}"}

# [#3] ZIP 解压安全：检查 Zip Slip + 限制解压总大小
MAX_ZIP_EXTRACT_SIZE = 100 * 1024 * 1024  # 100MB 上限

@app.post("/jianlai/api/ugc/admin/upload_zip")
async def upload_deploy_zip(
    file: UploadFile = File(...),
    admin=Depends(verify_admin)
):
    zip_path = os.path.join(UGC_DIR, "temp_deploy.zip")
    content_bytes = await file.read()
    with open(zip_path, "wb") as f:
        f.write(content_bytes)
        
    try:
        target_dir = os.path.join(DEPLOY_DIR, "data")
        target_dir_real = os.path.realpath(target_dir)
        os.makedirs(target_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 安全检查：遍历所有成员，检查路径和总大小
            total_size = 0
            for info in zip_ref.infolist():
                # Zip Slip 检查：确保解压路径不会逃逸到目标目录之外
                member_path = os.path.realpath(os.path.join(target_dir, info.filename))
                if not member_path.startswith(target_dir_real + os.sep) and member_path != target_dir_real:
                    raise HTTPException(status_code=400, detail=f"ZIP 包含非法路径: {info.filename}")
                # Zip Bomb 检查：累计解压大小
                total_size += info.file_size
                if total_size > MAX_ZIP_EXTRACT_SIZE:
                    raise HTTPException(status_code=400, detail="ZIP 解压后体积超过 100MB 限制")
            
            zip_ref.extractall(target_dir)
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
    return {"message": "Data zip extracted successfully and deployed!"}

# 本地启动指令：uvicorn api_ugc:app --host 0.0.0.0 --port 8002
