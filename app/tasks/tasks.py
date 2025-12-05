from ..core.celery_app import celery_app
from app.services.image_processor import apply_grayscale,resize_image,sepia_image,crop_image


@celery_app.task(acks_late=True)
def process_image_to_sepia(input_filename, output_filename):
    """
    Асинхронная задача Celery для применения эффекта сепии.
    """
    success = sepia_image(input_filename, output_filename)

    if not success:
        # Если функция image_processor вернула False, принудительно вызываем FAILURE
        raise Exception(f"Failed to apply sepia to image file: {input_filename}")

    return {
        "status": "COMPLETED",
        "input": input_filename,
        "output": output_filename,
        "effect": "sepia"
    }

@celery_app.task(acks_late=True)
def process_image_to_grayscale(input_filename: str, output_filename: str) ->dict:
    """
    Асинхронная задача Celery для применения фильтра градаций серого.
    """

    success = apply_grayscale(input_filename, output_filename)

    return {"status": "COMPLETED" if success else "FAILED",
            "input": input_filename,
            "output": output_filename}

@celery_app.task(acks_late=True)
def process_image_to_resize(input_filename: str, output_filename: str, width: int, height: int) ->dict:
    """
    Асинхронная задача Celery для изменения размера изображения.
    """

    size = (width, height)
    success = resize_image(input_filename, output_filename, size)
    if not success:
        raise Exception(f"Failed to process image file: {input_filename}")

    return {"status": "COMPLETED" if success else "FAILED",
            "input": input_filename,
            "output": output_filename,
            "size": f"{width}x{height}"}

@celery_app.task(acks_late=True)
def process_image_to_crop(input_filename: str, output_filename: str,
                          left: int, top: int, right: int, bottom: int) ->dict:
    """
    Асинхронная задача Celery для обрезки изображения.
    """

    box = (left, top, right, bottom)
    success = crop_image(input_filename, output_filename, box)
    if not success:
        raise Exception(f"Failed to process image file: {input_filename}")

    return {
        "status": "COMPLETED",
        "input": input_filename,
        "output": output_filename,
        "crop_box": box
    }