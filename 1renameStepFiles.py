#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path
import re
import datetime
import sys

class Logger:
    """
    日志记录器，同时输出到控制台和文件
    """
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志文件名（包含时间戳）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"rename_step_{timestamp}.log"
        
        # 打开日志文件
        self.log_handle = open(self.log_file, 'w', encoding='utf-8')
        
        # 记录开始时间
        self.start_time = datetime.datetime.now()
        self.log(f"日志开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"日志文件: {self.log_file}")
        self.log("-" * 60)
    
    def log(self, message):
        """
        记录日志信息
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 输出到控制台
        print(log_message)
        
        # 输出到文件
        self.log_handle.write(log_message + "\n")
        self.log_handle.flush()
    
    def close(self):
        """
        关闭日志文件
        """
        if hasattr(self, 'log_handle'):
            end_time = datetime.datetime.now()
            duration = end_time - self.start_time
            self.log(f"日志结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.log(f"运行时长: {duration}")
            self.log_handle.close()

def get_mode_config(mode):
    """
    根据运行模式获取配置
    """
    if mode.upper() == 'DEBUG':
        return {
            'input_dir': 'step2viewdata/debug_traceparts',
            'log_dir': 'step2viewdata/debug_processlog'
        }
    elif mode.upper() == 'RELEASE':
        return {
            'input_dir': 'step2viewdata/release_traceparts',
            'log_dir': 'step2viewdata/release_processlog'
        }
    else:
        raise ValueError(f"不支持的运行模式: {mode}")

def analyze_directory(source_dir):
    """
    分析目录中的所有文件，找出需要处理的文件
    """
    if not source_dir.exists():
        return None
    
    files_analysis = {
        'step_files': [],      # .step/.STEP 文件
        'stp_with_underscore': [],  # .stp 文件但包含下划线
        'stp_clean': [],       # 干净的 .stp 文件
        'other_files': []      # 其他文件
    }
    
    for file_path in source_dir.iterdir():
        if file_path.is_file():
            filename = file_path.name
            name_without_ext = file_path.stem
            extension = file_path.suffix.lower()
            
            if extension in ['.step', '.step']:
                files_analysis['step_files'].append({
                    'path': file_path,
                    'name': filename,
                    'name_without_ext': name_without_ext,
                    'extension': extension
                })
            elif extension == '.stp':
                if '_' in name_without_ext:
                    files_analysis['stp_with_underscore'].append({
                        'path': file_path,
                        'name': filename,
                        'name_without_ext': name_without_ext,
                        'extension': extension
                    })
                else:
                    files_analysis['stp_clean'].append({
                        'path': file_path,
                        'name': filename,
                        'name_without_ext': name_without_ext,
                        'extension': extension
                    })
            else:
                files_analysis['other_files'].append({
                    'path': file_path,
                    'name': filename,
                    'name_without_ext': name_without_ext,
                    'extension': extension
                })
    
    return files_analysis

def extract_name_before_underscore(name):
    """
    从文件名中提取下划线前的部分
    支持多种下划线模式：_IN, _OUT, _V1, _V2 等
    """
    # 使用正则表达式匹配常见的下划线模式
    patterns = [
        r'^(.+?)_IN$',      # 匹配 _IN 结尾
        r'^(.+?)_OUT$',     # 匹配 _OUT 结尾
        r'^(.+?)_V\d+$',    # 匹配 _V1, _V2 等
        r'^(.+?)_\d+$',     # 匹配 _数字 结尾
        r'^(.+?)_[A-Z]+$',  # 匹配 _大写字母 结尾
    ]
    
    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            return match.group(1)
    
    # 如果没有匹配到特定模式，返回第一个下划线前的内容
    if '_' in name:
        return name.split('_')[0]
    
    return name

def process_files_complete(source_dir, logger):
    """
    完整处理所有文件：先处理.step文件，再处理带下划线的.stp文件
    """
    if not source_dir.exists():
        logger.log(f"错误: 目录 {source_dir} 不存在")
        return
    
    # 分析目录
    logger.log("分析目录文件...")
    analysis = analyze_directory(source_dir)
    
    if not analysis:
        logger.log("目录分析失败")
        return
    
    logger.log(f"找到 {len(analysis['step_files'])} 个.step文件")
    logger.log(f"找到 {len(analysis['stp_with_underscore'])} 个带下划线的.stp文件")
    logger.log(f"找到 {len(analysis['stp_clean'])} 个干净的.stp文件")
    logger.log(f"找到 {len(analysis['other_files'])} 个其他文件")
    logger.log("-" * 60)
    
    total_renamed = 0
    total_skipped = 0
    total_errors = 0
    
    # 第一步：处理.step文件
    if analysis['step_files']:
        logger.log("第一步：处理.step文件")
        logger.log("-" * 40)
        
        for file_info in analysis['step_files']:
            old_path = file_info['path']
            old_name = file_info['name']
            name_without_ext = file_info['name_without_ext']
            
            # 提取下划线前的名称
            new_name_base = extract_name_before_underscore(name_without_ext)
            new_filename = f"{new_name_base}.stp"
            new_path = source_dir / new_filename
            
            logger.log(f"处理: {old_name}")
            logger.log(f"  提取名称: {name_without_ext} -> {new_name_base}")
            
            # 检查目标文件是否已存在
            if new_path.exists():
                logger.log(f"  跳过: 目标文件 {new_filename} 已存在")
                total_skipped += 1
                continue
            
            try:
                old_path.rename(new_path)
                logger.log(f"  ✓ 重命名: {old_name} -> {new_filename}")
                total_renamed += 1
            except Exception as e:
                logger.log(f"  ✗ 错误: {old_name} - {str(e)}")
                total_errors += 1
            
            logger.log("")
    
    # 第二步：处理带下划线的.stp文件
    if analysis['stp_with_underscore']:
        logger.log("第二步：处理带下划线的.stp文件")
        logger.log("-" * 40)
        
        for file_info in analysis['stp_with_underscore']:
            old_path = file_info['path']
            old_name = file_info['name']
            name_without_ext = file_info['name_without_ext']
            
            # 提取下划线前的名称
            new_name_base = extract_name_before_underscore(name_without_ext)
            new_filename = f"{new_name_base}.stp"
            new_path = source_dir / new_filename
            
            logger.log(f"处理: {old_name}")
            logger.log(f"  提取名称: {name_without_ext} -> {new_name_base}")
            
            # 检查目标文件是否已存在
            if new_path.exists():
                logger.log(f"  跳过: 目标文件 {new_filename} 已存在")
                total_skipped += 1
                continue
            
            try:
                old_path.rename(new_path)
                logger.log(f"  ✓ 重命名: {old_name} -> {new_filename}")
                total_renamed += 1
            except Exception as e:
                logger.log(f"  ✗ 错误: {old_name} - {str(e)}")
                total_errors += 1
            
            logger.log("")
    
    # 打印最终统计
    logger.log("=" * 60)
    logger.log("处理完成!")
    logger.log(f"成功重命名: {total_renamed}")
    logger.log(f"跳过文件: {total_skipped}")
    logger.log(f"错误文件: {total_errors}")
    
    return {
        'renamed': total_renamed,
        'skipped': total_skipped,
        'errors': total_errors
    }

def process_files_safe(source_dir, logger):
    """
    安全模式：先显示将要进行的操作，询问用户确认
    """
    analysis = analyze_directory(source_dir)
    
    if not analysis:
        logger.log("目录分析失败")
        return
    
    # 收集所有需要重命名的文件
    files_to_rename = []
    
    # 处理.step文件
    for file_info in analysis['step_files']:
        old_name = file_info['name']
        name_without_ext = file_info['name_without_ext']
        new_name_base = extract_name_before_underscore(name_without_ext)
        new_filename = f"{new_name_base}.stp"
        
        files_to_rename.append({
            'old_name': old_name,
            'new_name': new_filename,
            'type': 'step'
        })
    
    # 处理带下划线的.stp文件
    for file_info in analysis['stp_with_underscore']:
        old_name = file_info['name']
        name_without_ext = file_info['name_without_ext']
        new_name_base = extract_name_before_underscore(name_without_ext)
        new_filename = f"{new_name_base}.stp"
        
        files_to_rename.append({
            'old_name': old_name,
            'new_name': new_filename,
            'type': 'stp_underscore'
        })
    
    if not files_to_rename:
        logger.log("没有需要重命名的文件")
        return
    
    # 显示将要进行的操作
    logger.log(f"将要重命名 {len(files_to_rename)} 个文件:")
    logger.log("-" * 40)
    
    for i, file_info in enumerate(files_to_rename[:10], 1):
        logger.log(f"{i}. {file_info['old_name']} -> {file_info['new_name']}")
    
    if len(files_to_rename) > 10:
        logger.log(f"  ... 还有 {len(files_to_rename) - 10} 个文件")
    
    # 询问用户确认
    confirm = input("\n确认要执行重命名操作吗? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        logger.log("用户取消操作")
        return
    
    # 执行重命名
    logger.log("开始执行重命名操作...")
    logger.log("-" * 40)
    
    total_renamed = 0
    total_skipped = 0
    total_errors = 0
    
    for file_info in files_to_rename:
        old_path = source_dir / file_info['old_name']
        new_path = source_dir / file_info['new_name']
        
        logger.log(f"处理: {file_info['old_name']} -> {file_info['new_name']}")
        
        # 检查目标文件是否已存在
        if new_path.exists():
            logger.log(f"  跳过: 目标文件已存在")
            total_skipped += 1
            continue
        
        try:
            old_path.rename(new_path)
            logger.log(f"  ✓ 重命名成功")
            total_renamed += 1
        except Exception as e:
            logger.log(f"  ✗ 错误: {str(e)}")
            total_errors += 1
        
        logger.log("")
    
    # 打印最终统计
    logger.log("=" * 60)
    logger.log("处理完成!")
    logger.log(f"成功重命名: {total_renamed}")
    logger.log(f"跳过文件: {total_skipped}")
    logger.log(f"错误文件: {total_errors}")

def show_current_status(source_dir, logger):
    """
    显示当前目录状态
    """
    analysis = analyze_directory(source_dir)
    
    if not analysis:
        logger.log("目录分析失败")
        return
    
    logger.log("当前目录状态:")
    logger.log("-" * 40)
    logger.log(f"总文件数: {len(analysis['step_files']) + len(analysis['stp_with_underscore']) + len(analysis['stp_clean']) + len(analysis['other_files'])}")
    logger.log(f".step文件: {len(analysis['step_files'])}")
    logger.log(f"带下划线的.stp文件: {len(analysis['stp_with_underscore'])}")
    logger.log(f"干净的.stp文件: {len(analysis['stp_clean'])}")
    logger.log(f"其他文件: {len(analysis['other_files'])}")
    
    if analysis['step_files']:
        logger.log("\n.step文件列表:")
        for file_info in analysis['step_files'][:5]:
            logger.log(f"  {file_info['name']}")
        if len(analysis['step_files']) > 5:
            logger.log(f"  ... 还有 {len(analysis['step_files']) - 5} 个")
    
    if analysis['stp_with_underscore']:
        logger.log("\n带下划线的.stp文件列表:")
        for file_info in analysis['stp_with_underscore'][:5]:
            logger.log(f"  {file_info['name']}")
        if len(analysis['stp_with_underscore']) > 5:
            logger.log(f"  ... 还有 {len(analysis['stp_with_underscore']) - 5} 个")
    
    if analysis['other_files']:
        logger.log("\n其他文件列表:")
        for file_info in analysis['other_files'][:5]:
            logger.log(f"  {file_info['name']}")
        if len(analysis['other_files']) > 5:
            logger.log(f"  ... 还有 {len(analysis['other_files']) - 5} 个")

def main():
    """
    主函数，支持命令行参数和模式选择
    """
    print("=" * 60)
    print("STEP文件重命名工具 - 支持DEBUG/RELEASE模式")
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
        print("1. DEBUG模式  (使用debug_traceparts和debug_processlog)")
        print("2. RELEASE模式 (使用release_traceparts和release_processlog)")
        
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
    print(f"输入目录: {config['input_dir']}")
    print(f"日志目录: {config['log_dir']}")
    print("-" * 60)
    
    # 检查输入目录是否存在
    input_dir = Path(config['input_dir'])
    if not input_dir.exists():
        print(f"错误: 输入目录不存在 {input_dir}")
        print("请确保目录存在并包含STEP文件")
        return
    
    # 创建日志记录器
    logger = Logger(config['log_dir'])
    logger.log(f"开始处理 - 模式: {mode}")
    logger.log(f"输入目录: {input_dir}")
    logger.log(f"日志目录: {config['log_dir']}")
    
    try:
        # 执行文件处理
        result = process_files_complete(input_dir, logger)
        
        if result:
            logger.log(f"处理完成 - 重命名: {result['renamed']}, 跳过: {result['skipped']}, 错误: {result['errors']}")
        else:
            logger.log("处理失败")
            
    except Exception as e:
        logger.log(f"处理过程中发生错误: {str(e)}")
    finally:
        logger.close()
        print(f"\n日志已保存到: {config['log_dir']}")

if __name__ == "__main__":
    main() 