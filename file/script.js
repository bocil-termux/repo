import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { 
    getDatabase, 
    ref, 
    onValue, 
    update, 
    get, 
    set, 
    push, 
    remove, 
    off
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

const firebaseConfig = {
    apiKey: "AIzaSyAJi1JO3VOtIsNC7ZM21K4NapNvxM92sYw",
    authDomain: "command-terminal-7557f.firebaseapp.com",
    databaseURL: "https://command-terminal-7557f-default-rtdb.firebaseio.com",
    projectId: "command-terminal-7557f",
    storageBucket: "command-terminal-7557f.firebasestorage.app",
    messagingSenderId: "614995344327",
    appId: "1:614995344327:web:896fe5d1155b78704877e2",
    measurementId: "G-YE035QCESE"
};

const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
    };
    return String(text).replace(/[&<>"'`=\/]/g, function(m) {
        return map[m];
    });
}

class DeviceController {
    constructor() {
        this.currentDevice = null;
        this.deviceRef = null;
        this.isConnected = false;
        this.commandHistory = [];
        this.historyRef = null;
        this.deviceListener = null;
        this.historyListener = null;
        this.rootListener = null;
        this.lastOutput = '';
        this.devices = new Map();
        this.isFirebaseConnected = true;
        this.isDevicesListVisible = false;
        this.editingDeviceId = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupConnectionMonitoring();
        await this.startListeningToDevices();
    }

    setupConnectionMonitoring() {
        const connectedRef = ref(database, ".info/connected");
        onValue(connectedRef, (snap) => {
            this.isFirebaseConnected = snap.val() === true;
            if (this.isFirebaseConnected) {
                document.getElementById('connection-error').classList.remove('show');
                this.showNotification('Koneksi Firebase tersambung', 'success');
                this.updateUIStatus();
            } else {
                document.getElementById('connection-error').classList.add('show');
                document.getElementById('connection-status').textContent = 'Terputus';
                document.getElementById('connection-status').className = 'status-disconnected';
                this.disableControls();
            }
        });
    }

    async startListeningToDevices() {
        try {
            const rootRef = ref(database, '/');
            this.rootListener = onValue(rootRef, (snapshot) => {
                if (!snapshot.exists()) {
                    document.getElementById('devices-list').innerHTML = '<div class="no-devices">Tidak ada perangkat ditemukan</div>';
                    return;
                }
                const data = snapshot.val();
                const devices = Object.keys(data).filter(key => /^\d{8,10}$/.test(key));
                if (devices.length === 0) {
                    document.getElementById('devices-list').innerHTML = '<div class="no-devices">Tidak ada perangkat ditemukan</div>';
                    return;
                }
                devices.forEach(deviceId => {
                    this.devices.set(deviceId, data[deviceId]);
                });
                this.updateDevicesDisplay();
            }, (error) => {
                console.error('Error listening to devices:', error);
                if (this.isFirebaseConnected) {
                    document.getElementById('devices-list').innerHTML = '<div class="error">Gagal memuat perangkat</div>';
                }
            });
        } catch (error) {
            console.error('Error starting device listener:', error);
            if (this.isFirebaseConnected) {
                document.getElementById('devices-list').innerHTML = '<div class="error">Error memuat perangkat</div>';
            }
        }
    }

    toggleDevicesList() {
        this.isDevicesListVisible = !this.isDevicesListVisible;
        const devicesContainer = document.getElementById('devices-list');
        const toggleBtn = document.getElementById('toggle-devices-btn');
        if (this.isDevicesListVisible) {
            devicesContainer.classList.add('show');
            toggleBtn.classList.add('expanded');
            toggleBtn.innerHTML = '<span class="icon">▼</span><span>Sembunyikan Daftar Perangkat</span>';
        } else {
            devicesContainer.classList.remove('show');
            toggleBtn.classList.remove('expanded');
            toggleBtn.innerHTML = '<span class="icon">▼</span><span>Tampilkan Daftar Perangkat</span>';
        }
    }

