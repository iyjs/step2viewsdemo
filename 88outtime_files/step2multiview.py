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
        
        ass = math.sqrt(math.pow(x,2)+math.pow(y,2)+math.pow(z,2) )
        
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


def make_multiview_dataset(models_dir_path, mvcnn_images_dir_path):
    """
    Generate 36 2D views around of each 3D model of the STEP dataset and save them in the path specified by mvcnn_images_dir_path input
    :param models_dir_path: path of the input step dataset (.stp files)
    :param mvcnn_images_dir_path: path of the output multi views dataset
    """
    # 确保输出目录存在
    if not os.path.exists(mvcnn_images_dir_path):
        os.makedirs(mvcnn_images_dir_path)
    
    # 获取所有.stp文件（只处理直接位于traceparts目录下的文件）
    for file in os.listdir(models_dir_path):
        if file.endswith(".stp"):
            # 从文件名中提取类别名（不含扩展名）
            class_ = file.replace(".stp", "")
            
            print(f"--- 处理模型: {file}")
            
            # 为每个.stp文件创建对应的输出子目录
            output_subdir = os.path.join(mvcnn_images_dir_path, class_)
            if not os.path.exists(output_subdir):
                os.makedirs(output_subdir)
            
            # 设置输出图片的基本名称
            img_name = os.path.join(output_subdir, f"{class_}.jpeg")
            
            # 检查是否已经生成了图片（只检查第一个视角）
            if not os.path.exists(img_name.replace(".jpeg", "_0.jpeg")):
                # 读取STEP文件
                step_reader = STEPControl_Reader()
                status = step_reader.ReadFile(os.path.join(models_dir_path, file))
                
                if status == IFSelect_RetDone:  # 检查状态
                    failsonly = False
                    step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
                    step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)

                    # 检查有多少个roots可以转换
                    nbr = step_reader.NbRootsForTransfer()
                    print(f"文件 {file} 有 {nbr} 个roots可转换")

                    if nbr == 0:
                        print(f"警告: 文件 {file} 没有可转换的roots,跳过")
                        continue

                    # 转换所有roots (推荐方法)
                    step_reader.TransferRoots()

                    # 检查转换后的shape数量
                    _nbs = step_reader.NbShapes()
                    print(f"转换后得到 {_nbs} 个shapes")

                    if _nbs == 0:
                        print(f"警告: 文件 {file} 转换后没有生成shape,跳过")
                        continue

                    # 获取所有shape的复合体
                    aResShape = step_reader.OneShape()
                else:
                    print(f"错误: 无法读取文件 {file}")
                    continue
                
                # 显示和渲染3D模型
                display, start_display, add_menu, add_function_to_menu = init_display()
                display.DisplayShape(aResShape, update=True)
                
                # 生成多视角图片
                animate_viewpoint2(display=display, img_name=img_name)
                
                print(f"已为 {file} 生成多视角图片")
            else:
                print(f"跳过 {file} - 图片已存在")


if __name__ == "__main__":
    path_step = "step2viewdata/traceparts/"
    path_multiview = "step2viewdata/output/"

    make_multiview_dataset(path_step, path_multiview)



