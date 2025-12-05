from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from starlette.responses import JSONResponse, FileResponse
from starlette.background import BackgroundTasks

from app.services.file_manager import (
    generate_filenames,
    save_uploaded_file,
    get_processed_file_path,
    cleanup_files
)
from app.services.celery_service import (
    dispatch_image_processing_task_grayscale,
    dispatch_image_processing_task_resize,
    dispatch_image_processing_task_sepia,
    dispatch_image_processing_task_crop,
    get_task_result,
    get_task_status_data
)


router = APIRouter(prefix="",
    tags=["Image Processing"])

def validate_image_file(image: UploadFile):
    """Общая функция для проверки типа файла."""
    if image.content_type not in ["image/jpeg", "image/png"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {image.content_type}. Only JPG and PNG are allowed.")


async def _common_processing_pipeline(image: UploadFile, process_type: str, **kwargs) -> JSONResponse:
    """
    Общий пайплайн для всех ручек обработки изображений.
    Выполняет проверку, сохранение, диспетчеризацию Celery и форматирует ответ.
    """
    validate_image_file(image)
    input_filename, output_filename = generate_filenames(image.filename, process_type)
    await save_uploaded_file(image, input_filename)

    if process_type == "grayscale":
        task = dispatch_image_processing_task_grayscale(input_filename, output_filename)
        specific_data = {}
    elif process_type == "sepia":
        task = dispatch_image_processing_task_sepia(input_filename, output_filename)
        specific_data = {"effect": 'sepia'}
    elif process_type == "resize":
        task = dispatch_image_processing_task_resize(input_filename, output_filename,
                                                     kwargs['width'], kwargs['height'])
        specific_data = {"size": f"{kwargs['width']}x{kwargs['height']}"}
    elif process_type == "crop":
        task = dispatch_image_processing_task_crop(input_filename, output_filename,
                                                   kwargs['left'], kwargs['top'],
                                                   kwargs['right'], kwargs['bottom'])
        specific_data = {"crop_box": (kwargs['left'], kwargs['top'], kwargs['right'], kwargs['bottom'])}
    else:
        raise HTTPException(status_code=500, detail=f"Internal error: Unknown process type '{process_type}'.")

    response_data = {
        'task_id': task.id,
        'status_url': f'/task-status/{task.id}',
        'original_filename': image.filename,
        'task_name': task.name,
    }

    response_data.update(specific_data)
    return JSONResponse(response_data)


@router.post('/sepia')
async def process_to_sepia(image: UploadFile = File(...)):
    """
    Принимает изображение, сохраняет его и ставит задачу Celery на асинхронную
    обработку для применения эффекта сепии.
    """
    return await _common_processing_pipeline(image, "sepia")


@router.post("/grayscale")
async def process_to_grayscale(image: UploadFile = File(...)):
    """
    Принимает изображение, сохраняет его и ставит задачу Celery на асинхронную
    обработку для преобразования в оттенки серого.
    """
    return await _common_processing_pipeline(image, "grayscale")


@router.post("/resize")
async def process_to_resize(image: UploadFile = File(...),
                            width: int = Form(..., ge=16, le=4096),
                            height: int = Form(..., ge=16, le=4096)):
    """
    Принимает изображение и параметры размера, сохраняет файл и ставит задачу
    Celery на изменение размера изображения.
    """
    return await _common_processing_pipeline(
        image,
        "resize",
        width=width,
        height=height
    )

@router.post("/crop")
async def process_to_crop(image: UploadFile = File(...),
                          left: int = Form(..., ge=0), top: int = Form(..., ge=0),
                          right: int = Form(..., ge=0), bottom: int = Form(..., ge=0)):
    """
    Принимает изображение и координаты, сохраняет файл и ставит задачу
    Celery на обрезку изображения.
    """
    validate_image_file(image)
    from fastapi import HTTPException
    if right <= left:
        raise HTTPException(
            status_code=422,
            detail="Crop area is invalid: 'right' coordinate must be greater than 'left'."
        )
    if bottom <= top:
        raise HTTPException(
            status_code=422,
            detail="Crop area is invalid: 'bottom' coordinate must be greater than 'top'."
        )
    return await _common_processing_pipeline(
        image,
        "crop",
        left=left, top=top, right=right, bottom=bottom
    )


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Возвращает текущий статус задачи Celery.
    """
    res = get_task_result(task_id)
    return JSONResponse(content=get_task_status_data(res))


@router.get("/download-result/{task_id}")
async def download_result(task_id: str, background_tasks: BackgroundTasks):
    """
    Проверяет статус задачи и возвращает обработанный файл, если он готов.
    Добавляет задачу по удалению файлов в фон.
    """
    res = get_task_result(task_id)

    if res.ready():
        if res.successful():
            result_data = res.get()
            output_filename = result_data.get('output')
            input_filename = result_data.get('input')

            if not output_filename or not input_filename:
                return JSONResponse(status_code=500,
                                    content={"message": "Task succeeded, but output filename is missing from result."})

            file_path = get_processed_file_path(output_filename)

            if file_path.is_file():
                background_tasks.add_task(cleanup_files, input_filename, output_filename)
                return FileResponse(file_path,
                                    filename=output_filename,
                                    media_type="application/octet-stream")
            else:
                return JSONResponse(status_code=500,
                                    content={"message": f"Processed file not found on disk: {output_filename}"})
        else:
            return JSONResponse(status_code=500,
                                content={"message": "Task failed to process image.", "error": str(res.result)})
    else:
            return JSONResponse(status_code=202, content={"message": "Processing is still in progress. Check status later."})
