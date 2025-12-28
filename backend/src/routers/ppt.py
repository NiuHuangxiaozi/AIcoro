from fastapi import APIRouter, HTTPException, status, Depends
import hashlib
import logging
import traceback
import os
import uuid
from datetime import datetime
from os.path import join
import json
import asyncio
from copy import deepcopy
from fastapi import (
    File,
    Form,
    UploadFile,
)
from fastapi.responses import FileResponse


# current program lib
from ..models import (
    PPTResponse,
    User
)
from ..auth import get_current_user
from ..config import settings

router = APIRouter(prefix="/pptgen", tags=["PPT生成"])
logger = logging.getLogger(__name__)




# 下面是报告进度的函数
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
active_connections: dict[str, WebSocket] = {}
progress_store: dict[str, dict] = {}
STAGES = [
    "PPT Parsing",
    "PDF Parsing",
    "PPT Analysis",
    "PPT Generation",
    "Success!",
]
class ProgressManager:
    def __init__(self, task_id: str, stages: list[str], debug: bool = True):
        self.task_id = task_id
        self.stages = stages
        self.debug = debug
        self.task_id = task_id
        self.failed = False
        self.current_stage = 0
        self.total_stages = len(stages)

    async def report_progress(self):
        assert self.task_id in active_connections, (
            "WebSocket connection is already closed"
        )
        self.current_stage += 1
        progress = int((self.current_stage / self.total_stages) * 100)
        await send_progress(
            active_connections[self.task_id],
            f"Stage: {self.stages[self.current_stage - 1]}",
            progress,
        )

    async def fail_stage(self, error_message: str):
        await send_progress(
            active_connections[self.task_id],
            f"{self.stages[self.current_stage]} Error: {error_message}",
            100,
        )
        self.failed = True
        active_connections.pop(self.task_id, None)
        if self.debug:
            logger.error(
                f"{self.task_id}: {self.stages[self.current_stage]} Error: {error_message}"
            )
            
async def send_progress(websocket: WebSocket | None, status: str, progress: int):
    if websocket is None:
        logger.info(f"websocket is None, status: {status}, progress: {progress}")
        return
    await websocket.send_json({"progress": progress, "status": status})


