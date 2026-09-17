#!/usr/bin/env python3
"""
重命名章节文件：删除文件名前的数字前缀（如 "006_"）

将 "006_第1章 惊蛰.txt" 重命名为 "第1章 惊蛰.txt"
"""

import os
import glob
from pathlib import Path

CHAPTERS_DIR = Path("/Users/shushu/剑来/chapters")

def main():
    files = sorted(glob.glob(str(CHAPTERS_DIR / "*.txt")))
    print(f"发现 {len(files)} 个章节文件")
    
    renamed_count = 0
    for file_path in files:
        filename = os.path.basename(file_path)
        
        # 检查是否有数字前缀（格式：006_第1章 xxx.txt）
        if "_" in filename:
            parts = filename.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit():
                new_filename = parts[1]  # 取 "_" 后面的部分
                new_path = CHAPTERS_DIR / new_filename
                
                # 检查目标文件是否已存在
                if new_path.exists():
                    print(f"跳过（目标已存在）: {filename} -> {new_filename}")
                    continue
                
                # 重命名
                os.rename(file_path, new_path)
                print(f"重命名: {filename} -> {new_filename}")
                renamed_count += 1
    
    print(f"\n完成！共重命名 {renamed_count} 个文件")

if __name__ == "__main__":
    main()
