# 本地开发环境使用指南

## 概述

这个本地开发环境让你可以在本地测试完整的前后端交互，而不需要部署到AWS。它完全模拟了云端的架构：

```
本地: 前端 → FastAPI → agent.py
云端: 前端 → API Gateway → Lambda → agent.py
```

## 快速开始

### 1. 安装依赖
```bash
# 安装本地开发依赖
pip install -r requirements-dev.txt
```

### 2. 设置AWS凭证
确保你的AWS凭证已设置（用于访问Bedrock）：
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token  # 如果使用临时凭证
```

### 3. 启动开发环境

#### 选项A：一键启动（推荐）
```bash
python local_dev_setup.py
```
这将自动：
- 启动API服务器 (端口 5000)
- 启动前端服务器 (端口 8000)
- 配置前端连接到本地API
- 打开浏览器

#### 选项B：手动启动
```bash
# 终端1: 启动API服务器
python local_server.py

# 终端2: 启动前端服务器
cd frontend
python -m http.server 8000

# 浏览器访问: http://localhost:8000
```

## 测试选项

### 1. 完整UI测试
访问 `http://localhost:8000` 测试完整的聊天界面

### 2. 纯Python测试
```bash
python test_agent.py
```
提供两种测试模式：
- 自动化测试：运行预设的测试用例
- 交互式测试：在终端中与AI对话

### 3. API测试
访问 `http://localhost:5000/docs` 查看API文档并测试

## 开发工作流

### 1. 修改业务逻辑
编辑 `src/agent.py` 中的代码

### 2. 本地测试
- Python测试: `python test_agent.py`
- 完整测试: 访问本地UI

### 3. 部署到云端
```bash
make deploy-dev
```

## 文件说明

- `local_server.py`: 本地FastAPI服务器，模拟AWS API Gateway + Lambda
- `test_agent.py`: 纯Python测试脚本，用于测试业务逻辑
- `local_dev_setup.py`: 一键启动本地开发环境
- `requirements-dev.txt`: 本地开发依赖
- `frontend/index_local.html`: 临时前端文件，配置为连接本地API

## 服务端点

- **API服务器**: `http://localhost:5000`
- **API文档**: `http://localhost:5000/docs`
- **健康检查**: `http://localhost:5000/health`
- **前端界面**: `http://localhost:8000`
- **聊天端点**: `http://localhost:5000/chat`

## 故障排除

### API服务器启动失败
```bash
# 检查端口是否被占用
lsof -i :5000

# 杀死占用进程
kill -9 <PID>
```

### AWS凭证问题
```bash
# 检查凭证
aws sts get-caller-identity

# 或使用AWS CLI配置
aws configure
```

### 依赖问题
```bash
# 重新安装依赖
pip install -r requirements-dev.txt --force-reinstall
```

## 开发提示

1. **热重载**: API服务器支持代码热重载，修改代码后自动重启
2. **调试**: 可以在代码中添加 `print()` 语句，输出会显示在API服务器的终端中
3. **错误信息**: 检查浏览器控制台和服务器终端获取详细错误信息
4. **端口冲突**: 如果端口被占用，可以修改 `local_server.py` 中的端口设置

## 与云端部署的区别

| 功能 | 本地开发 | 云端部署 |
|------|----------|----------|
| 入口点 | FastAPI | API Gateway + Lambda |
| 业务逻辑 | agent.py (相同) | agent.py (相同) |
| 前端 | 本地HTTP服务器 | S3静态网站 |
| 调试 | 直接在终端查看 | CloudWatch日志 |
| 成本 | 免费 | 按使用量计费 |

## 注意事项

- 本地开发文件不会影响云端部署
- `frontend/index_local.html` 是临时文件，会在停止开发环境时自动删除
- 确保AWS凭证有访问Bedrock的权限
- 本地开发环境仅用于开发和测试，不适合生产使用 