@router.websocket("/wsapi/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    logger.info(f"websocket connected: {task_id}")
    if task_id in progress_store:
        await websocket.accept()
    else:
        raise HTTPException(status_code=404, detail="Task not found")
    active_connections[task_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("websocket disconnected: %s", task_id)
        active_connections.pop(task_id, None)

# =================================================================================================================


@router.post("/generate", response_model=PPTResponse)
async def generate_ppt(
    pptxFile: UploadFile = File(None),
    pdfFile: UploadFile = File(None),
    topic: str = Form(None),
    numberOfPages: int = Form(...),
    current_user: User = Depends(get_current_user)
):    
    """生成PPT"""
    task_id = datetime.now().strftime("20%y-%m-%d") + "-" + str(uuid.uuid4())
    user_hash_code = hashlib.md5(current_user.id.encode()).hexdigest()
    logger.info(f"task created: {task_id}, user_hash_code: {user_hash_code}")

    # 为每一个用户生成一个任务目录,用户id的哈希值作为目录名,还有任务创建的时间
    current_user_dir=join(settings.ppt_generation_dir, user_hash_code, task_id)
    os.makedirs(current_user_dir, exist_ok=True)
    
    task = {
        "numberOfPages": numberOfPages,
        "pptx": "default_template",
    }

    # 检查生成ppt需要的配置
    if pptxFile is not None:
        pptx_blob = await pptxFile.read()
        pptx_md5 = hashlib.md5(pptx_blob).hexdigest()
        task["pptx"] = pptx_md5
        pptx_dir = join(current_user_dir, "pptx", pptx_md5)
        if not os.path.exists(pptx_dir):
            os.makedirs(pptx_dir, exist_ok=True)
            with open(join(pptx_dir, "source.pptx"), "wb") as f:
                f.write(pptx_blob)

    # 检查生成pdf需要的配置
    if pdfFile is not None:
        pdf_blob = await pdfFile.read()
        pdf_md5 = hashlib.md5(pdf_blob).hexdigest()
        task["pdf"] = pdf_md5
        pdf_dir = join(current_user_dir, "pdf", pdf_md5)
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir, exist_ok=True)
            with open(join(pdf_dir, "source.pdf"), "wb") as f:
                f.write(pdf_blob)
    
    if topic is not None:
        task["topic"] = topic

    # task里面保存了这次生成ppt有关信息,保存到对应用户生成目录
    with open(join(current_user_dir, "task.json"), "w") as f:
        json.dump(task, f, ensure_ascii=False, indent=4)
    
    progress_store[task_id] = task
    
    progress = ProgressManager(task_id, STAGES)
     
    # 调度生成ppt任务
    asyncio.create_task(generate_ppt_task(user_hash_code, task_id, progress))

    
    return {"task_id": task_id}




from pptagent.presentation import Presentation
from pptagent.utils import Config, ppt_to_images_async
from pptagent.multimodal import ImageLabler
from pptagent.model_utils import ModelManager, parse_pdf
from pptagent.document import Document
from pptagent.induct import SlideInducter
from pptagent.pptgen import PPTAgent
async def generate_ppt_task(user_hash_code: str, task_id: str, progress: ProgressManager):
    
    await asyncio.sleep(1)
    task_dir=join(settings.ppt_generation_dir, user_hash_code, task_id)
    task = json.load(open(join(task_dir, "task.json"), encoding="utf-8"))


    pptx_config = Config(join(task_dir, "pptx", task["pptx"]))
    pdf_config = Config(join(task_dir, "pdf", task["pdf"]))
    generation_config = Config(join(task_dir, "generation"))
    models = ModelManager()
    
    await send_progress(
        active_connections[task_id], "task initialized successfully", 10
    )
    
    try:
        # 生成ppt
        # ppt 模板的解析 parsing
        presentation = Presentation.from_file(
            join(pptx_config.RUN_DIR, "source.pptx"),
            pptx_config
        )

        if not os.path.exists(join(pptx_config.RUN_DIR, "slide_images")) or len(
            os.listdir(join(pptx_config.RUN_DIR, "slide_images"))
        ) != len(presentation):
            await ppt_to_images_async(
                join(pptx_config.RUN_DIR, "source.pptx"), join(pptx_config.RUN_DIR, "slide_images")
            )
            assert len(os.listdir(join(pptx_config.RUN_DIR, "slide_images"))) == len(presentation) + len(
                presentation.error_history
            ), "Number of parsed slides and images do not match"

            for err_idx, _ in presentation.error_history:
                os.remove(join(join(pptx_config.RUN_DIR, "slide_images"), f"slide_{err_idx:04d}.jpg"))
            for i, slide in enumerate(presentation.slides, 1):
                slide.slide_idx = i
                os.rename(
                    join(join(pptx_config.RUN_DIR, "slide_images"), f"slide_{slide.real_idx:04d}.jpg"),
                    join(join(pptx_config.RUN_DIR, "slide_images"), f"slide_{slide.slide_idx:04d}.jpg"),
                )


        # 图片的标签化 labeling（还是类属于pptx）
        labler = ImageLabler(presentation, pptx_config)
        if os.path.exists(join(pptx_config.RUN_DIR, "image_stats.json")):
            image_stats = json.load(
                open(join(pptx_config.RUN_DIR, "image_stats.json"), encoding="utf-8")
            )
            labler.apply_stats(image_stats)
        else:
            await labler.caption_images_async(models.vision_model)
            json.dump(
                labler.image_stats,
                open(
                    join(pptx_config.RUN_DIR, "image_stats.json"),
                    "w",
                    encoding="utf-8",
                ),
                ensure_ascii=False,
                indent=4,
            )
        await progress.report_progress()
        
        # 解析pdf
        # pdf parsing
        if not os.path.exists(join(pdf_config.RUN_DIR, "source.md")):
            _ = await parse_pdf(
                join(pdf_config.RUN_DIR, "source.pdf"),
                pdf_config.RUN_DIR,
            )
            print("解析pdf......完成,已经保存到本地")
            text_content = open(
                join(pdf_config.RUN_DIR, "source.md"), encoding="utf-8"
            ).read()
        else:
            text_content = open(
                join(pdf_config.RUN_DIR, "source.md"), encoding="utf-8"
            ).read()
        
        await progress.report_progress()

        # 上面我们将pdf转化为了md，下面我们在整理总结一下md的信息，保存为refined_doc.json文件
         # document refine
        if not os.path.exists(join(pdf_config.RUN_DIR, "refined_doc.json")):
            source_doc = await Document.from_markdown(
                text_content,
                models.language_model,
                models.vision_model,
                pdf_config.RUN_DIR,
            )
            json.dump(
                source_doc.model_dump(),
                open(join(pdf_config.RUN_DIR, "refined_doc.json"), "w"),
                ensure_ascii=False,
                indent=4,
            )
        else:
            source_doc = json.load(
                open(join(pdf_config.RUN_DIR, "refined_doc.json"), encoding="utf-8")
            )
            source_doc = Document.model_validate(source_doc)
            
        await progress.report_progress()
        
            
        # Slide Induction
        if not os.path.exists(join(pptx_config.RUN_DIR, "slide_induction.json")):
            deepcopy(presentation).save(
                join(pptx_config.RUN_DIR, "template.pptx"), layout_only=True
            )
            
            # 将每一页ppt拍一张照片，然后保存到template_images下面
            await ppt_to_images_async(
                join(pptx_config.RUN_DIR, "template.pptx"),
                join(pptx_config.RUN_DIR, "template_images"),
            )
            slide_inducter = SlideInducter(
                presentation,
                join(pptx_config.RUN_DIR, "slide_images"),
                join(pptx_config.RUN_DIR, "template_images"),
                pptx_config,
                models.image_model,
                models.language_model,
                models.vision_model,
            )
            layout_induction = await slide_inducter.layout_induct()
            slide_induction = await slide_inducter.content_induct(layout_induction)
            json.dump(
                slide_induction,
                open(
                    join(pptx_config.RUN_DIR, "slide_induction.json"),
                    "w",
                    encoding="utf-8",
                ),
                ensure_ascii=False,
                indent=4,
            )
        else:
            slide_induction = json.load(
                open(
                    join(pptx_config.RUN_DIR, "slide_induction.json"), encoding="utf-8"
                )
            )
        
        await progress.report_progress()
        
         # PPT Generation with PPTAgent
        ppt_agent = PPTAgent(
            models.language_model,
            models.vision_model,
            error_exit=False,
            retry_times=5,
        )
        ppt_agent.set_reference(
            slide_induction=slide_induction,
            presentation=presentation,
        )

        prs, _ = await ppt_agent.generate_pres(
            source_doc=source_doc,
            num_slides=task["numberOfPages"],
        )
        prs.save(join(generation_config.RUN_DIR, "final.pptx"))
        logger.info(f" generation finished") 
        
        await progress.report_progress()
    except Exception as e:
        await progress.fail_stage(str(e))
        logger.error(f"生成ppt任务失败: {e}")
        traceback.print_exc()
        with open(join(task_dir, "error.log"), "w") as f:
            f.write(traceback.format_exc())
        return
    





# 生成完毕后，下载文件的api
@router.get("/api/download")
async def download(task_id: str, current_user: User = Depends(get_current_user)):
    user_hash_code = hashlib.md5(current_user.id.encode()).hexdigest()
    final_file_path = join(settings.ppt_generation_dir, user_hash_code, task_id, "generation", "final.pptx")
    if not os.path.exists(final_file_path):
        raise HTTPException(status_code=404, detail="Task not created yet")
    if os.path.exists(final_file_path):
        return FileResponse(
            final_file_path,
            media_type="application/pptx",
            headers={"Content-Disposition": "attachment; filename=pptagent.pptx"},
        )
    raise HTTPException(status_code=404, detail="Task not finished yet")

