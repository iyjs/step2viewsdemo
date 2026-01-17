#!/bin/bash

# 3D STEP 多视角图像生成工具 - 快速启动脚本

echo "=================================="
echo "3D STEP 多视角图像生成工具"
echo "=================================="
echo ""

# 添加常用路径到 PATH
export PATH="/usr/local/bin:$PATH"

# 尝试多个可能的 conda 位置
CONDA_PATHS=(
    "/usr/local/bin/conda"
    "/usr/local/Caskroom/miniconda/base/bin/conda"
    "/opt/homebrew/Caskroom/miniconda/base/bin/conda"
    "$HOME/miniconda3/bin/conda"
    "$HOME/anaconda3/bin/conda"
)

CONDA_CMD=""
for conda_path in "${CONDA_PATHS[@]}"; do
    if [ -f "$conda_path" ]; then
        CONDA_CMD="$conda_path"
        echo "✓ 找到 conda: $CONDA_CMD"
        break
    fi
done

if [ -z "$CONDA_CMD" ]; then
    echo "❌ 错误: conda 未安装"
    echo "请先安装 Miniconda 或 Anaconda"
    echo "安装命令: /usr/local/bin/brew install --cask miniconda"
    echo "或访问: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# 初始化 conda
CONDA_BASE=$($CONDA_CMD info --base 2>/dev/null)
if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
    source "$CONDA_BASE/etc/profile.d/conda.sh"
else
    echo "⚠️  警告: 无法找到 conda.sh，尝试直接使用 conda"
fi

# 检查环境是否存在
if ! $CONDA_CMD env list | grep -q "3dsteps"; then
    echo "⚠️  环境 '3dsteps' 不存在，正在创建..."
    $CONDA_CMD create --name 3dsteps python=3.8 -y
    echo "✓ 环境创建成功"
    echo ""
    echo "正在安装依赖包..."
    conda activate 3dsteps
    $CONDA_CMD install -c conda-forge numpy pythonocc-core pyqt -y
    echo "✓ 依赖包安装完成"
else
    echo "✓ 环境 '3dsteps' 已存在"
fi

echo ""
echo "正在激活环境..."
conda activate 3dsteps

echo "✓ 环境已激活"
echo ""
echo "启动程序..."
echo ""

# 运行主程序
python 0step2multiviewAddlog.py
