# TomGPT 用户指南 / User Guide

[中文](#中文指南) · [English](#english-guide) · [架构](ARCHITECTURE.md) · [部署](DEPLOYMENT.md) · [返回主页](../README.md)

---

## 中文指南

### 1. 安装前需要什么？

- Python 3.10+；建议使用当前仍受支持的稳定版本。
- `pip`、Python 虚拟环境和现代浏览器。
- 访问所选第三方模型服务的网络。
- Node.js 不是运行 TomGPT 的必需项，只用于 JavaScript 测试。

TomGPT 本身免费，默认不需要购买 SDK。第三方免费通道是独立服务，不提供永久 SLA，可能限流、变更或停止开放。

### 2. 如何安装？

```bash
git clone https://github.com/Tomhao10225101490/TomGPT.git
cd TomGPT
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

完整依赖包含 Flask、g4f 运行依赖及文档解析所需的 `pypdf2`、`python-docx`、`openpyxl`、`pandas`、`markitdown` 等。安装失败时先升级 `pip`，再查看最先出现的错误，而不是只看最后一行。

### 3. 如何启动？

```bash
python start_tomgpt.py
```

浏览器打开 <http://127.0.0.1:8080/chat/>。

可用参数：

```bash
python start_tomgpt.py --host 127.0.0.1 --port 8080
python start_tomgpt.py --host 0.0.0.0 --port 8080
python start_tomgpt.py --debug
```

- `127.0.0.1`：仅本机，默认且最安全。
- `0.0.0.0`：监听所有网卡，用于可信局域网；不是公网安全配置。
- `--debug`：增加诊断日志；公开日志前应检查敏感信息。

### 4. 如何开始聊天？

1. 打开聊天页。
2. 保持默认的 TomGPT 自动路由，或在模型菜单中选路由/模型。
3. 在输入框输入问题并发送。
4. 回答会通过流式连接逐步显示。
5. 可停止生成、重新生成、继续回答、复制、打印或导出消息。

普通对话保存在当前浏览器的 IndexedDB 数据库 `chat-db` / `conversations` 中。UI 设置和选项保存在 `localStorage`。隐私对话仅保存在页面内存中；刷新或关闭后不应依赖其继续存在。

> 本地保存不等于离线推理。发送消息时，提示词和必要附件会传给实际处理请求的第三方模型通道。

### 5. 如何选择模型？

#### TomGPT 自动适合什么情况？

自动模式适合日常使用。默认匿名池当前包含 Qwen、CopilotApp、OperaAria、Pollinations 和 TeachAnything。候选会按认证需求、是否可能弹出外部浏览器、稳定质量层级和实时健康分排序，再逐个尝试。

#### Free Advanced 四个路由有什么区别？

| 路由 | 用途 | 当前候选 |
|---|---|---|
| `free-advanced` | 日常高质量通用对话 | Qwen `qwen3.7-plus`、CopilotApp `smart`、Pollinations `gpt-oss` |
| `free-reasoning` | 推理、分析、复杂问题 | CopilotApp `reasoning`、Qwen `qwen3.7-plus`、Pollinations `gpt-oss` |
| `free-coding` | 编程与代码解释 | Qwen `qwen3-coder-plus`、Pollinations `kimi-code` |
| `free-multimodal` | 图片理解和多模态 | Qwen `qwen3.5-omni-plus`、OperaAria `aria` |

这些是当前源码中的路由映射，不保证每个候选此刻可用。新增规范模型还包括 `qwen-3.7-plus`、`qwen-3.7-max`、`qwen-3-coder-plus`、`qwen-3.5-omni-plus`、`gpt-oss-20b`、`llama-3.3-70b`、`kimi-k2.7-code`、`glm-5.2`。

#### 手动选择单一通道后还会自动换源吗？

会。`PreferredThenAny` 先尝试用户选择的通道；如果在输出内容前失败或空响应，它会显示自动切换提示并转入 `AnyProvider`，同时排除刚失败的通道。若通道已经输出部分内容后中断，系统保留一致的部分回答并提示重新生成，不会把另一通道的文本直接拼到后面。

### 6. 如何上传和分析文件？

点击输入区的附件按钮，选择文件后再发送。常见格式包括：

- 文档：PDF、DOC/DOCX、TXT、Markdown、RTF、ODT、EPUB。
- 表格：CSV、XLS/XLSX。
- 演示：PPT/PPTX（实际解析能力取决于安装的转换组件）。
- 图片：PNG、JPG/JPEG、GIF、WebP、BMP、SVG。

如果只上传文件而未写问题，前端会添加默认指令，请模型给出摘要、分析和要点。大文件可能超过解析器、上传或模型上下文限制；建议拆分并明确要分析的页码、章节或字段。

不要上传无权处理的机密、个人敏感信息、访问令牌、cookie 或私钥。附件必须发送给处理请求的第三方服务。

### 7. 如何识别图片？

1. 选择一张图片。
2. 输入“描述这张图片”“识别图中文字”或具体问题。
3. 默认路由检测到图片后使用视觉候选池。

“分析/识别图片”不会被误判为“生成图片”。若选中的单一模型不支持视觉，改用 `free-multimodal` 或 TomGPT 自动模式。

### 8. 如何生成图片？

直接输入明确的生图指令，例如：

- `生成一张雨夜中的未来城市插画`
- `Draw a flat vector logo of a blue whale`

在默认模型下，前后端意图检测会将请求强制路由到真实图片模型（首选 `flux`）。失败时只在 `gpt-image`、`flux-dev`、`sdxl-turbo`、`flux` 等已注册图片模型之间尝试，不会切回聊天模型并虚构图片 URL。

如果收到“图片生成失败，请再试一次”，说明当前可用图片候选都未成功。可以稍后重试、调整提示词，或选择另一个真实图片模型。

### 9. 如何导出 Word？

有三种入口：

1. 点击助手消息旁的 Word 导出按钮。
2. 对刚才的回答说“把上面的内容导出为 Word”。
3. 在请求内容时直接说明“生成后给我 Word 文档”。

前端调用 `/backend-api/v2/export/docx`，后端使用 `python-docx` 生成真实 `.docx` 文件。若提示缺少依赖：

```bash
python -m pip install python-docx
```

导出的是当前消息合并后的文本内容；复杂网页布局、交互组件和远程媒体不保证原样写入 Word。

### 10. 如何使用语音？

#### 语音输入

点击麦克风按钮，授权浏览器使用麦克风。TomGPT 使用浏览器 `SpeechRecognition` 或 `webkitSpeechRecognition` API，支持中间转写结果和持续识别。可以在设置中选择识别语言。

若没有麦克风按钮或无结果：

- 检查浏览器是否支持 Web Speech API。
- 检查站点麦克风权限。
- 优先在 `localhost` 或 HTTPS 页面使用；部分浏览器不允许非安全来源录音。
- Safari、Firefox 和不同地区的实现能力可能不同。

#### 朗读

当回复包含可用的合成音频地址时，点击扬声器按钮播放。语音模型列表和音频可能来自外部服务；网络、额度或服务状态会影响结果。

### 11. 如何在手机上访问？

仅在可信局域网内：

```bash
python start_tomgpt.py --host 0.0.0.0 --port 8080
```

查询电脑局域网 IP，然后在同一 Wi-Fi 的手机打开：

```text
http://<电脑局域网IP>:8080/chat/
```

如果打不开：

- 确认手机和电脑在同一网络，且不是隔离访客网络。
- 允许 Python 通过系统防火墙。
- 确认端口未被占用。
- 不要使用 README 中的占位符原样访问。

**安全警告：** 当前应用没有完整的用户登录、租户隔离、CSRF 策略、限流和滥用防护。不要将 Flask 开发服务器直接映射到公网。临时隧道和生产建议见[部署指南](DEPLOYMENT.md)。

### 12. 设置如何工作？

设置通常保存在当前站点来源的 `localStorage`，包括主题、动画开关、模型/通道偏好、语音选项等。聊天记录则保存在 IndexedDB，而不是同一个 `localStorage` 键中。

动态 UI 资源使用 `tomgpt-brand-11` 查询版本标识，帮助浏览器刷新 CSS/JavaScript 缓存。若升级后样式仍旧：

1. 强制刷新页面。
2. 清除该站点缓存，但注意不要误删仍需保留的 IndexedDB 对话。
3. 检查开发者工具 Network 中资源 URL 是否包含 `tomgpt-brand-11`。

关闭动画有两条路径：

- 设置中的“关闭动画”会添加 `no-animations` 状态。
- 操作系统启用减少动态效果后，CSS `prefers-reduced-motion: reduce` 会降低动画。

### 13. 如何配置可选 API Key 或代理？

TomGPT 默认免费池不要求购买 SDK。若你自愿配置自己有权使用的通道，可以根据 `example.env` 和上游 g4f 文档设置环境变量，例如 `G4F_PROXY` 或具体 provider 的 API Key。

安全原则：

- 不要把 `.env`、cookie JSON、HAR、token 或密钥提交到 Git。
- 不要把密钥贴到 issue、截图或调试日志。
- 只使用你有权访问的账号和服务。
- 服务端公开时不要让未授权用户读取或覆盖凭据。

## 常见问题 / FAQ

### 为什么启动后浏览器打不开？

确认终端中进程仍在运行，地址是 `http://127.0.0.1:8080/chat/`，并检查端口：

```bash
python start_tomgpt.py --port 8081
```

若 8081 可用，原端口可能被其他程序占用。

### 为什么出现 `ModuleNotFoundError`？

通常是虚拟环境未激活或依赖未装入当前 Python：

```bash
which python
python -m pip install -r requirements.txt
```

Windows 使用 `where python`。

### 为什么模型一直切换？

前序通道可能限流、返回空内容、会话过期或网络错误。自动切换是容错行为。调试模式可看到尝试顺序，但日志可能包含请求信息，不要公开原始日志。

### 为什么回答中途停止？

如果通道在已经开始输出后断开，TomGPT 不会拼接另一模型的答案，而会保留部分回答并提示“重新生成”。这样可避免上下文和风格不一致。

### 为什么图片上传后模型仍看不见？

模型或通道可能不支持视觉，或图片过大/格式异常。尝试 `free-multimodal`、压缩图片、转换为 PNG/JPEG，并明确写出识图问题。

### 为什么生图请求只返回错误？

TomGPT 刻意禁止聊天幻觉回退。当前真实图片通道都失败时，它宁可报错，也不会伪造“已生成图片”。

### 为什么 Word 无法下载？

检查 `python-docx`、响应状态和浏览器下载权限。标题会经过安全文件名处理；空内容不会调用导出接口。

### 为什么语音输入不可用？

浏览器可能不支持 Web Speech API、麦克风权限被拒绝，或当前页面不是允许录音的安全来源。使用支持的 Chromium 浏览器并从 localhost/HTTPS 访问。

### 为什么清理浏览器后对话消失？

聊天记录在浏览器 IndexedDB 内。清除站点数据、换浏览器、换设备或使用隐私窗口都会产生不同的本地存储空间。重要内容应及时导出。

### 免费模型会永远可用吗？

不会作此承诺。TomGPT 本身免费且不要求付费 SDK，但匿名第三方通道没有永久 SLA。自动切换可以提高成功率，不能保证第三方持续提供资源。

### 如何运行自检？

```bash
python -m etc.unittest
node g4f.dev/dist/js/tomgpt-intents.test.js
git diff --check
```

某些 Python 测试会因可选组件或平台条件跳过；以实际汇总为准。

---

## English Guide

### 1. What do I need?

Use Python 3.10+, `pip`, a virtual environment, a modern browser, and network access to the selected third-party AI services. Node.js is only required for the JavaScript intent test.

TomGPT is free software and its default route does not require a paid SDK. Independent anonymous services may rate-limit, change, or disappear and have no permanent SLA.

### 2. How do I install and start it?

```bash
git clone https://github.com/Tomhao10225101490/TomGPT.git
cd TomGPT
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python start_tomgpt.py
```

Open <http://127.0.0.1:8080/chat/>.

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python start_tomgpt.py
```

### 3. How do conversations work?

Choose TomGPT Auto or a model route, enter a prompt, and submit. The browser renders the SSE stream as it arrives. Normal conversations are stored in IndexedDB (`chat-db`, `conversations`); preferences use `localStorage`. Private conversations stay in page memory.

Local history does not mean offline inference: prompts and required attachments are sent to the external provider that processes the request.

### 4. Which free route should I use?

- `free-advanced`: general high-quality work.
- `free-reasoning`: analysis and reasoning.
- `free-coding`: programming tasks.
- `free-multimodal`: image understanding.

These are curated route definitions, not uptime guarantees. If a manually selected provider fails before producing content, `PreferredThenAny` can switch to the automatic pool. If a stream breaks after content starts, TomGPT preserves the partial answer instead of stitching in another model.

### 5. How do I analyze files and images?

Use the attachment control and add a specific question. Supported input selectors include PDF, DOC/DOCX, text, Markdown, CSV, spreadsheets, presentations, common images, and several other document types. Actual extraction depends on installed parsers and file structure.

An attached image routes the default model toward the vision pool. Recognition language such as “describe this photo” is deliberately distinguished from image-generation language.

### 6. How do I generate an image?

Write an explicit request such as `Generate a watercolor image of a lighthouse at dawn`. The default route forces a real image model, beginning with `flux`. On failure it tries registered image alternatives only. It never falls back to a chat model that could falsely claim an image was generated.

### 7. How do I export Word?

Click the Word action on an assistant message, ask to export the previous answer, or request Word as part of the prompt. The frontend calls `/backend-api/v2/export/docx`; the backend uses `python-docx` to return a real `.docx`.

### 8. How do voice features work?

Voice input uses the browser's `SpeechRecognition`/`webkitSpeechRecognition` API and therefore depends on browser support, microphone permission, language support, and secure-origin rules. Reply playback depends on a synthesis URL and the availability of an external voice provider.

### 9. How can my phone connect?

On a trusted LAN:

```bash
python start_tomgpt.py --host 0.0.0.0 --port 8080
```

Open `http://<computer-lan-ip>:8080/chat/` from a phone on the same Wi-Fi. Configure the OS firewall as needed.

Do not expose this development server directly to the public Internet. The current app does not implement a complete authentication and abuse-protection boundary. See [Deployment](DEPLOYMENT.md).

### 10. Where are settings stored?

UI preferences use browser `localStorage`; conversations use IndexedDB. Static assets carry the cache marker `tomgpt-brand-11`. The UI supports both an explicit no-animation setting and `prefers-reduced-motion`.

### FAQ

#### Why is a model slow or unavailable?

Anonymous services can rate-limit, queue, change endpoints, or fail. Automatic routing tries alternatives when possible. Retry later or configure a provider you are authorized to use.

#### Why did a partial answer stop?

TomGPT avoids mixing two providers in one response after output has started. It keeps the coherent partial answer and asks you to regenerate.

#### Why did my conversations disappear?

Clearing site data, changing browser/profile/device, or using private browsing creates or removes local IndexedDB storage. Export important material.

#### Will free providers always remain free?

There is no such guarantee. TomGPT's code is free and the default path avoids paid SDK requirements, but third-party services control their own access and quotas.

#### How do I troubleshoot?

Run with `--debug`, inspect the first meaningful terminal error, verify the active virtual environment, and execute:

```bash
python -m etc.unittest
node g4f.dev/dist/js/tomgpt-intents.test.js
```

Never publish raw logs until tokens, cookies, personal paths, prompts, and uploaded content have been removed.
