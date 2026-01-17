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

def animate_viewpoint2(display, img_name):
    """
    :param img_name: save name of the view
    """
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

def make_multiview_dataset_with_timing(models_dir_path, mvcnn_images_dir_path):
    """
    Generate 36 2D views around of each 3D model of the STEP dataset and save them in the path specified by mvcnn_images_dir_path input
    增加时间统计功能
    """
    # 记录总体开始时间
    total_start_time = time.time()
    start_datetime = datetime.datetime.now()
    
    print("=" * 80)
    print("多视角图像生成工具 (带时间统计)")
    print("=" * 80)
    print(f"开始时间: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输入目录: {models_dir_path}")
    print(f"输出目录: {mvcnn_images_dir_path}")
    print("-" * 80)
    
    # 确保输出目录存在
    if not os.path.exists(mvcnn_images_dir_path):
        os.makedirs(mvcnn_images_dir_path)
        print("创建输出目录")
    
    # 获取所有.stp文件
    stp_files = [f for f in os.listdir(models_dir_path) if f.endswith(".stp")]
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
        
        # 从文件名中提取类别名（不含扩展名）
        class_ = file.replace(".stp", "")
        
        print(f"[{file_idx}/{total_files}] 处理模型: {file}")
        print(f"  开始时间: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        # 为每个.stp文件创建对应的输出子目录
        output_subdir = os.path.join(mvcnn_images_dir_path, class_)
        if not os.path.exists(output_subdir):
            os.makedirs(output_subdir)
        
        # 设置输出图片的基本名称
        img_name = os.path.join(output_subdir, f"{class_}.jpeg")
        
        # 检查是否已经生成了图片（只检查第一个视角）
        if not os.path.exists(img_name.replace(".jpeg", "_0.jpeg")):
            try:
                # 读取STEP文件
                step_reader = STEPControl_Reader()
                status = step_reader.ReadFile(os.path.join(models_dir_path, file))
                
                if status == IFSelect_RetDone:  # 检查状态
                    failsonly = False
                    step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
                    step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
                    
                    ok = step_reader.TransferRoot(1)
                    _nbs = step_reader.NbShapes()
                    aResShape = step_reader.Shape(1)
                else:
                    print(f"  错误: 无法读取文件 {file}")
                    error_files += 1
                    continue
                
                # 尝试不同的显示后端
                backends = ["qt-pyqt5", "qt-pyside2", "qt-pyside6"]
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

def make_multiview_dataset_simple_timing(models_dir_path, mvcnn_images_dir_path):
    """
    简化版本的时间统计
    """
    total_start_time = time.time()
    
    print(f"开始处理: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 确保输出目录存在
    if not os.path.exists(mvcnn_images_dir_path):
        os.makedirs(mvcnn_images_dir_path)
    
    # 获取所有.stp文件
    stp_files = [f for f in os.listdir(models_dir_path) if f.endswith(".stp")]
    total_files = len(stp_files)
    
    print(f"找到 {total_files} 个STEP文件")
    
    processed_files = 0
    skipped_files = 0
    error_files = 0
    
    for file_idx, file in enumerate(stp_files, 1):
        file_start_time = time.time()
        
        class_ = file.replace(".stp", "")
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
                    step_reader.TransferRoot(1)
                    aResShape = step_reader.Shape(1)
                    
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

if __name__ == "__main__":
    path_step = "step2viewdata/traceparts_debug/"
    path_multiview = "step2viewdata/output_debug/"
    
    print("选择处理模式:")
    print("1. 详细时间统计 (推荐)")
    print("2. 简化时间统计")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "2":
        make_multiview_dataset_simple_timing(path_step, path_multiview)
    else:
        make_multiview_dataset_with_timing(path_step, path_multiview) 