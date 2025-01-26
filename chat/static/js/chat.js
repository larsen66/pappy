// Функции для работы с файлами
const fileHandler = {
    // Максимальный размер файла (10MB)
    maxFileSize: 10 * 1024 * 1024,
    
    // Допустимые типы файлов
    allowedTypes: [
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ],
    
    // Проверка файла
    validateFile(file) {
        if (file.size > this.maxFileSize) {
            throw new Error('Файл слишком большой. Максимальный размер: 10MB');
        }
        
        if (!this.allowedTypes.includes(file.type)) {
            throw new Error('Неподдерживаемый тип файла');
        }
        
        return true;
    },
    
    // Создание превью файла
    createPreview(file) {
        const preview = document.createElement('div');
        preview.className = 'file-preview-item';
        
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            preview.appendChild(img);
        } else {
            const icon = document.createElement('i');
            icon.className = 'fas fa-file';
            const name = document.createElement('span');
            name.textContent = file.name;
            preview.appendChild(icon);
            preview.appendChild(name);
        }
        
        return preview;
    }
};

// Функции для работы с геолокацией
const locationHandler = {
    // Получение текущей геолокации
    getCurrentLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Геолокация не поддерживается вашим браузером'));
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                position => resolve(position),
                error => reject(error)
            );
        });
    },
    
    // Создание превью карты
    createMapPreview(latitude, longitude) {
        // Здесь можно использовать любой сервис карт (Google Maps, OpenStreetMap и т.д.)
        const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${longitude-0.01},${latitude-0.01},${longitude+0.01},${latitude+0.01}&marker=${latitude},${longitude}`;
        
        const iframe = document.createElement('iframe');
        iframe.src = mapUrl;
        iframe.width = '100%';
        iframe.height = '200';
        iframe.frameBorder = '0';
        
        return iframe;
    }
};

// Функции для работы с аудио
const audioHandler = {
    // Инициализация записи
    async initRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            const audioChunks = [];
            
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });
            
            return { mediaRecorder, audioChunks, stream };
        } catch (error) {
            throw new Error('Не удалось получить доступ к микрофону');
        }
    },
    
    // Создание аудио элемента для предпросмотра
    createAudioPreview(blob) {
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.src = URL.createObjectURL(blob);
        return audio;
    }
};

// Основной класс для работы с чатом
class ChatHandler {
    constructor(dialogId) {
        this.dialogId = dialogId;
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        this.messagesContainer = document.getElementById('messages-container');
        this.filePreview = document.getElementById('file-preview');
        this.typingIndicator = document.getElementById('typing-indicator');
        
        this.attachEventListeners();
        this.initWebSocket();
    }
    
    // Инициализация WebSocket соединения
    initWebSocket() {
        const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
        this.socket = new WebSocket(
            `${wsScheme}://${window.location.host}/ws/chat/${this.dialogId}/`
        );
        
        this.socket.onmessage = this.handleWebSocketMessage.bind(this);
        this.socket.onclose = () => {
            console.log('WebSocket соединение закрыто');
            // Можно добавить логику переподключения
        };
    }
    
    // Прикрепление обработчиков событий
    attachEventListeners() {
        // Отправка сообщения
        this.messageForm.addEventListener('submit', this.handleMessageSubmit.bind(this));
        
        // Отправка файлов
        document.getElementById('attach-file').addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.addEventListener('change', this.handleFileSelect.bind(this));
            input.click();
        });
        
        // Отправка геолокации
        document.getElementById('send-location').addEventListener('click', 
            this.handleLocationSend.bind(this));
        
        // Запись голосового сообщения
        const recordButton = document.getElementById('record-voice');
        recordButton.addEventListener('mousedown', this.startVoiceRecording.bind(this));
        recordButton.addEventListener('mouseup', this.stopVoiceRecording.bind(this));
        
        // Индикатор печати
        let typingTimeout;
        this.messageInput.addEventListener('input', () => {
            clearTimeout(typingTimeout);
            
            this.socket.send(JSON.stringify({
                type: 'typing',
                typing: true
            }));
            
            typingTimeout = setTimeout(() => {
                this.socket.send(JSON.stringify({
                    type: 'typing',
                    typing: false
                }));
            }, 3000);
        });
    }
    
    // Обработка WebSocket сообщений
    handleWebSocketMessage(event) {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'new_message':
                this.addMessage(data.message);
                break;
            case 'typing':
                this.updateTypingStatus(data.user);
                break;
            case 'user_status':
                this.updateUserStatus(data.user);
                break;
            case 'message_read':
                this.updateMessageStatus(data.message_id);
                break;
        }
    }
    
    // Отправка сообщения
    async handleMessageSubmit(event) {
        event.preventDefault();
        
        const content = this.messageInput.value.trim();
        if (!content) return;
        
        const formData = new FormData();
        formData.append('content', content);
        
        try {
            const response = await fetch(`/chat/${this.dialogId}/send/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            
            if (!response.ok) throw new Error('Ошибка отправки сообщения');
            
            this.messageInput.value = '';
            this.messageInput.focus();
            
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось отправить сообщение');
        }
    }
    
    // Обработка выбора файлов
    async handleFileSelect(event) {
        const files = Array.from(event.target.files);
        
        try {
            for (const file of files) {
                fileHandler.validateFile(file);
                
                const preview = fileHandler.createPreview(file);
                this.filePreview.querySelector('.preview-content').appendChild(preview);
            }
            
            this.filePreview.style.display = 'block';
            
        } catch (error) {
            alert(error.message);
        }
    }
    
    // Отправка геолокации
    async handleLocationSend() {
        try {
            const position = await locationHandler.getCurrentLocation();
            
            const formData = new FormData();
            formData.append('latitude', position.coords.latitude);
            formData.append('longitude', position.coords.longitude);
            
            const response = await fetch(`/chat/${this.dialogId}/send-location/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            
            if (!response.ok) throw new Error('Ошибка отправки геолокации');
            
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось отправить геолокацию');
        }
    }
    
    // Запись голосового сообщения
    async startVoiceRecording() {
        try {
            const recording = await audioHandler.initRecording();
            this.currentRecording = recording;
            recording.mediaRecorder.start();
        } catch (error) {
            alert(error.message);
        }
    }
    
    async stopVoiceRecording() {
        if (!this.currentRecording) return;
        
        const { mediaRecorder, audioChunks, stream } = this.currentRecording;
        
        mediaRecorder.stop();
        stream.getTracks().forEach(track => track.stop());
        
        mediaRecorder.addEventListener('stop', async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
            
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('duration', Math.ceil(audioBlob.size / 16000)); // Примерная длительность
            
            try {
                const response = await fetch(`/chat/${this.dialogId}/send-voice/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });
                
                if (!response.ok) throw new Error('Ошибка отправки аудио');
                
            } catch (error) {
                console.error('Ошибка:', error);
                alert('Не удалось отправить голосовое сообщение');
            }
        });
    }
    
    // Добавление сообщения в чат
    addMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender_id === currentUser ? 'outgoing' : 'incoming'}`;
        messageElement.dataset.messageId = message.id;
        
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${message.content}</p>
            </div>
            <div class="message-meta">
                <span class="time">${new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                ${message.sender_id === currentUser ? '<span class="status"><i class="fas fa-check"></i></span>' : ''}
            </div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    // Обновление статуса печати
    updateTypingStatus(user) {
        this.typingIndicator.style.display = user.typing ? 'block' : 'none';
    }
    
    // Обновление статуса пользователя
    updateUserStatus(user) {
        const statusElement = document.getElementById('online-status');
        statusElement.textContent = user.is_online ? 'В сети' : 'Не в сети';
        statusElement.className = user.is_online ? 'status-online' : 'status-offline';
    }
    
    // Обновление статуса сообщения
    updateMessageStatus(messageId) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            const statusIcon = messageElement.querySelector('.status i');
            if (statusIcon) {
                statusIcon.className = 'fas fa-check-double';
            }
        }
    }
    
    // Прокрутка к последнему сообщению
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
}

// Инициализация чата при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const dialogId = document.querySelector('[data-dialog-id]')?.dataset.dialogId;
    if (dialogId) {
        new ChatHandler(dialogId);
    }
}); 