    updateDevicesDisplay() {
        const devicesList = document.getElementById('devices-list');
        const fragment = document.createDocumentFragment();
        this.devices.forEach((deviceData, deviceId) => {
            const deviceElement = document.createElement('div');
            deviceElement.className = 'device-item';
            const isCurrentDevice = this.currentDevice === deviceId;
            const isEditing = this.editingDeviceId === deviceId;
            const deviceName = deviceData.deviceName || `Perangkat ${deviceId.slice(-4)}`;
            deviceElement.innerHTML = `
                <div class="device-header">
                    <div>
                        ${isEditing ? 
                            `<input type="text" class="device-name-input" value="${escapeHtml(deviceName)}" placeholder="Nama perangkat">` :
                            `<div class="device-name">${escapeHtml(deviceName)}</div>`
                        }
                        <div class="device-id">ID: ${escapeHtml(deviceId)}</div>
                    </div>
                    <div class="device-status ${deviceData.status ? 'online' : 'offline'}">
                        ${deviceData.status ? '🟢 Online' : '🔴 Offline'}
                    </div>
                </div>
                <div class="device-last-command">
                    ${escapeHtml(deviceData.command || 'Tidak ada perintah')}
                </div>
                <div class="device-actions">
                    ${isEditing ? 
                        `<button class="rename-btn save-rename" data-device-id="${escapeHtml(deviceId)}">Simpan</button>
                         <button class="rename-btn cancel-rename" data-device-id="${escapeHtml(deviceId)}">Batal</button>` :
                        `<button class="rename-btn" data-device-id="${escapeHtml(deviceId)}">✏️ Ganti Nama</button>`
                    }
                </div>
                <button class="connect-btn" data-device-id="${escapeHtml(deviceId)}" ${isCurrentDevice ? 'disabled' : ''}>
                    ${isCurrentDevice ? 'Terpilih' : 'Pilih Perangkat'}
                </button>
            `;
            fragment.appendChild(deviceElement);
        });
        devicesList.innerHTML = '';
        devicesList.appendChild(fragment);
        this.setupDevicesEventListeners();
    }

    setupDevicesEventListeners() {
        const devicesList = document.getElementById('devices-list');
        devicesList.addEventListener('click', (e) => {
            const deviceId = e.target.getAttribute('data-device-id');
            if (!deviceId) return;
            if (e.target.classList.contains('connect-btn') && !e.target.disabled) {
                this.connectToDevice(deviceId);
            }
            else if (e.target.classList.contains('rename-btn')) {
                if (e.target.classList.contains('save-rename')) {
                    this.saveDeviceName(deviceId);
                }
                else if (e.target.classList.contains('cancel-rename')) {
                    this.cancelRename();
                }
                else {
                    this.startRenaming(deviceId);
                }
            }
        });
        devicesList.addEventListener('keypress', (e) => {
            if (e.target.classList.contains('device-name-input') && e.key === 'Enter') {
                const deviceId = this.editingDeviceId;
                if (deviceId) {
                    this.saveDeviceName(deviceId);
                }
            }
        });
    }

    startRenaming(deviceId) {
        this.editingDeviceId = deviceId;
        this.updateDevicesDisplay();
    }

    cancelRename() {
        this.editingDeviceId = null;
        this.updateDevicesDisplay();
    }

    async saveDeviceName(deviceId) {
        const input = document.querySelector(`[data-device-id="${deviceId}"] .device-name-input`);
        if (!input) return;
        const newName = input.value.trim();
        if (!newName) {
            this.showNotification('Nama perangkat tidak boleh kosong', 'error');
            return;
        }
        try {
            const deviceRef = ref(database, `${deviceId}/deviceName`);
            await set(deviceRef, newName);
            this.editingDeviceId = null;
            this.showNotification('Nama perangkat berhasil disimpan', 'success');
            this.updateDevicesDisplay();
        } catch (error) {
            console.error('Error saving device name:', error);
            this.showNotification('Error menyimpan nama perangkat', 'error');
        }
    }

