// frontend/html/app.js

// URL нашего API, работающего на порту 8001
const API_URL = "http://localhost:8001";
const STATUS_DIV = document.getElementById('status');
const RESULT_DIV = document.getElementById('result');
const INPUT_PREVIEW = document.getElementById('inputPreview');
const OUTPUT_PREVIEW = document.getElementById('outputPreview');

/**
 * Инициализация: Отображение превью выбранного файла.
 */
document.getElementById('fileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        // Создаем локальный URL для отображения файла в браузере
        INPUT_PREVIEW.src = URL.createObjectURL(file);

        // Сбрасываем предыдущий результат
        OUTPUT_PREVIEW.src = '';
        STATUS_DIV.innerHTML = '';
        RESULT_DIV.innerHTML = '';
    }
});


/**
 * 1. Отправляет файл и параметры на бэкенд для начала обработки.
 */
async function uploadFile(endpoint) {
    STATUS_DIV.innerHTML = '';
    RESULT_DIV.innerHTML = '';
    OUTPUT_PREVIEW.src = ''; // Сброс превью результата перед новой задачей

    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert("Пожалуйста, выберите файл!");
        return;
    }

    STATUS_DIV.innerHTML = `<p>Загрузка файла и постановка задачи в Celery...</p>`;

    const formData = new FormData();
    formData.append("image", file);

    // --- ДИНАМИЧЕСКОЕ ДОБАВЛЕНИЕ ПАРАМЕТРОВ ---
    if (endpoint === 'resize') {
        const width = document.getElementById('resizeWidth').value;
        const height = document.getElementById('resizeHeight').value;
        formData.append("width", width);
        formData.append("height", height);
    } else if (endpoint === 'crop') {
        // Параметры для обрезки (Crop)
        const left = document.getElementById('cropLeft').value;
        const top = document.getElementById('cropTop').value;
        const right = document.getElementById('cropRight').value;
        const bottom = document.getElementById('cropBottom').value;

        formData.append("left", left);
        formData.append("top", top);
        formData.append("right", right);
        formData.append("bottom", bottom);
    }
    // ------------------------------------------

    try {
        const response = await fetch(`${API_URL}/${endpoint}`, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (response.ok) {
            STATUS_DIV.innerHTML = `<p>✅ Задача "${endpoint}" поставлена в очередь. ID: ${data.task_id}</p>`;
            // Начинаем опрос статуса каждую секунду
            pollStatus(data.task_id, 1000);
        } else {
            STATUS_DIV.innerHTML = `<p style="color: red;">❌ Ошибка API: ${data.detail || 'Неизвестная ошибка'}</p>`;
        }
    } catch (error) {
        STATUS_DIV.innerHTML = `<p style="color: red;">❌ Ошибка сети: ${error.message}</p>`;
    }
}

/**
 * 2. Рекурсивно опрашивает статус задачи Celery.
 */
function pollStatus(taskId, interval) {
    const statusUrl = `${API_URL}/task-status/${taskId}`;

    fetch(statusUrl)
        .then(res => res.json())
        .then(data => {
            const status = data.status;

            STATUS_DIV.innerHTML = `<p>🔄 Статус задачи ${taskId}: <b>${status}</b></p>`;

            if (status === 'SUCCESS') {
                const downloadLink = `${API_URL}/download-result/${taskId}`;

                RESULT_DIV.innerHTML = `
                    <p>✨ Обработка завершена!</p>
                    <a href="${downloadLink}" download>
                        Скачать результат
                    </a>
                `;

                // Отображаем готовый результат, используя URL для скачивания
                OUTPUT_PREVIEW.src = downloadLink;

            } else if (status === 'FAILURE' || status === 'REVOKED') {
                // Обработка ошибок
                const errorDetail = data.result && data.result.error ? data.result.error : 'См. логи Flower.';
                STATUS_DIV.innerHTML = `<p style="color: red;">🔥 Задача завершилась с ошибкой: ${errorDetail}</p>`;
            } else {
                // Если статус не финальный (PENDING, STARTED), продолжаем опрос
                setTimeout(() => pollStatus(taskId, interval), interval);
            }
        })
        .catch(error => {
            STATUS_DIV.innerHTML = `<p style="color: red;">❌ Ошибка опроса статуса: ${error.message}</p>`;
        });
}

// Делаем функцию доступной в глобальной области видимости для onclick
window.uploadFile = uploadFile;