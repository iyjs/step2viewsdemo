## 安装说明

### 1. 创建 Conda 虚拟环境

```bash
conda create --name 3dsteps python=3.8
conda activate 3dsteps
```

### 2. 安装依赖包

```bash
conda install -c conda-forge numpy pythonocc-core pyqt -y
```

### 3. 运行程序

```bash
python 0step2multiviewAddlog.py
```

### 环境重置（如遇到问题）

```bash
conda deactivate
conda remove -n 3dsteps --all  # 删除旧环境
conda create -n 3dsteps python=3.8  # 重新创建环境
conda activate 3dsteps
conda install -c conda-forge numpy pythonocc-core pyqt -y
```

### 参考资源

- [Online3DViewer](https://github.com/kovacsv/Online3DViewer)