import { join } from 'node:path';
import { app, BrowserWindow, shell } from 'electron';
import { startBackend, stopBackend } from './backend';

function createWindow(backendUrl: string): void {
  const window = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    show: false,
    autoHideMenuBar: true,
    title: 'Ticket AI Manager',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false,
      // Passa l'URL del backend (porta dinamica) al preload in modo affidabile.
      additionalArguments: [`--backend-url=${backendUrl}`],
    },
  });

  window.on('ready-to-show', () => window.show());

  // I link esterni si aprono nel browser, non nell'app.
  window.webContents.setWindowOpenHandler(({ url }) => {
    void shell.openExternal(url);
    return { action: 'deny' };
  });

  if (process.env.ELECTRON_RENDERER_URL) {
    void window.loadURL(process.env.ELECTRON_RENDERER_URL);
  } else {
    void window.loadFile(join(__dirname, '../renderer/index.html'));
  }
}

app.whenReady().then(async () => {
  // Avvia il backend (impacchettato o, in sviluppo, via venv) e attende che risponda.
  const backendUrl = await startBackend();
  createWindow(backendUrl);
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow(backendUrl);
  });
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => stopBackend());
