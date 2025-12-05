from app.core.celery_app import celery_app
from app.tasks.tasks import (
    process_image_to_grayscale,
    process_image_to_resize,
    process_image_to_sepia,
    process_image_to_crop,
)
from celery.result import AsyncResult
from typing import Optional, Dict, Any



def dispatch_image_processing_task_grayscale(input_filename: str, output_filename: str):
    """
    Диспетчер для постановки задачи преобразования изображения в оттенки серого.
    """
    task = process_image_to_grayscale.delay(input_filename, output_filename)
    return task


def dispatch_image_processing_task_resize(input_filename: str, output_filename: str,
                                          width: Optional[int] = None, height: Optional[int] = None
                                          )->AsyncResult:
    """
    Диспетчер для постановки задачи изменения размера изображения.
    """
    task = process_image_to_resize.delay(input_filename, output_filename, width, height)
    return task


def dispatch_image_processing_task_sepia(input_filename: str, output_filename: str):
    """
    Диспетчер для постановки задачи применения эффекта сепии.
    """
    task = process_image_to_sepia.delay(input_filename, output_filename)
    return task

def dispatch_image_processing_task_crop(input_filename: str, output_filename: str,
                                        left: int, top: int, right: int, bottom: int)->AsyncResult:
    """
    Диспетчер для постановки задачи обрезки изображения.
    """
    task = process_image_to_crop.delay(input_filename, output_filename, left, top, right, bottom)
    return task


def get_task_result(task_id: str)->Optional[AsyncResult]:
    """
    Создает объект AsyncResult для проверки статуса задачи.
    """
    return celery_app.AsyncResult(task_id)


def get_task_status_data(task: AsyncResult)-> Dict[str, Any]:
    """
    Извлекает информацию о статусе из объекта AsyncResult.
    """
    return {
        "task_id": task.id,
        "status": task.status,
        "ready": task.ready(),
        "successful": task.successful(),
        "result": task.result if task.ready() else None
    }

