#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到脚本所在目录
cd "$DIR"

# 执行初始化脚本
./init.sh

# 执行完成后等待用户按任意键退出
echo "按任意键退出..."
read -n 1 