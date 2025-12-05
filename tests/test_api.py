import pytest
from unittest.mock import MagicMock


TEST_IMAGE_PATH = "./tests/test_image.jpg"

@pytest.mark.asyncio
async def test_crop_success(sync_client, mock_celery_tasks: MagicMock):
    """Проверяет, что /crop успешно вызывает Celery-диспетчер с правильными аргументами."""
    mock_celery_tasks.reset_mock()

    with open(TEST_IMAGE_PATH, "rb") as image_file:
        files = {'image': ("test_image.jpg", image_file, 'image/jpeg')}
        data = {
            "left": 10,
            "top": 10,
            "right": 100,
            "bottom": 100
        }
        response = sync_client.post("/crop", data=data, files=files)

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data

    mock_celery_tasks.assert_called_once()

    args, kwargs = mock_celery_tasks.call_args

    assert len(args) == 6
    assert args[2] == 10
    assert args[3] == 10
    assert args[4] == 100
    assert args[5] == 100


@pytest.mark.asyncio
async def test_crop_validation_right_less_than_left(sync_client, mock_celery_tasks: MagicMock):
    """Проверяет, что роут возвращает 422, если right <= left."""

    # Сбрасываем мок и убеждаемся, что Celery не будет вызван
    mock_celery_tasks.reset_mock()

    with open(TEST_IMAGE_PATH, "rb") as image_file:
        files = {"image": ("test_image.jpg", image_file, "image/jpeg")}
        # right=10, left=50 -> ошибка
        data = {
            "left": 50,
            "top": 10,
            "right": 10,
            "bottom": 100
        }

        response = sync_client.post("/crop", files=files, data=data)

    # 1. Проверка результата API
    assert response.status_code == 422
    assert "Crop area is invalid" in response.json()["detail"]

    # 2. Проверка, что Celery не был вызван!
    mock_celery_tasks.assert_not_called()