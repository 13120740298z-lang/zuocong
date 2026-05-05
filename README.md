# Dumpling（小团子）桌宠

## 运行

```bash
npm install
npm start
```

如果 `npm install` 下载 Electron 失败，可以使用本项目自带的 `.npmrc` 镜像配置重试，或手动设置：

```bash
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
npm config set electron_builder_binaries_mirror https://npmmirror.com/mirrors/electron-builder-binaries/
npm install
```

## 配置 AI（OpenAI 兼容接口）

通过环境变量配置（推荐）：

- `DUMPLING_OPENAI_BASE_URL`（默认 `http://127.0.0.1:8000/v1`）
- `DUMPLING_OPENAI_API_KEY`（默认空）
- `DUMPLING_OPENAI_MODEL`（默认 `deepseek-chat`）

示例（PowerShell）：

```powershell
$env:DUMPLING_OPENAI_BASE_URL="http://127.0.0.1:8000/v1"
$env:DUMPLING_OPENAI_API_KEY="YOUR_KEY"
$env:DUMPLING_OPENAI_MODEL="deepseek-chat"
npm start
```

## 打包成 Windows .exe

```bash
npm run dist
```

产物会输出到 `dist/`，包含安装包（NSIS）与便携版（portable）的 `.exe`。
