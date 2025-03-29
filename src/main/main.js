const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
// const isDev = require("electron-is-dev");
const fs = require("fs");

let mainWindow;
let currentPythonProcess = null; // 添加这行来跟踪当前的Python进程

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));

  // 添加这行，自动打开开发者工具
  //   if (isDev) {
  //     mainWindow.webContents.openDevTools();
  //   }
}

app.whenReady().then(async () => {
  // Install DevTools
  // if (process.env.NODE_ENV === 'development') {
  //   await installExtension(REACT_DEVELOPER_TOOLS)
  //     .then((name) => console.log(`Added Extension: ${name}`))
  //     .catch((err) => console.log('An error occurred: ', err));
  // }
  createWindow();

  if (app.isPackaged) {
    console.log(
      "Resources directory contents:",
      fs.readdirSync(path.join(process.resourcesPath))
    );
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

function getPythonPath() {
  const poetryEnv = spawn("poetry", ["env", "info", "-p"], {
    encoding: "utf8",
    shell: true,
  });

  return new Promise((resolve, reject) => {
    let envPath = "";

    poetryEnv.stdout.on("data", (data) => {
      envPath += data.toString();
    });

    poetryEnv.on("close", (code) => {
      if (code !== 0) {
        reject(new Error("Failed to get Poetry environment path"));
        return;
      }

      const pythonPath =
        process.platform === "win32"
          ? path.join(envPath.trim(), "Scripts", "python.exe")
          : path.join(envPath.trim(), "bin", "python");

      resolve(pythonPath);
    });
  });
}

ipcMain.handle("open-file-dialog", async (event) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openFile", "multiSelections"],
  });
  if (result.canceled) {
    return [];
  } else {
    return result.filePaths;
  }
});

ipcMain.handle("open-folder-dialog", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"], // Allows selecting folders only
  });

  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle("change-skin", async (event, root_data_dir) => {
  try {
    let pythonExecutablePath = "";
    let param;
    let basePath;

    if (app.isPackaged) {
      basePath = process.resourcesPath;
      // 直接使用打包后的可执行文件
      pythonExecutablePath = path.join(basePath, "python", "plot_courses");
      param = ["--root-data-dir", root_data_dir];

      // 确保文件有执行权限
      if (process.platform === "darwin" || process.platform === "linux") {
        try {
          fs.chmodSync(pythonExecutablePath, "755");
        } catch (error) {
          console.error("Failed to set executable permissions:", error);
        }
      }
    } else {
      basePath = path.join(__dirname, "../python/plot_courses.py");
      param = [basePath, "--root-data-dir", root_data_dir];
      pythonExecutablePath = await getPythonPath();
    }

    currentPythonProcess = spawn(pythonExecutablePath, param);

    let hasShownPreview = false; // 添加标志位

    return new Promise((resolve, reject) => {
      let result = "";
      let error = "";

      currentPythonProcess.stdout.on("data", (data) => {
        const output = data.toString();
        result += output;
        console.log("Python output:", output);

        // 只有还没展示过预览图时才处理
        if (!hasShownPreview && output.includes("Generated image:")) {
          try {
            const imagePath = output.split("Generated image:")[1].trim();
            mainWindow.webContents.send("update-preview", imagePath);
            hasShownPreview = true; // 设置标志位
          } catch (e) {
            console.error("Error parsing image path:", e);
          }
        }
      });

      currentPythonProcess.stderr.on("data", (data) => {
        error += data.toString();
        console.error("Python error details:", {
          error: data.toString(),
          pythonPath: pythonExecutablePath,
          params: param,
        });
      });

      currentPythonProcess.on("close", (code) => {
        currentPythonProcess = null; // 清除进程引用
        console.log("Python process exited with code:", code);
        if (code !== 0) {
          reject(error || "Process failed");
        } else {
          try {
            resolve(result);
          } catch (e) {
            reject(`Failed to parse result: ${result}`);
          }
        }
      });
    });
  } catch (error) {
    console.error("Error processing files:", error);
    throw error;
  }
});

// 修改abort处理部分
ipcMain.handle("abort-process", () => {
  if (currentPythonProcess) {
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", currentPythonProcess.pid, "/f", "/t"]);
    } else {
      currentPythonProcess.kill("SIGTERM");
    }
    currentPythonProcess = null;
    throw new Error("Process aborted");
  }
  return false;
});
