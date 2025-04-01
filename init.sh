#!/bin/bash

echo "开始安装高尔夫球场地图生成工具的依赖..."

# 检查是否已安装 homebrew
if ! command -v brew &> /dev/null; then
    echo "正在安装 homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "homebrew 已安装"
fi

# 检查是否已安装 git
if ! command -v git &> /dev/null; then
    echo "正在安装 git..."
    brew install git
else
    echo "git 已安装"
fi

# 检查是否已安装 nvm
if ! command -v nvm &> /dev/null; then
    echo "正在安装 nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
else
    echo "nvm 已安装"
fi

# 配置 nvm 环境变量
echo "配置 nvm 环境变量..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# 检查是否已安装 Node.js
if ! command -v node &> /dev/null; then
    echo "正在安装 Node.js..."
    nvm install --lts
    nvm use --lts
else
    echo "Node.js 已安装"
fi

# 检查是否已安装 npm
if ! command -v npm &> /dev/null; then
    echo "正在安装 npm..."
    nvm install --lts
    nvm use --lts
else
    echo "npm 已安装"
fi

# 安装项目依赖
echo "正在安装项目依赖..."
npm install
npm update

# 检查是否已安装 Poetry
if ! command -v poetry &> /dev/null; then
    echo "正在安装 Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
else
    echo "Poetry 已安装"
fi

# 安装项目 Python 依赖
echo "正在安装项目 Python 依赖..."
poetry install --no-root
env activate

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p input_data output_data resources/icons resources/textures

echo "安装完成！"
echo "运行 'npm start' 来启动前端应用" 