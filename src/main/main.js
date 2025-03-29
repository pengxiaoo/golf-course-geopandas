const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));

}

app.whenReady().then(async () => {
    // Install DevTools
    // if (process.env.NODE_ENV === 'development') {
    //   await installExtension(REACT_DEVELOPER_TOOLS)
    //     .then((name) => console.log(`Added Extension: ${name}`))
    //     .catch((err) => console.log('An error occurred: ', err));
    // }
    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

function getPythonPath() {
    const poetryEnv = spawn('poetry', ['env', 'info', '-p'], {
        encoding: 'utf8',
        shell: true
    })

    return new Promise((resolve, reject) => {
        let envPath = ''

        poetryEnv.stdout.on('data', (data) => {
            envPath += data.toString()
        })

        poetryEnv.on('close', (code) => {
            if (code !== 0) {
                reject(new Error('Failed to get Poetry environment path'))
                return
            }

            const pythonPath = process.platform === 'win32'
                ? path.join(envPath.trim(), 'Scripts', 'python.exe')
                : path.join(envPath.trim(), 'bin', 'python')

            resolve(pythonPath)
        })
    })
}

ipcMain.handle('open-file-dialog', async (event) => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile', 'multiSelections']
    });
    if (result.canceled) {
        return [];
    } else {
        return result.filePaths;
    }
});

ipcMain.handle('open-folder-dialog', async () => {
    const result = await dialog.showOpenDialog({
        properties: ['openDirectory'] // Allows selecting folders only
    });

    return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('change-skin', async (event, input_data_dir, resources_dir, output_data_dir) => {
    try {
        let pythonExecutablePath = "";
        let param;
        let basePath;

        if (app.isPackaged) {
            basePath = process.resourcesPath
            param = [
                '--input-data-dir', input_data_dir,
                '--resources-dir', resources_dir,
                '--output-data-dir', output_data_dir
            ]
            pythonExecutablePath = path.join(basePath, 'python', 'plot_courses');
        } else {
            basePath = path.join(__dirname, '../python/plot_courses.py');
            param = [
                basePath,
                '--input-data-dir', input_data_dir,
                '--resources-dir', resources_dir,
                '--output-data-dir', output_data_dir
            ]
            pythonExecutablePath = await getPythonPath();
        }

        const pythonProcess = spawn(pythonExecutablePath, param);

        return new Promise((resolve, reject) => {
            let result = '';
            let error = '';

            pythonProcess.stdout.on('data', (data) => {
                result += data.toString();
                console.log('Python output:', data.toString());
            });

            pythonProcess.stderr.on('data', (data) => {
                error += data.toString();
                console.error('Python error:', data.toString());
            });

            pythonProcess.on('close', (code) => {
                console.log('Python process exited with code:', code);
                if (code !== 0) {
                    reject(error || 'Process failed');
                } else {
                    // console.log("check", result);

                    try {
                        resolve(result);
                    } catch (e) {
                        reject(`Failed to parse result: ${result}`);
                    }
                }
            });
        });
    } catch (error) {
        console.error('Error processing files:', error);
        throw error;
    }
}); 
