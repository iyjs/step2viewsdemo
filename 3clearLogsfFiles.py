#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path
import datetime
import sys

def get_mode_config(mode):
    """
    根据运行模式获取配置
    """
    if mode.upper() == 'DEBUG':
        return {
            'log_dir': 'step2viewdata/debug_processlog'
        }
    elif mode.upper() == 'RELEASE':
        return {
            'log_dir': 'step2viewdata/release_processlog'
        }
    else:
        raise ValueError(f"不支持的运行模式: {mode}")

def print_log(message):
    """
    简单的控制台日志输出
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def clear_log_directory(log_dir_path):
    """
    清除指定目录下的所有日志文件
    """
    log_dir = Path(log_dir_path)
    
    # 检查目录是否存在
    if not log_dir.exists():
        print_log(f"日志目录不存在: {log_dir}")
        return False
    
    # 统计要删除的文件数量
    log_files = list(log_dir.glob("*.log"))
    total_files = len(log_files)
    
    if total_files == 0:
        print_log(f"日志目录为空: {log_dir}")
        return True
    
    print_log(f"找到 {total_files} 个日志文件需要删除")
    print("-" * 40)
    
    # 显示将要删除的文件
    for i, log_file in enumerate(log_files, 1):
        file_size = log_file.stat().st_size
        mtime = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
        print(f"{i:3d}. {log_file.name} ({file_size:,} 字节, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    print("-" * 40)
    
    # 询问用户确认
    confirm = input(f"确认删除 {total_files} 个日志文件吗？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print_log("用户取消操作")
        return False
    
    # 删除文件
    deleted_count = 0
    error_count = 0
    
    for log_file in log_files:
        try:
            log_file.unlink()
            print_log(f"删除文件: {log_file.name}")
            deleted_count += 1
        except Exception as e:
            print_log(f"删除文件失败 {log_file.name}: {e}")
            error_count += 1
    
    print("-" * 40)
    print_log(f"删除完成: {deleted_count} 个文件成功删除, {error_count} 个文件删除失败")
    
    return error_count == 0

def show_log_directory_info(log_dir_path):
    """
    显示日志目录信息
    """
    log_dir = Path(log_dir_path)
    
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        print_log(f"日志目录: {log_dir}")
        print_log(f"现有日志文件数: {len(log_files)}")
        
        if log_files:
            print("日志文件列表:")
            # 按修改时间排序
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            for i, log_file in enumerate(log_files, 1):
                file_size = log_file.stat().st_size
                mtime = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
                print(f"  {i:3d}. {log_file.name} ({file_size:,} 字节, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print_log("目录为空")
    else:
        print_log(f"日志目录不存在: {log_dir}")

def main():
    """
    主函数，支持命令行参数和模式选择
    """
    print("=" * 60)
    print("日志文件清理工具 - 支持DEBUG/RELEASE模式")
    print("=" * 60)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1].upper()
        if mode not in ['DEBUG', 'RELEASE']:
            print(f"错误: 不支持的运行模式 '{mode}'")
            print("支持的模式: DEBUG, RELEASE")
            return
    else:
        # 交互式选择模式
        print("请选择运行模式:")
        print("1. DEBUG模式  (清除debug_processlog目录)")
        print("2. RELEASE模式 (清除release_processlog目录)")
        
        while True:
            choice = input("请输入选择 (1/2): ").strip()
            if choice == "1":
                mode = "DEBUG"
                break
            elif choice == "2":
                mode = "RELEASE"
                break
            else:
                print("无效选择，请输入 1 或 2")
    
    try:
        # 获取模式配置
        config = get_mode_config(mode)
        log_dir = config['log_dir']
        
        print(f"\n运行模式: {mode}")
        print(f"日志目录: {log_dir}")
        print("-" * 60)
        
        # 显示当前状态
        print_log(f"开始清理 {mode} 模式的日志文件")
        show_log_directory_info(log_dir)
        
        # 执行清理操作
        success = clear_log_directory(log_dir)
        
        if success:
            print_log("日志清理操作完成")
        else:
            print_log("日志清理操作部分失败")
            
    except Exception as e:
        print(f"程序执行出错: {e}")
        return

if __name__ == "__main__":
    main()