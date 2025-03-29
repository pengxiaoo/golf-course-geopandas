#!/bin/bash

# 确保脚本在出错时停止执行
set -e

echo "=== 开始构建应用 ==="

# 进入 Python 目录并执行 Python 打包
echo "1. 打包 Python 脚本..."
cd src/python
rm -rf dist
rm -rf build
sh build_python.sh

# 返回项目根目录
echo "2. 返回项目根目录..."
cd ../..

# 执行 Electron 打包
echo "3. 打包 Electron 应用..."
rm -rf dist
npm run build

echo "=== 构建完成 ==="

# 显示输出目录内容
echo "检查构建输出:"
ls -la dist/ 