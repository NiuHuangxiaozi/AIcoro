from pptagent.pptgen import PPTAgent
from os.path import join
from pptagent.model_utils import ModelManager
from pptagent.presentation import Presentation
from pptagent.utils import Config
from copy import deepcopy
import os
import json
import asyncio
from pptagent.utils import ppt_to_images_async
from pptagent.induct import SlideInducter
from pptagent.document import Document
from pptagent.multimodal import ImageLabler
from pptagent.model_utils import parse_pdf


models = ModelManager()

async def test_generate_slide():
    task_dir=join('./test', 'test_generate_slide')
    pptx_config = Config(join(task_dir, "pptx", "default_template"))
    pdf_config = Config(join(task_dir, "pdf"))

    presentation = Presentation.from_file(
        join(pptx_config.RUN_DIR, "source.pptx"), pptx_config
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
    pptgen = PPTAgent(
        language_model=models.language_model,
        vision_model=models.vision_model,
    ).set_reference(
        presentation=presentation,
        slide_induction=slide_induction,
    )
    
    prs, _ = await pptgen.generate_pres(
            source_doc=source_doc,
            num_slides=4,
    )

    prs.save(join(pptx_config.RUN_DIR, "final.pptx"))




asyncio.run(test_generate_slide())