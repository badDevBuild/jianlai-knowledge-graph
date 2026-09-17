#!/usr/bin/env python3
"""
Compress avatar images from PNG to WebP for faster loading.
Also generates thumbnails for home page use.
"""

import subprocess
from pathlib import Path

def compress_avatars():
    # 路径配置
    base_dir = Path(__file__).parent
    input_dir = base_dir / "frontend/public/img/avatars"
    output_dir = input_dir  # 输出到同一目录
    
    # 检查 cwebp 是否可用
    try:
        subprocess.run(["cwebp", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("错误: 需要安装 cwebp 工具")
        print("macOS: brew install webp")
        print("Linux: apt install webp")
        return
    
    # 获取所有 PNG 文件
    png_files = list(input_dir.glob("*.png"))
    if not png_files:
        print(f"未找到 PNG 文件: {input_dir}")
        return
    
    print(f"找到 {len(png_files)} 张头像图片")
    
    total_before = 0
    total_after = 0
    
    for png_path in png_files:
        webp_path = output_dir / (png_path.stem + ".webp")
        
        # 压缩为 WebP (质量 80，足够清晰)
        result = subprocess.run([
            "cwebp",
            "-q", "80",
            "-resize", "144", "144",  # 缩小到 144x144 (2x for retina)
            str(png_path),
            "-o", str(webp_path)
        ], capture_output=True)
        
        if result.returncode == 0:
            before_size = png_path.stat().st_size / 1024
            after_size = webp_path.stat().st_size / 1024
            total_before += before_size
            total_after += after_size
            print(f"  {png_path.name}: {before_size:.0f}KB → {after_size:.0f}KB")
        else:
            print(f"  {png_path.name}: 压缩失败")
    
    print(f"\n总计: {total_before:.0f}KB → {total_after:.0f}KB")
    print(f"压缩比: {total_after/total_before*100:.1f}%")

if __name__ == "__main__":
    compress_avatars()
