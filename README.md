# TomGPT

基于 [gpt4free (g4f)](https://github.com/xtekky/gpt4free) 复刻的私人 GPT 网页应用。

**TomGPT 完全免费、本地运行**：不挖矿积分（Cake Baker）、不强制会员、不跳转付费页。对话数据留在你自己的电脑上。

本地 Web UI 已品牌化为 **TomGPT**，后端使用 g4f 的多供应商聚合能力。

## 快速开始

```bash
cd ~/Projects/TomGPT
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python start_tomgpt.py
```

浏览器打开：<http://127.0.0.1:8080/chat/>

## 文件上传（PDF / Word / 图片等）

聊天输入框旁的回形针可上传文件，和消息一起发给 TomGPT：

| 类型 | 常见格式 |
|------|----------|
| 文档 | PDF、Word（`.docx`）、TXT、Markdown、CSV |
| 表格 | Excel（`.xlsx`） |
| 图片 | PNG、JPG、GIF、WebP 等 |

依赖已写入 `requirements.txt`（`pypdf2`、`python-docx`、`openpyxl`、`pandas`、`markitdown`）。装好后重启即可。

## 自动换源（TomGPT）

默认使用 **TomGPT 自动**（`AnyProvider`）：
- 某个接口失败时，会自动切换到下一个可用接口
- 即使你手动选了单一供应商，失败后也会自动回退到多接口轮询
- 界面会提示「已自动切换」，尽量不打断对话

可选参数：

```bash
python start_tomgpt.py --host 0.0.0.0 --port 8080 --debug
```

也可用原生命令：

```bash
python -m g4f.cli gui --port 8080 --debug
```

## 项目结构（关键）

| 路径 | 说明 |
|------|------|
| `g4f/` | gpt4free 核心库与 GUI 服务端 |
| `g4f.dev/` | 本地化前端（已改成 TomGPT 品牌） |
| `start_tomgpt.py` | 一键启动脚本 |
| `example.env` | 可选 API Key / 代理配置模板 |

## 配置（可选）

复制 `example.env` 到 cookies 目录或按需设置环境变量，例如：

- `G4F_API_KEY`
- `G4F_PROXY`
- `OPENAI_API_KEY` / `GROQ_API_KEY` / `OPENROUTER_API_KEY` 等

## 说明

- 上游仓库保留为 git remote `upstream`，便于后续同步更新。
- TomGPT 仅做本地品牌化与个人使用封装；请遵守各模型供应商服务条款与当地法律。
- 原项目许可证为 GPL-3.0，本复刻同样遵循该许可证。

## 致谢

- [xtekky/gpt4free](https://github.com/xtekky/gpt4free)
- [gpt4free/g4f.dev](https://github.com/gpt4free/g4f.dev)
