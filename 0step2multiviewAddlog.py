#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import numpy
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Display.SimpleGui import init_display
from OCC.Display.WebGl import threejs_renderer
import sys
import os
from OCC.Extend.ShapeFactory import translate_shp, rotate_shp_3_axis
import math
import time
import datetime
import gc
from OCC.Core.Graphic3d import Graphic3d_Camera
from pathlib import Path

class Logger:
    """
    日志记录器，同时输出到控制台和文件
    """
    def __init__(self, log_dir="step2viewdata/processlog_debug"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志文件名（包含时间戳）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"multiview_{timestamp}.log"
        
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

class ConfigManager:
    """
    配置管理器，处理不同运行模式的路径配置
    """
    def __init__(self, mode="debug", force_reprocess=False):
        self.mode = mode.lower()
        self.base_dir = "step2viewdata"
        self.force_reprocess = force_reprocess  # 是否强制重新处理已存在的文件
        
        if self.mode == "debug":
            self.input_dir = f"{self.base_dir}/debug_traceparts"
            self.output_dir = f"{self.base_dir}/debug_output"
            self.log_dir = f"{self.base_dir}/debug_processlog"
        elif self.mode == "release":
            self.input_dir = f"{self.base_dir}/release_traceparts"
            self.output_dir = f"{self.base_dir}/release_output"
            self.log_dir = f"{self.base_dir}/release_processlog"
        else:
            raise ValueError(f"不支持的运行模式: {mode}")
    
    def get_paths(self):
        """
        获取所有路径
        """
        return {
            'input_dir': self.input_dir,
            'output_dir': self.output_dir,
            'log_dir': self.log_dir,
            'mode': self.mode
        }
    
    def create_directories(self):
        """
        创建必要的目录
        """
        Path(self.input_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
    
    def validate_input_directory(self):
        """
        验证输入目录是否存在且包含.stp文件（不区分大小写）
        """
        input_path = Path(self.input_dir)
        if not input_path.exists():
            return False, f"输入目录不存在: {self.input_dir}"
        
        # 查找所有.stp和.STEP文件（不区分大小写）
        stp_files = list(input_path.glob("*.stp")) + list(input_path.glob("*.STP")) + \
                    list(input_path.glob("*.step")) + list(input_path.glob("*.STEP"))
        if not stp_files:
            return False, f"输入目录中没有找到STEP文件: {self.input_dir}"
        
        return True, f"找到 {len(stp_files)} 个STEP文件"

def format_time(seconds):
    """
    格式化时间显示
    """
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds:.2f}秒"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}小时{remaining_minutes}分{remaining_seconds:.2f}秒"

def fibonacci_sphere(samples=36, distance=5):
    """
    :param samples: number of views
    :param distance: distance from the center of the object
    :return: # samples points of view around the model
    """
    points = []
    phi = math.pi * (3. - math.sqrt(5.))  # golden angle in radians
    for i in range(samples):
        y = (1 - (i / float(samples - 1)) * 2) * distance   # y goes from 1 to -1
        radius = math.sqrt(distance * distance - y * y)  # radius at y
        theta = phi * i  # golden angle increment
        x = math.cos(theta) * radius
        z = math.sin(theta) * radius
        points.append((x, y, z))
        
    return points

def animate_viewpoint2(display, img_name, logger=None):
    """
    :param img_name: save name of the view
    :param logger: 日志记录器
    """
    if logger:
        logger.log("开始生成多视角图片...")
    
    display.FitAll()
    display.Context.UpdateCurrentViewer()

    cam = display.View.Camera()  # type: Graphic3d_Camera

    center = cam.Center()
    eye = cam.Eye()

    display.View.FitAll()
    eye_ = numpy.array([eye.X(), eye.Y(), eye.Z()])
    center_ = numpy.array([center.X(), center.Y(), center.Z()])
    distance = numpy.linalg.norm(eye_ - center_)

    points = fibonacci_sphere(samples=36, distance=distance)

    for i, point in enumerate(points):
        eye.SetX(point[0]+center_[0])
        eye.SetY(point[1]+center_[1])
        eye.SetZ(point[2]+center_[2])
        cam.SetEye(eye)

        display.View.FitAll()
        display.Context.UpdateCurrentViewer()
        name = img_name.replace(".jpeg", "_"+str(i)+".jpeg")
        display.View.Dump(name)
        
        if logger and (i + 1) % 10 == 0:  # 每10个视角记录一次进度
            logger.log(f"  生成进度: {i+1}/36")

def make_multiview_dataset_with_timing_and_logging(config):
    """
    Generate 36 2D views around of each 3D model of the STEP dataset and save them in the path specified by mvcnn_images_dir_path input
    增加时间统计和日志记录功能
    """
    # 获取配置路径
    models_dir_path = config.input_dir
    mvcnn_images_dir_path = config.output_dir
    
    # 创建日志记录器
    logger = Logger(config.log_dir)
    
    try:
        # 记录总体开始时间
        total_start_time = time.time()
        start_datetime = datetime.datetime.now()
        
        logger.log("=" * 80)
        logger.log(f"多视角图像生成工具 (运行模式: {config.mode.upper()})")
        logger.log("=" * 80)
        logger.log(f"开始时间: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.log(f"运行模式: {config.mode}")
        logger.log(f"强制重新处理: {'是' if config.force_reprocess else '否'}")
        logger.log(f"输入目录: {models_dir_path}")
        logger.log(f"输出目录: {mvcnn_images_dir_path}")
        logger.log(f"日志目录: {config.log_dir}")
        logger.log("-" * 80)
        
        # 验证输入目录
        is_valid, message = config.validate_input_directory()
        if not is_valid:
            logger.log(f"错误: {message}")
            return
        
        logger.log(message)
        
        # 确保输出目录存在
        if not os.path.exists(mvcnn_images_dir_path):
            os.makedirs(mvcnn_images_dir_path)
            logger.log("创建输出目录")
        
        # 获取所有.stp文件（不区分大小写）
        stp_files = [f for f in os.listdir(models_dir_path) if f.lower().endswith((".stp", ".step"))]
        total_files = len(stp_files)
        
        logger.log(f"找到 {total_files} 个STEP文件")
        logger.log("-" * 80)
        
        # 统计变量
        processed_files = 0
        skipped_files = 0
        error_files = 0
        total_processing_time = 0
        file_times = []
        
        # 处理每个文件
        for file_idx, file in enumerate(stp_files, 1):
            # 记录单个文件开始时间
            file_start_time = time.time()
            
            # 初始化状态变量
            success = False
            
            # 从文件名中提取类别名（不含扩展名）
            class_ = os.path.splitext(file)[0]
            
            logger.log(f"[{file_idx}/{total_files}] 处理模型: {file}")
            logger.log(f"  开始时间: {datetime.datetime.now().strftime('%H:%M:%S')}")
            
            # 为每个.stp文件创建对应的输出子目录
            output_subdir = os.path.join(mvcnn_images_dir_path, class_)
            if not os.path.exists(output_subdir):
                os.makedirs(output_subdir)
            
            # 设置输出图片的基本名称
            img_name = os.path.join(output_subdir, f"{class_}.jpeg")
            
            # 检查是否已经生成了图片（只检查第一个视角）
            # 如果force_reprocess为True，则强制重新处理
            first_view_exists = os.path.exists(img_name.replace(".jpeg", "_0.jpeg"))
            if not first_view_exists or config.force_reprocess:
                if first_view_exists and config.force_reprocess:
                    logger.log(f"  ⚠ 图片已存在，强制重新处理")
                try:
                    # 读取STEP文件
                    step_reader = STEPControl_Reader()
                    status = step_reader.ReadFile(os.path.join(models_dir_path, file))
                    
                    if status == IFSelect_RetDone:  # 检查状态
                        failsonly = False
                        step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
                        step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
                        
                        # 传输所有根实体
                        step_reader.TransferRoots()
                        _nbs = step_reader.NbShapes()
                        
                        if _nbs == 0:
                            logger.log(f"  错误: STEP文件中没有形状 {file}")
                            error_files += 1
                            continue
                        
                        # 获取合并后的形状
                        aResShape = step_reader.OneShape()
                        logger.log(f"  成功读取STEP文件，形状数量: {_nbs}")
                    else:
                        logger.log(f"  错误: 无法读取文件 {file}")
                        error_files += 1
                        continue
                    
                    # 尝试不同的显示后端
                    backends = ["pyqt5", "pyqt6", "pyside2"]
                    success = False
                    
                    for backend in backends:
                        try:
                            # 清理内存
                            gc.collect()
                            
                            logger.log(f"    尝试后端: {backend}")
                            
                            # 初始化显示
                            display, start_display, add_menu, add_function_to_menu = init_display(backend_str=backend)
                            
                            # 显示形状
                            display.DisplayShape(aResShape, update=True)
                            
                            # 生成多视角图片
                            animate_viewpoint2(display=display, img_name=img_name, logger=logger)
                            
                            success = True
                            logger.log(f"    后端 {backend} 成功")
                            break
                            
                        except Exception as e:
                            logger.log(f"    后端 {backend} 失败: {str(e)}")
                            continue
                    
                    if success:
                        processed_files += 1
                        logger.log(f"  ✓ 成功生成多视角图片")
                    else:
                        error_files += 1
                        logger.log(f"  ✗ 所有后端都失败了")
                        
                except Exception as e:
                    error_files += 1
                    logger.log(f"  ✗ 处理错误: {str(e)}")
            else:
                skipped_files += 1
                logger.log(f"  - 跳过 (图片已存在)")
            
            # 计算单个文件处理时间
            file_end_time = time.time()
            file_processing_time = file_end_time - file_start_time
            total_processing_time += file_processing_time
            
            file_times.append({
                'file': file,
                'time': file_processing_time,
                'status': 'success' if success else 'error' if error_files > 0 else 'skipped'
            })
            
            logger.log(f"  处理时间: {format_time(file_processing_time)}")
            logger.log(f"  累计时间: {format_time(total_processing_time)}")
            
            # 估算剩余时间
            if file_idx < total_files:
                avg_time_per_file = total_processing_time / file_idx
                remaining_files = total_files - file_idx
                estimated_remaining_time = avg_time_per_file * remaining_files
                logger.log(f"  预计剩余时间: {format_time(estimated_remaining_time)}")
            
            logger.log("-" * 80)
            
            # 清理内存
            gc.collect()
        
        # 计算总时间
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        end_datetime = datetime.datetime.now()
        
        # 打印详细统计报告
        logger.log("=" * 80)
        logger.log("处理完成! 详细统计报告")
        logger.log("=" * 80)
        logger.log(f"结束时间: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.log(f"总耗时: {format_time(total_time)}")
        logger.log(f"总文件数: {total_files}")
        logger.log(f"成功处理: {processed_files}")
        logger.log(f"跳过文件: {skipped_files}")
        logger.log(f"错误文件: {error_files}")
        logger.log(f"成功率: {(processed_files/total_files*100):.1f}%" if total_files > 0 else "0%")
        
        if processed_files > 0:
            avg_time = total_processing_time / processed_files
            logger.log(f"平均处理时间: {format_time(avg_time)}")
            
            # 显示最快和最慢的文件
            if file_times:
                successful_times = [ft for ft in file_times if ft['status'] == 'success']
                if successful_times:
                    fastest = min(successful_times, key=lambda x: x['time'])
                    slowest = max(successful_times, key=lambda x: x['time'])
                    logger.log(f"最快文件: {fastest['file']} ({format_time(fastest['time'])})")
                    logger.log(f"最慢文件: {slowest['file']} ({format_time(slowest['time'])})")
        
        logger.log("-" * 80)
        logger.log("处理时间详情:")
        for ft in file_times:
            status_symbol = "✓" if ft['status'] == 'success' else "✗" if ft['status'] == 'error' else "-"
            logger.log(f"  {status_symbol} {ft['file']}: {format_time(ft['time'])}")
        
        logger.log("=" * 80)
        
    except Exception as e:
        logger.log(f"程序执行出错: {str(e)}")
        import traceback
        logger.log(f"错误详情: {traceback.format_exc()}")
    
    finally:
        # 关闭日志记录器
        logger.close()
        print(f"\n日志已保存到: {logger.log_file}")

def make_multiview_dataset_with_timing(config):
    """
    Generate 36 2D views around of each 3D model of the STEP dataset and save them in the path specified by mvcnn_images_dir_path input
    增加时间统计功能
    """
    # 获取配置路径
    models_dir_path = config.input_dir
    mvcnn_images_dir_path = config.output_dir
    
    # 记录总体开始时间
    total_start_time = time.time()
    start_datetime = datetime.datetime.now()
    
    print("=" * 80)
    print(f"多视角图像生成工具 (运行模式: {config.mode.upper()})")
    print("=" * 80)
    print(f"开始时间: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"运行模式: {config.mode}")
    print(f"强制重新处理: {'是' if config.force_reprocess else '否'}")
    print(f"输入目录: {models_dir_path}")
    print(f"输出目录: {mvcnn_images_dir_path}")
    print("-" * 80)
    
    # 验证输入目录
    is_valid, message = config.validate_input_directory()
    if not is_valid:
        print(f"错误: {message}")
        return
    
    print(message)
    
    # 确保输出目录存在
    if not os.path.exists(mvcnn_images_dir_path):
        os.makedirs(mvcnn_images_dir_path)
        print("创建输出目录")
    
    # 获取所有.stp文件（不区分大小写）
    stp_files = [f for f in os.listdir(models_dir_path) if f.lower().endswith((".stp", ".step"))]
    total_files = len(stp_files)
    
    print(f"找到 {total_files} 个STEP文件")
    print("-" * 80)
    
    # 统计变量
    processed_files = 0
    skipped_files = 0
    error_files = 0
    total_processing_time = 0
    file_times = []
    
    # 处理每个文件
    for file_idx, file in enumerate(stp_files, 1):
        # 记录单个文件开始时间
        file_start_time = time.time()
        
        # 初始化状态变量
        success = False
        
        # 从文件名中提取类别名（不含扩展名）
        class_ = os.path.splitext(file)[0]
        
        print(f"[{file_idx}/{total_files}] 处理模型: {file}")
        print(f"  开始时间: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        # 为每个.stp文件创建对应的输出子目录
        output_subdir = os.path.join(mvcnn_images_dir_path, class_)
        if not os.path.exists(output_subdir):
            os.makedirs(output_subdir)
        
        # 设置输出图片的基本名称
        img_name = os.path.join(output_subdir, f"{class_}.jpeg")
        
        # 检查是否已经生成了图片（只检查第一个视角）
        # 如果force_reprocess为True，则强制重新处理
        first_view_exists = os.path.exists(img_name.replace(".jpeg", "_0.jpeg"))
        if not first_view_exists or config.force_reprocess:
            if first_view_exists and config.force_reprocess:
                print(f"  ⚠ 图片已存在，强制重新处理")
            try:
                # 读取STEP文件
                step_reader = STEPControl_Reader()
                status = step_reader.ReadFile(os.path.join(models_dir_path, file))
                
                if status == IFSelect_RetDone:  # 检查状态
                    failsonly = False
                    step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
                    step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
                    
                    # 传输所有根实体
                    step_reader.TransferRoots()
                    _nbs = step_reader.NbShapes()
                    
                    if _nbs == 0:
                        print(f"  错误: STEP文件中没有形状 {file}")
                        error_files += 1
                        continue
                    
                    # 获取合并后的形状
                    aResShape = step_reader.OneShape()
                else:
                    print(f"  错误: 无法读取文件 {file}")
                    error_files += 1
                    continue
                
                # 尝试不同的显示后端
                backends = ["pyqt5", "pyqt6", "pyside2"]
                success = False
                
                for backend in backends:
                    try:
                        # 清理内存
                        gc.collect()
                        
                        # 初始化显示
                        display, start_display, add_menu, add_function_to_menu = init_display(backend_str=backend)
                        
                        # 显示形状
                        display.DisplayShape(aResShape, update=True)
                        
                        # 生成多视角图片
                        animate_viewpoint2(display=display, img_name=img_name)
                        
                        success = True
                        break
                        
                    except Exception as e:
                        print(f"    后端 {backend} 失败: {str(e)}")
                        continue
                
                if success:
                    processed_files += 1
                    print(f"  ✓ 成功生成多视角图片")
                else:
                    error_files += 1
                    print(f"  ✗ 所有后端都失败了")
                    
            except Exception as e:
                error_files += 1
                print(f"  ✗ 处理错误: {str(e)}")
        else:
            skipped_files += 1
            print(f"  - 跳过 (图片已存在)")
        
        # 计算单个文件处理时间
        file_end_time = time.time()
        file_processing_time = file_end_time - file_start_time
        total_processing_time += file_processing_time
        
        file_times.append({
            'file': file,
            'time': file_processing_time,
            'status': 'success' if success else 'error' if error_files > 0 else 'skipped'
        })
        
        print(f"  处理时间: {format_time(file_processing_time)}")
        print(f"  累计时间: {format_time(total_processing_time)}")
        
        # 估算剩余时间
        if file_idx < total_files:
            avg_time_per_file = total_processing_time / file_idx
            remaining_files = total_files - file_idx
            estimated_remaining_time = avg_time_per_file * remaining_files
            print(f"  预计剩余时间: {format_time(estimated_remaining_time)}")
        
        print("-" * 80)
        
        # 清理内存
        gc.collect()
    
    # 计算总时间
    total_end_time = time.time()
    total_time = total_end_time - total_start_time
    end_datetime = datetime.datetime.now()
    
    # 打印详细统计报告
    print("=" * 80)
    print("处理完成! 详细统计报告")
    print("=" * 80)
    print(f"结束时间: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {format_time(total_time)}")
    print(f"总文件数: {total_files}")
    print(f"成功处理: {processed_files}")
    print(f"跳过文件: {skipped_files}")
    print(f"错误文件: {error_files}")
    print(f"成功率: {(processed_files/total_files*100):.1f}%" if total_files > 0 else "0%")
    
    if processed_files > 0:
        avg_time = total_processing_time / processed_files
        print(f"平均处理时间: {format_time(avg_time)}")
        
        # 显示最快和最慢的文件
        if file_times:
            successful_times = [ft for ft in file_times if ft['status'] == 'success']
            if successful_times:
                fastest = min(successful_times, key=lambda x: x['time'])
                slowest = max(successful_times, key=lambda x: x['time'])
                print(f"最快文件: {fastest['file']} ({format_time(fastest['time'])})")
                print(f"最慢文件: {slowest['file']} ({format_time(slowest['time'])})")
    
    print("-" * 80)
    print("处理时间详情:")
    for ft in file_times:
        status_symbol = "✓" if ft['status'] == 'success' else "✗" if ft['status'] == 'error' else "-"
        print(f"  {status_symbol} {ft['file']}: {format_time(ft['time'])}")
    
    print("=" * 80)

def make_multiview_dataset_simple_timing(config):
    """
    简化版本的时间统计
    """
    # 获取配置路径
    models_dir_path = config.input_dir
    mvcnn_images_dir_path = config.output_dir
    
    total_start_time = time.time()
    
    print(f"开始处理: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"运行模式: {config.mode}")
    print(f"输入目录: {models_dir_path}")
    print(f"输出目录: {mvcnn_images_dir_path}")
    
    # 验证输入目录
    is_valid, message = config.validate_input_directory()
    if not is_valid:
        print(f"错误: {message}")
        return
    
    print(message)
    
    # 确保输出目录存在
    if not os.path.exists(mvcnn_images_dir_path):
        os.makedirs(mvcnn_images_dir_path)
    
    # 获取所有.stp文件（不区分大小写）
    stp_files = [f for f in os.listdir(models_dir_path) if f.lower().endswith((".stp", ".step"))]
    total_files = len(stp_files)
    
    print(f"找到 {total_files} 个STEP文件")
    
    processed_files = 0
    skipped_files = 0
    error_files = 0
    
    for file_idx, file in enumerate(stp_files, 1):
        file_start_time = time.time()
        
        class_ = os.path.splitext(file)[0]
        print(f"[{file_idx}/{total_files}] 处理: {file}")
        
        output_subdir = os.path.join(mvcnn_images_dir_path, class_)
        if not os.path.exists(output_subdir):
            os.makedirs(output_subdir)
        
        img_name = os.path.join(output_subdir, f"{class_}.jpeg")
        
        if not os.path.exists(img_name.replace(".jpeg", "_0.jpeg")):
            try:
                # 读取STEP文件
                step_reader = STEPControl_Reader()
                status = step_reader.ReadFile(os.path.join(models_dir_path, file))
                
                if status == IFSelect_RetDone:
                    # 传输所有根实体
                    step_reader.TransferRoots()
                    _nbs = step_reader.NbShapes()
                    
                    if _nbs == 0:
                        print(f"  错误: STEP文件中没有形状 {file}")
                        error_files += 1
                        continue
                    
                    # 获取合并后的形状
                    aResShape = step_reader.OneShape()
                    
                    # 显示和渲染3D模型
                    display, start_display, add_menu, add_function_to_menu = init_display()
                    display.DisplayShape(aResShape, update=True)
                    
                    # 生成多视角图片
                    animate_viewpoint2(display=display, img_name=img_name)
                    
                    processed_files += 1
                    print(f"  ✓ 成功")
                else:
                    error_files += 1
                    print(f"  ✗ 读取失败")
                    
            except Exception as e:
                error_files += 1
                print(f"  ✗ 错误: {str(e)}")
        else:
            skipped_files += 1
            print(f"  - 跳过")
        
        file_time = time.time() - file_start_time
        print(f"  时间: {format_time(file_time)}")
    
    total_time = time.time() - total_start_time
    
    print(f"\n完成! 总时间: {format_time(total_time)}")
    print(f"成功: {processed_files}, 跳过: {skipped_files}, 错误: {error_files}")

def show_config_info(config):
    """
    显示配置信息
    """
    print("=" * 60)
    print("当前配置信息")
    print("=" * 60)
    print(f"运行模式: {config.mode.upper()}")
    print(f"输入目录: {config.input_dir}")
    print(f"输出目录: {config.output_dir}")
    print(f"日志目录: {config.log_dir}")
    
    # 检查目录状态
    input_path = Path(config.input_dir)
    output_path = Path(config.output_dir)
    log_path = Path(config.log_dir)
    
    print("\n目录状态:")
    print(f"输入目录: {'存在' if input_path.exists() else '不存在'}")
    if input_path.exists():
        stp_files = list(input_path.glob("*.stp")) + list(input_path.glob("*.STP")) + \
                    list(input_path.glob("*.step")) + list(input_path.glob("*.STEP"))
        print(f"  - STEP文件数量: {len(stp_files)}")
    
    print(f"输出目录: {'存在' if output_path.exists() else '不存在'}")
    print(f"日志目录: {'存在' if log_path.exists() else '不存在'}")
    
    print("=" * 60)

if __name__ == "__main__":
    print("多视角图像生成工具")
    print("=" * 60)
    print("运行模式:")
    print("1. DEBUG模式 - 使用debug_前缀目录")
    print("2. RELEASE模式 - 使用release_前缀目录")
    print("3. 显示配置信息")
    print("=" * 60)
    
    mode_choice = input("请选择运行模式 (1/2/3): ").strip()
    
    if mode_choice == "1":
        mode = "debug"
    elif mode_choice == "2":
        mode = "release"
    elif mode_choice == "3":
        # 显示配置信息
        try:
            config = ConfigManager("debug")
            show_config_info(config)
            print("\nDEBUG模式配置:")
            show_config_info(config)
            
            config = ConfigManager("release")
            print("\nRELEASE模式配置:")
            show_config_info(config)
        except Exception as e:
            print(f"显示配置信息时出错: {str(e)}")
        exit()
    else:
        print("无效选择，使用DEBUG模式...")
        mode = "debug"
    
    # 询问是否强制重新处理已存在的文件
    print("=" * 60)
    reprocess_choice = input("是否重新处理已存在的文件? (y/n，默认n): ").strip().lower()
    force_reprocess = (reprocess_choice == 'y' or reprocess_choice == 'yes')
    
    if force_reprocess:
        print("⚠ 将重新处理所有文件（包括已存在的）")
    else:
        print("✓ 将跳过已处理的文件")
    
    try:
        # 创建配置管理器
        config = ConfigManager(mode, force_reprocess=force_reprocess)
        
        # 创建必要的目录
        config.create_directories()
        
        # 显示配置信息
        show_config_info(config)
        
        print("\n选择处理模式:")
        print("1. 详细时间统计 + 日志记录 (推荐)")
        print("2. 详细时间统计 (无日志)")
        print("3. 简化时间统计")
        
        choice = input("请选择 (1/2/3): ").strip()
        
        if choice == "1":
            make_multiview_dataset_with_timing_and_logging(config)
        elif choice == "2":
            make_multiview_dataset_with_timing(config)
        elif choice == "3":
            make_multiview_dataset_simple_timing(config)
        else:
            print("无效选择，使用推荐模式...")
            make_multiview_dataset_with_timing_and_logging(config)
            
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}") 