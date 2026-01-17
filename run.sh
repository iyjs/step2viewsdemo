#!/bin/bash

# 3D STEP 多视角图像生成工具 - 快速启动脚本

echo "=================================="
echo "3D STEP 多视角图像生成工具"
echo "=================================="
echo ""

# 检查 conda 是否已安装
if ! command -v conda &> /dev/null; then
    echo "❌ 错误: conda 未安装"
    echo "请先安装 Miniconda 或 Anaconda"
    echo "安装命令: brew install --cask miniconda"
    exit 1
fi

# 检查环境是否存在
if ! conda env list | grep -q "3dsteps"; then
    echo "⚠️  环境 '3dsteps' 不存在，正在创建..."
    conda create --name 3dsteps python=3.8 -y
    echo "✓ 环境创建成功"
    echo ""
    echo "正在安装依赖包..."
    conda activate 3dsteps
    conda install -c conda-forge numpy pythonocc-core pyqt -y
    echo "✓ 依赖包安装完成"
else
    echo "✓ 环境 '3dsteps' 已存在"
fi

echo ""
echo "正在激活环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate 3dsteps

echo "✓ 环境已激活"
echo ""
echo "启动程序..."
echo ""

# 运行主程序
python 0step2multiviewAddlog.py
