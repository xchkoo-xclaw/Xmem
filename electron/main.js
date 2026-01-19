const { app, BrowserWindow, session } = require("electron");
const path = require("path");

/**
 * 获取生产模式下要加载的 index.html 路径。
 * - 打包后：前端静态资源会被拷贝到 process.resourcesPath/frontend-dist
 * - 本地直接运行（无 dev server）：使用仓库内 ../frontend/dist
 */
function resolveRendererIndexHtml() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "frontend-dist", "index.html");
  }
  return path.join(__dirname, "../frontend/dist/index.html");
}

/**
 * 修正 file:// 渲染进程访问线上后端时的 Origin/Referer。
 *
 * 说明：
 * - 本项目后端开启了基于 Origin 的 CSRF 校验；
 * - Electron 生产模式常见是 file:// 页面，浏览器会发出 Origin: null；
 * - 若线上环境配置了 CSRF_TRUSTED_ORIGINS（通常为 https://xmem.top），Origin: null 会被拒绝；
 * - 这里对发往 xmem.top 的请求，在 Origin 为空或为 null 时补齐为 https://xmem.top。
 */
function configureOnlineBackendRequestHeaders() {
  const trustedOrigin = "https://xmem.top";
  const isTargetHost = (hostname) => hostname === "xmem.top" || hostname.endsWith(".xmem.top");

  session.defaultSession.webRequest.onBeforeSendHeaders((details, callback) => {
    let hostname = "";
    try {
      hostname = new URL(details.url).hostname;
    } catch {
      callback({ requestHeaders: details.requestHeaders });
      return;
    }

    if (!isTargetHost(hostname)) {
      callback({ requestHeaders: details.requestHeaders });
      return;
    }

    const headers = { ...details.requestHeaders };
    const origin = headers.Origin ?? headers.origin;

    if (origin === undefined || origin === null || origin === "" || origin === "null") {
      headers.Origin = trustedOrigin;
      headers.Referer = `${trustedOrigin}/`;
    }

    callback({ requestHeaders: headers });
  });
}

/**
 * 创建应用主窗口。
 */
function createWindow() {
  const win = new BrowserWindow({
    width: 1123,
    height: 781,
    backgroundColor: "#f8f9fb",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
    show: false, // 先不显示，等加载完成后再显示
  });

  const devUrl = process.env.VITE_DEV_SERVER;
  if (devUrl) {
    // 确保 URL 格式正确
    const url = devUrl.startsWith("http") ? devUrl : `http://${devUrl}`;
    console.log("Loading dev server:", url);
    win.loadURL(url).catch((err) => {
      console.error("Failed to load URL:", err);
      win.webContents.once("did-fail-load", () => {
        console.error("页面加载失败，请确保前端开发服务器正在运行 (npm run dev in frontend/)");
      });
    });
  } else {
    const distPath = resolveRendererIndexHtml();
    console.log("Loading production build:", distPath);
    win.loadFile(distPath).catch((err) => {
      console.error("Failed to load file:", err);
    });
  }

  // 移除默认菜单栏（File、Edit、View 等）
  win.setMenuBarVisibility(false);
  win.setMenu(null);

  // 页面加载完成后显示窗口
  win.once("ready-to-show", () => {
    win.show();
    console.log("Window is ready and shown");
  });

  // 监听页面加载错误
  win.webContents.on("did-fail-load", (event, errorCode, errorDescription) => {
    if (errorCode !== -3) { // -3 是正常导航，忽略
      console.error(`页面加载失败 (${errorCode}): ${errorDescription}`);
    }
  });

  // 打开开发者工具以便调试（可通过环境变量控制）
  if (devUrl && process.env.OPEN_DEVTOOLS !== "false") {
    win.webContents.openDevTools();
  }
}

app.whenReady().then(() => {
  configureOnlineBackendRequestHeaders();
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

