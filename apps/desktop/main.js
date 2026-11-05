// Lumière desktop shell.
// A locked-down Chromium window around the live site: no Node access in the page,
// navigation restricted to our own origin, external links open in the real browser.
const { app, BrowserWindow, Menu, shell, session } = require("electron");
const fs = require("fs");
const path = require("path");

const HOME_URL = "https://movies.creativeclicks.art/";
const ALLOWED_HOST = "movies.creativeclicks.art";
const BG = "#08090c";

if (!app.requestSingleInstanceLock()) {
  app.quit();
}

let win = null;
const stateFile = () => path.join(app.getPath("userData"), "window-state.json");

function loadState() {
  try {
    return JSON.parse(fs.readFileSync(stateFile(), "utf8"));
  } catch {
    return { width: 1360, height: 840 };
  }
}

function saveState() {
  if (!win || win.isDestroyed()) return;
  try {
    const b = win.getNormalBounds();
    fs.writeFileSync(
      stateFile(),
      JSON.stringify({ ...b, maximized: win.isMaximized() })
    );
  } catch {
    /* non-fatal */
  }
}

function isInternal(url) {
  try {
    const u = new URL(url);
    return u.protocol === "https:" && u.hostname.toLowerCase() === ALLOWED_HOST;
  } catch {
    return false;
  }
}

function openExternalSafely(url) {
  try {
    const u = new URL(url);
    if (u.protocol === "https:" || u.protocol === "mailto:") shell.openExternal(url);
  } catch {
    /* ignore */
  }
}

function createWindow() {
  const st = loadState();
  win = new BrowserWindow({
    width: st.width || 1360,
    height: st.height || 840,
    x: st.x,
    y: st.y,
    minWidth: 360,
    minHeight: 560,
    backgroundColor: BG,
    title: "Lumière",
    icon: path.join(__dirname, "build", "icon.png"),
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      spellcheck: false,
    },
  });

  if (st.maximized) win.maximize();
  win.once("ready-to-show", () => win.show());

  const ua = win.webContents.getUserAgent().replace(/\sElectron\/\S+/, "");
  win.webContents.setUserAgent(`${ua} LumiereDesktop/1.0`);

  win.webContents.on("will-navigate", (event, url) => {
    if (url.startsWith("file://")) return; // our own offline page
    if (!isInternal(url)) {
      event.preventDefault();
      openExternalSafely(url);
    }
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (isInternal(url)) {
      win.loadURL(url);
    } else {
      openExternalSafely(url);
    }
    return { action: "deny" };
  });

  win.webContents.on("did-fail-load", (_e, code, _desc, url, isMainFrame) => {
    if (!isMainFrame || code === -3 /* aborted */) return;
    if (url && url.startsWith("file://")) return;
    win.loadFile(path.join(__dirname, "offline.html"));
  });

  // F11 / Esc fullscreen like a real media app
  win.webContents.on("before-input-event", (event, input) => {
    if (input.type !== "keyDown") return;
    if (input.key === "F11") {
      win.setFullScreen(!win.isFullScreen());
      event.preventDefault();
    } else if (input.key === "Escape" && win.isFullScreen() && !win.webContents.isDevToolsOpened()) {
      // let the page's own fullscreen handler run first; only force-exit window fullscreen
      setTimeout(() => {
        if (win && !win.isDestroyed() && win.isFullScreen() && !win.webContents.isLoading()) {
          win.webContents
            .executeJavaScript("!!document.fullscreenElement")
            .then((pageFs) => {
              if (!pageFs && win && !win.isDestroyed()) win.setFullScreen(false);
            })
            .catch(() => {});
        }
      }, 120);
    }
  });

  win.on("close", saveState);
  win.on("closed", () => {
    win = null;
  });

  win.loadURL(HOME_URL);
}

app.on("second-instance", () => {
  if (win) {
    if (win.isMinimized()) win.restore();
    win.focus();
  }
});

app.whenReady().then(() => {
  // The site never needs camera / mic / location / notifications; allow fullscreen only.
  session.defaultSession.setPermissionRequestHandler((_wc, permission, cb) => {
    cb(permission === "fullscreen");
  });
  session.defaultSession.setPermissionCheckHandler((_wc, permission) => permission === "fullscreen");

  if (process.platform === "darwin") {
    Menu.setApplicationMenu(
      Menu.buildFromTemplate([
        { role: "appMenu" },
        { role: "editMenu" },
        { role: "viewMenu" },
        { role: "windowMenu" },
      ])
    );
  } else {
    Menu.setApplicationMenu(null);
  }

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
