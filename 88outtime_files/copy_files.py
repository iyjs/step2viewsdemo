#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path

def copy_files_from_subdirs():
    # 定义源目录和目标目录
    source_base_dir = Path("step2viewdata/traceparts")
    target_dir = Path("step2viewdata/traceparts")
    
    # 检查源目录是否存在
    if not source_base_dir.exists():
        print(f"源目录 {source_base_dir} 不存在")
        return
    
    # 获取所有子目录
    subdirs = [d for d in source_base_dir.iterdir() if d.is_dir()]
    
    if not subdirs:
        print(f"在 {source_base_dir} 中未找到子目录")
        return
    
    # 遍历每个子目录并复制文件
    total_files = 0
    for subdir in subdirs:
        print(f"处理子目录: {subdir.name}")
        files = [f for f in subdir.glob("**/*") if f.is_file()]
        
        for file in files:
            # 获取文件名
            filename = file.name
            # 构建目标文件路径 (直接放在目标目录下)
            dest_file = target_dir / filename
            
            # 如果目标文件已存在，添加子目录名作为前缀避免冲突
            if dest_file.exists():
                dest_file = target_dir / f"{subdir.name}_{filename}"
            
            # 复制文件
            shutil.copy2(file, dest_file)
            print(f"  复制: {file} -> {dest_file}")
            total_files += 1
    
    print(f"完成! 共复制了 {total_files} 个文件")

if __name__ == "__main__":
    copy_files_from_subdirs() 