    async connectToDevice(deviceId) {
        if (!this.isFirebaseConnected) {
            this.showNotification('Tidak terhubung ke Firebase', 'error');
            return;
        }
        try {
            document.getElementById('connection-status').textContent = 'Menghubungkan...';
            document.getElementById('connection-status').className = 'status-connecting';
            this.cleanupDeviceListeners();
            this.currentDevice = deviceId;
            this.deviceRef = ref(database, deviceId);
            this.historyRef = ref(database, `${deviceId}/history`);
            const deviceData = this.devices.get(deviceId);
            const deviceName = deviceData?.deviceName || `Perangkat ${deviceId.slice(-4)}`;
            document.getElementById('current-device').textContent = `${deviceName} (${deviceId})`;
            this.deviceListener = onValue(this.deviceRef, (snapshot) => {
                if (snapshot.exists()) {
                    const data = snapshot.val();
                    this.updateOutput(data);
                    document.getElementById('connection-status').textContent = 'Terhubung';
                    document.getElementById('connection-status').className = 'status-connected';
                    this.enableControls();
                }
            }, (error) => {
                console.error('Error listening to device:', error);
                document.getElementById('connection-status').textContent = 'Error';
                document.getElementById('connection-status').className = 'status-disconnected';
                this.disableControls();
            });
            this.setupHistoryListener();
            this.updateDevicesDisplay();
        } catch (error) {
            console.error('Error connecting to device:', error);
            this.showNotification('Error menghubungkan ke perangkat', 'error');
            document.getElementById('connection-status').textContent = 'Error';
            document.getElementById('connection-status').className = 'status-disconnected';
            this.disableControls();
        }
    }

    setupHistoryListener() {
        if (!this.historyRef || !this.isFirebaseConnected) return;
        if (this.historyListener) {
            off(this.historyRef, this.historyListener);
        }
        this.historyListener = onValue(this.historyRef, (snapshot) => {
            this.updateHistoryDisplay(snapshot);
        }, (error) => {
            console.error('Error listening to history:', error);
            document.getElementById('history-list').innerHTML = '<div class="error">Error memuat riwayat</div>';
        });
    }

