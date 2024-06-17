const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;
let ollamaProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: true
        }
    });

    mainWindow.loadFile('pages/index.html');

    mainWindow.on('closed', function () {
        mainWindow = null;
    });

    mainWindow.on('close', function () {
        if (pythonProcess) {
            pythonProcess.kill();
        }
        if (ollamaProcess) {
            ollamaProcess.kill();
        }
    });
}

app.on('ready', () => {
    // Start the Python backend server
    pythonProcess = spawn('python3', ['-u', path.join(__dirname, 'backend', 'backend.py')]);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
    });

    // Start the Ollama server
    ollamaProcess = spawn('python3', ['-u', path.join(__dirname, 'backend', 'server_control.py')]);

    ollamaProcess.stdout.on('data', (data) => {
        console.log(`Ollama stdout: ${data}`);
    });

    ollamaProcess.stderr.on('data', (data) => {
        console.error(`Ollama stderr: ${data}`);
    });

    ollamaProcess.on('close', (code) => {
        console.log(`Ollama process exited with code ${code}`);
    });

    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('before-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
    if (ollamaProcess) {
        ollamaProcess.kill();
    }
});
