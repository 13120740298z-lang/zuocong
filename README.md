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

---

# Python/tkinter 版本（团子.py）

项目根目录已同时提供 `团子.py` 与 `build.bat`（Windows）。

## 一键打包并运行（推荐）

双击 `build.bat`：
- 如果已经存在 `dist\团子.exe`，会直接运行
- 否则会自动生成 `团子.ico`、安装 PyInstaller、打包单文件 exe，然后自动启动

## AI 配置

编辑 `团子.py` 顶部：
- `API_URL`（OpenAI 兼容接口，例如 `http://127.0.0.1:8000/v1`）
- `API_KEY`（留空则走本地拟人化回复）
- `MODEL`（默认 `deepseek-chat`）

## 如果你想“我什么都不做就拿到 exe”

可以把仓库推到 GitHub，然后在 Actions 里手动运行工作流 `.github/workflows/build-windows-exe.yml`，构建产物会以 artifact 形式提供下载（`团子.exe`）。
