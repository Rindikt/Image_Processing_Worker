import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app

@pytest.fixture(scope="session")
def sync_client():
    """Создает СИНХРОННЫЙ клиент TestClient для тестирования FastAPI."""
    with TestClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_celery_tasks():
    """Фикстура, которая мокирует все Celery-задачи."""
    mock_async_result = MagicMock()
    mock_async_result.id = 'fake_task_id_123'
    mock_async_result.name = 'task.image_processing.crop'

    mock_delay = MagicMock(return_value=mock_async_result)

    task_paths = [
        "app.routers.image_processing.dispatch_image_processing_task_grayscale",
        "app.routers.image_processing.dispatch_image_processing_task_sepia",
        "app.routers.image_processing.dispatch_image_processing_task_resize",
        "app.routers.image_processing.dispatch_image_processing_task_crop",
    ]

    mocks = []

    for path in task_paths:
        patcher = patch(path, new=MagicMock(return_value=mock_async_result))
        mocks.append(patcher.start())
    yield mocks[3]

    for patcher in mocks:
        patcher.stop()