#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path

def rename_step_files():
    """
    将traceparts目录下的.step和.STEP文件重命名为.stp文件
    """
    # 定义源目录
    source_dir = Path("step2viewdata/traceparts")
    
    # 检查目录是否存在
    if not source_dir.exists():
        print(f"错误: 目录 {source_dir} 不存在")
        return
    
    # 统计信息
    total_files = 0
    renamed_files = 0
    skipped_files = 0
    error_files = 0
    
    print(f"开始处理目录: {source_dir}")
    print("-" * 50)
    
    # 遍历目录中的所有文件
    for file_path in source_dir.iterdir():
        if file_path.is_file():
            total_files += 1
            filename = file_path.name
            name_without_ext = file_path.stem
            extension = file_path.suffix.lower()
            
            # 检查是否是.step或.STEP文件
            if extension in ['.step', '.step']:
                # 构建新的文件名
                new_filename = f"{name_without_ext}.stp"
                new_file_path = source_dir / new_filename
                
                # 检查目标文件是否已存在
                if new_file_path.exists():
                    print(f"跳过: {filename} -> {new_filename} (目标文件已存在)")
                    skipped_files += 1
                    continue
                
                try:
                    # 重命名文件
                    file_path.rename(new_file_path)
                    print(f"重命名: {filename} -> {new_filename}")
                    renamed_files += 1
                    
                except Exception as e:
                    print(f"错误: 无法重命名 {filename}: {str(e)}")
                    error_files += 1
            else:
                # 显示其他文件类型（可选）
                if extension not in ['.stp', '.py', '.md', '.txt']:
                    print(f"其他文件: {filename} ({extension})")
    
    # 打印统计结果
    print("-" * 50)
    print("处理完成!")
    print(f"总文件数: {total_files}")
    print(f"成功重命名: {renamed_files}")
    print(f"跳过文件: {skipped_files}")
    print(f"错误文件: {error_files}")

def rename_step_files_safe():
    """
    安全模式：先显示将要重命名的文件，询问用户确认
    """
    source_dir = Path("step2viewdata/traceparts")
    
    if not source_dir.exists():
        print(f"错误: 目录 {source_dir} 不存在")
        return
    
    # 收集需要重命名的文件
    files_to_rename = []
    
    for file_path in source_dir.iterdir():
        if file_path.is_file():
            filename = file_path.name
            name_without_ext = file_path.stem
            extension = file_path.suffix.lower()
            
            if extension in ['.step', '.step']:
                new_filename = f"{name_without_ext}.stp"
                new_file_path = source_dir / new_filename
                
                if not new_file_path.exists():
                    files_to_rename.append((file_path, new_file_path))
    
    if not files_to_rename:
        print("没有找到需要重命名的.step文件")
        return
    
    # 显示将要重命名的文件
    print(f"找到 {len(files_to_rename)} 个文件需要重命名:")
    print("-" * 50)
    
    for old_path, new_path in files_to_rename:
        print(f"  {old_path.name} -> {new_path.name}")
    
    print("-" * 50)
    
    # 询问用户确认
    confirm = input("确认重命名这些文件吗? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        # 执行重命名
        success_count = 0
        error_count = 0
        
        for old_path, new_path in files_to_rename:
            try:
                old_path.rename(new_path)
                print(f"✓ 重命名: {old_path.name} -> {new_path.name}")
                success_count += 1
            except Exception as e:
                print(f"✗ 错误: {old_path.name}: {str(e)}")
                error_count += 1
        
        print(f"\n完成! 成功: {success_count}, 失败: {error_count}")
    else:
        print("操作已取消")

def rename_step_files_backup():
    """
    带备份的重命名：先复制文件，再重命名
    """
    source_dir = Path("step2viewdata/traceparts")
    backup_dir = Path("step2viewdata/traceparts_backup")
    
    if not source_dir.exists():
        print(f"错误: 目录 {source_dir} 不存在")
        return
    
    # 创建备份目录
    if not backup_dir.exists():
        backup_dir.mkdir(parents=True)
        print(f"创建备份目录: {backup_dir}")
    
    # 收集需要重命名的文件
    files_to_rename = []
    
    for file_path in source_dir.iterdir():
        if file_path.is_file():
            filename = file_path.name
            name_without_ext = file_path.stem
            extension = file_path.suffix.lower()
            
            if extension in ['.step', '.step']:
                new_filename = f"{name_without_ext}.stp"
                new_file_path = source_dir / new_filename
                
                if not new_file_path.exists():
                    files_to_rename.append((file_path, new_file_path))
    
    if not files_to_rename:
        print("没有找到需要重命名的.step文件")
        return
    
    print(f"找到 {len(files_to_rename)} 个文件需要重命名")
    print("开始备份和重命名...")
    
    success_count = 0
    error_count = 0
    
    for old_path, new_path in files_to_rename:
        try:
            # 先备份原文件
            backup_path = backup_dir / old_path.name
            shutil.copy2(old_path, backup_path)
            
            # 重命名文件
            old_path.rename(new_path)
            
            print(f"✓ {old_path.name} -> {new_path.name} (已备份)")
            success_count += 1
            
        except Exception as e:
            print(f"✗ 错误: {old_path.name}: {str(e)}")
            error_count += 1
    
    print(f"\n完成! 成功: {success_count}, 失败: {error_count}")
    print(f"备份文件保存在: {backup_dir}")

if __name__ == "__main__":
    print("STEP文件重命名工具")
    print("=" * 50)
    print("1. 直接重命名")
    print("2. 安全模式（先确认）")
    print("3. 带备份重命名")
    print("=" * 50)
    
    choice = input("请选择模式 (1/2/3): ").strip()
    
    if choice == "1":
        rename_step_files()
    elif choice == "2":
        rename_step_files_safe()
    elif choice == "3":
        rename_step_files_backup()
    else:
        print("无效选择，使用安全模式...")
        rename_step_files_safe() 