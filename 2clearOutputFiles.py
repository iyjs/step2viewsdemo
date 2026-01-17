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
            'output_dir': 'step2viewdata/debug_output',
            'log_dir': 'step2viewdata/debug_processlog'
        }
    elif mode.upper() == 'RELEASE':
        return {
            'output_dir': 'step2viewdata/release_output',
            'log_dir': 'step2viewdata/release_processlog'
        }
    else:
        raise ValueError(f"不支持的运行模式: {mode}")

class Logger:
    """
    日志记录器，同时输出到控制台和文件
    """
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志文件名（包含时间戳）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"clearoutput_{timestamp}.log"
        
        # 打开日志文件
        self.log_handle = open(self.log_file, 'w', encoding='utf-8')
        
        # 记录开始时间
        self.start_time = datetime.datetime.now()
        self.log(f"日志开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"日志文件: {self.log_file}")
        self.log("-" * 60)
    
    def log(self, message):
        """
        记录日志消息
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 输出到控制台
        print(log_message)
        
        # 输出到文件
        self.log_handle.write(log_message + '\n')
        self.log_handle.flush()  # 立即写入文件
    
    def close(self):
        """
        关闭日志文件
        """
        end_time = datetime.datetime.now()
        duration = end_time - self.start_time
        
        self.log("-" * 60)
        self.log(f"日志结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"总耗时: {duration}")
        self.log(f"日志文件保存位置: {self.log_file}")
        
        self.log_handle.close()

def clear_output_directory(logger, output_dir):
    """
    清除指定目录下的所有子文件和子目录
    """
    logger.log(f"开始清理目录: {output_dir}")
    
    # 检查output目录是否存在
    if not output_dir.exists():
        logger.log(f"输出目录 {output_dir} 不存在，无需清理")
        return
    
    # 统计要删除的文件和目录数量
    total_files = 0
    total_dirs = 0
    deleted_items = []
    
    # 遍历output目录下的所有内容
    for item in output_dir.iterdir():
        if item.is_file():
            # 删除文件
            try:
                item.unlink()
                logger.log(f"删除文件: {item.name}")
                deleted_items.append(f"文件: {item.name}")
                total_files += 1
            except Exception as e:
                logger.log(f"删除文件失败 {item.name}: {str(e)}")
        elif item.is_dir():
            # 删除目录及其所有内容
            try:
                shutil.rmtree(item)
                logger.log(f"删除目录: {item.name}")
                deleted_items.append(f"目录: {item.name}")
                total_dirs += 1
            except Exception as e:
                logger.log(f"删除目录失败 {item.name}: {str(e)}")
    
    logger.log(f"清理完成!")
    logger.log(f"共删除 {total_files} 个文件")
    logger.log(f"共删除 {total_dirs} 个目录")
    
    if deleted_items:
        logger.log("删除的项目详情:")
        for item in deleted_items:
            logger.log(f"  - {item}")

def clear_output_directory_safe(logger, output_dir):
    """
    安全清除目录 - 先询问用户确认
    """
    logger.log(f"检查目录: {output_dir}")
    
    if not output_dir.exists():
        logger.log(f"输出目录 {output_dir} 不存在，无需清理")
        return
    
    # 统计要删除的内容
    files_count = 0
    dirs_count = 0
    items_list = []
    
    for item in output_dir.iterdir():
        if item.is_file():
            files_count += 1
            items_list.append(f"文件: {item.name}")
        elif item.is_dir():
            dirs_count += 1
            items_list.append(f"目录: {item.name}")
    
    if files_count == 0 and dirs_count == 0:
        logger.log("目录为空，无需清理")
        return
    
    # 显示将要删除的内容
    logger.log(f"即将删除 {output_dir.name} 目录下的:")
    logger.log(f"  - {files_count} 个文件")
    logger.log(f"  - {dirs_count} 个目录")
    
    if items_list:
        logger.log("将要删除的项目:")
        for item in items_list[:10]:  # 只显示前10个
            logger.log(f"  {item}")
        if len(items_list) > 10:
            logger.log(f"  ... 还有 {len(items_list) - 10} 个项目")
    
    # 询问用户确认
    logger.log("等待用户确认...")
    confirm = input("确认删除吗? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        logger.log("用户确认删除，开始执行...")
        clear_output_directory(logger, output_dir)
    else:
        logger.log("用户取消操作")

def clear_output_directory_auto(logger, output_dir):
    """
    自动清除目录 - 无需用户确认
    """
    logger.log("自动清理模式")
    clear_output_directory(logger, output_dir)

def show_log_directory_info(logger, log_dir):
    """
    显示日志目录信息
    """
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        logger.log(f"日志目录: {log_dir}")
        logger.log(f"现有日志文件数: {len(log_files)}")
        
        if log_files:
            logger.log("最近的日志文件:")
            # 按修改时间排序，显示最新的5个
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            for log_file in log_files[:5]:
                mtime = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
                logger.log(f"  {log_file.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        logger.log(f"日志目录不存在: {log_dir}")

def main():
    """
    主函数，支持命令行参数和模式选择
    """
    print("=" * 60)
    print("清理输出目录工具 - 支持DEBUG/RELEASE模式")
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
        print("1. DEBUG模式  (清理debug_output，日志保存到debug_processlog)")
        print("2. RELEASE模式 (清理release_output，日志保存到release_processlog)")
        
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
    
    # 获取模式配置
    try:
        config = get_mode_config(mode)
    except ValueError as e:
        print(f"错误: {e}")
        return
    
    print(f"\n运行模式: {mode}")
    print(f"输出目录: {config['output_dir']}")
    print(f"日志目录: {config['log_dir']}")
    print("-" * 60)
    
    # 创建日志记录器
    logger = Logger(config['log_dir'])
    logger.log(f"开始处理 - 模式: {mode}")
    logger.log(f"输出目录: {config['output_dir']}")
    logger.log(f"日志目录: {config['log_dir']}")
    
    try:
        # 显示日志目录信息
        show_log_directory_info(logger, Path(config['log_dir']))
        logger.log("-" * 60)
        
        # 选择清理模式
        print("\n选择清理模式:")
        print("1. 安全模式 (需要确认)")
        print("2. 自动模式 (无需确认)")
        print("3. 仅显示日志信息")
        
        while True:
            choice = input("请输入选择 (1/2/3): ").strip()
            if choice == "1":
                logger.log("选择安全模式")
                clear_output_directory_safe(logger, Path(config['output_dir']))
                break
            elif choice == "2":
                logger.log("选择自动模式")
                clear_output_directory_auto(logger, Path(config['output_dir']))
                break
            elif choice == "3":
                logger.log("仅显示日志信息")
                break
            else:
                print("无效选择，请输入 1、2 或 3")
                
    except Exception as e:
        logger.log(f"处理过程中发生错误: {str(e)}")
    finally:
        logger.close()
        print(f"\n日志已保存到: {config['log_dir']}")

if __name__ == "__main__":
    main()