    updateHistoryDisplay(snapshot) {
        if (!snapshot.exists()) {
            document.getElementById('history-list').innerHTML = '<div class="no-devices">Tidak ada riwayat perintah</div>';
            return;
        }
        const history = snapshot.val();
        const historyArray = Object.entries(history).map(([key, value]) => ({
            id: key,
            ...value
        })).sort((a, b) => 
            new Date(b.timestamp) - new Date(a.timestamp)
        );
        const fragment = document.createDocumentFragment();
        historyArray.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <span class="history-command">${escapeHtml(item.command)}</span>
                <span class="history-time">${new Date(item.timestamp).toLocaleTimeString()}</span>
            `;
            historyItem.addEventListener('click', () => {
                if (this.isFirebaseConnected) {
                    document.getElementById('command-input').value = item.command;
                    this.sendCommand();
                }
            });
            fragment.appendChild(historyItem);
        });
        document.getElementById('history-list').innerHTML = '';
        document.getElementById('history-list').appendChild(fragment);
    }

    updateOutput(data) {
        const outputElement = document.getElementById('output');
        if (data.output && data.output.trim() !== '' && data.output !== this.lastOutput) {
            this.lastOutput = data.output;
            const formattedOutput = this.formatOutput(data.output);
            outputElement.innerHTML = formattedOutput;
            outputElement.scrollTop = outputElement.scrollHeight;
            if (data.status === true && data.command) {
                this.addToHistory(data.command);
            }
        }
    }

    formatOutput(output) {
        const escapedOutput = escapeHtml(output);
        const lines = escapedOutput.split('\n');
        let formattedLines = '';
        const maxLines = 1000;
        const linesToProcess = lines.length > maxLines ? 
            lines.slice(0, maxLines).concat(['... (output dipotong)']) : lines;
        linesToProcess.forEach(line => {
            let lineClass = '';
            if (line.startsWith('drwx') || line.includes('/')) {
                lineClass = 'directory';
            } else if (line.startsWith('-rwx')) {
                lineClass = 'executable';
            } else if (line.toLowerCase().includes('error') || line.startsWith('bash:')) {
                lineClass = 'error';
            } else if (line.includes(':') && !line.includes('http')) {
                lineClass = 'info';
            }
            formattedLines += `<div class="output-line ${lineClass}">${line}</div>`;
        });
        return formattedLines;
    }

    async sendCommand() {
        if (!this.currentDevice || !this.isFirebaseConnected) {
            this.showNotification('Tidak terhubung ke perangkat atau Firebase', 'error');
            return;
        }
        const commandInput = document.getElementById('command-input');
        const command = commandInput.value.trim();
        if (!command) {
            this.showNotification('Masukkan perintah!', 'error');
            return;
        }
        try {
            document.getElementById('output').textContent = 'Mengirim perintah...';
            document.getElementById('send-btn').disabled = true;
            await update(this.deviceRef, {
                command: command,
                status: false,
                output: '',
                timestamp: Date.now()
            });
            commandInput.value = '';
            this.showNotification(`Perintah "${escapeHtml(command)}" dikirim`, 'info');
            setTimeout(() => {
                if (this.isFirebaseConnected) {
                    document.getElementById('send-btn').disabled = false;
                }
            }, 1000);
        } catch (error) {
            console.error('Error sending command:', error);
            this.showNotification('Error mengirim perintah', 'error');
            if (this.isFirebaseConnected) {
                document.getElementById('send-btn').disabled = false;
            }
        }
    }

    async addToHistory(command) {
        if (!this.currentDevice || !this.historyRef || !this.isFirebaseConnected) return;
        try {
            const historyItem = {
                command: command,
                timestamp: new Date().toISOString()
            };
            const newHistoryRef = push(this.historyRef);
            await set(newHistoryRef, historyItem);
            await this.limitHistory();
        } catch (error) {
            console.error('Error adding to history:', error);
        }
    }

    async limitHistory() {
        if (!this.historyRef || !this.isFirebaseConnected) return;
        try {
            const snapshot = await get(this.historyRef);
            if (snapshot.exists()) {
                const history = snapshot.val();
                const historyKeys = Object.keys(history);
                if (historyKeys.length > 10) {
                    const historyArray = Object.entries(history).map(([key, value]) => ({
                        id: key,
                        ...value
                    })).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                    while (historyArray.length > 10) {
                        const oldestItem = historyArray.shift();
                        const oldestRef = ref(database, `${this.currentDevice}/history/${oldestItem.id}`);
                        await remove(oldestRef);
                    }
                }
            }
        } catch (error) {
            console.error('Error limiting history:', error);
        }
    }

    enableControls() {
        document.getElementById('command-input').disabled = false;
        document.getElementById('send-btn').disabled = false;
        document.getElementById('clear-btn').disabled = false;
        document.querySelectorAll('.quick-command').forEach(btn => {
            btn.disabled = false;
        });
    }

    disableControls() {
        document.getElementById('command-input').disabled = true;
        document.getElementById('send-btn').disabled = true;
        document.getElementById('clear-btn').disabled = true;
        document.querySelectorAll('.quick-command').forEach(btn => {
            btn.disabled = true;
        });
    }

    updateUIStatus() {
        if (this.currentDevice && this.isFirebaseConnected) {
            this.enableControls();
        } else {
            this.disableControls();
        }
    }

    showNotification(message, type) {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type} show`;
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    setupEventListeners() {
        document.getElementById('toggle-devices-btn').addEventListener('click', () => {
            this.toggleDevicesList();
        });
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendCommand();
        });
        document.getElementById('command-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && this.isFirebaseConnected) {
                this.sendCommand();
            }
        });
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('command-input').focus();
            }
        });
        document.getElementById('clear-btn').addEventListener('click', () => {
            document.getElementById('output').innerHTML = '';
            this.lastOutput = '';
        });
        document.querySelectorAll('.quick-command').forEach(button => {
            button.addEventListener('click', () => {
                if (this.isFirebaseConnected) {
                    const command = button.getAttribute('data-command');
                    document.getElementById('command-input').value = command;
                    this.sendCommand();
                }
            });
        });
    }

    cleanupDeviceListeners() {
        if (this.deviceListener && this.deviceRef) {
            off(this.deviceRef, this.deviceListener);
        }
        if (this.historyListener && this.historyRef) {
            off(this.historyRef, this.historyListener);
        }
    }

    cleanup() {
        this.cleanupDeviceListeners();
        if (this.rootListener) {
            const rootRef = ref(database, '/');
            off(rootRef, this.rootListener);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.deviceController = new DeviceController();
});

window.addEventListener('beforeunload', () => {
    if (window.deviceController) {
        window.deviceController.cleanup();
    }
});
