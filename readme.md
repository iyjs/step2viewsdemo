## Installation

Create Conda virtual environment:

```
conda create --name 3D_STEP_Classification python=3.8
conda activate 3D_STEP_Classification
```
conda install -c conda-forge pythonocc-core

$ python 0step2multiviewAddlog.py 


碰到环境安装问题可以初始化重新安装
conda deactivate
conda remove -n 3D_STEP_Classification --all  # 删除旧环境
conda create -n 3D_STEP_Classification python=3.8  # 推荐Python 3.9/3.10[2,5](@ref)
conda activate 3D_STEP_Classification
conda install -c conda-forge pythonocc-core pyqt  # 同时安装PythonOCC和PyQt5

conda install -c conda-forge numpy pythonocc-core


碰到环境安装问题可以初始化重新安装
conda deactivate
conda remove -n 3DSTEP --all  # 删除旧环境
conda create -n 3DSTEP python=3.8  # 推荐Python 3.9/3.10[2,5](@ref)
conda activate 3DSTEP
conda install -c conda-forge pythonocc-core pyqt  # 同时安装PythonOCC和PyQt5

conda install -c conda-forge numpy pythonocc-core


https://github.com/kovacsv/Online3DViewer