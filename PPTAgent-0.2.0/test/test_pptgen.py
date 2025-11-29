from os.path import join

import pytest

from pptagent.document import Document
from pptagent.multimodal import ImageLabler
from pptagent.pptgen import PPTAgent
from pptagent.presentation import Presentation
from test.conftest import test_config


@pytest.mark.asyncio
@pytest.mark.llm
async def test_pptgen():
    
    
    
    
    
    '''
        下面的slide_induction就是对于源source.pptx里面内容的总结，就是每一个用了什么layout，模态是文本还是图片，然后这样的情况出现在
        哪些pptx（index），然后这些pptx的index是什么。
    '''
    pptgen = PPTAgent(
        language_model=test_config.language_model,
        vision_model=test_config.vision_model,
    ).set_reference(
        presentation=Presentation.from_file(
            join(test_config.template, "source.pptx"), test_config.config
        ),
        slide_induction=test_config.get_slide_induction(),
    )
    
    '''
        labeler就是一个标签器，作用是将源文件source.pptx里面的图片用视觉语言模型打上标签，然后保存为image_stats.json文件。
        这个文件记录了图片的caption、size、appear_times、slide_numbers等信息。
        这个文件是后续生成ppt的依据（存疑，不知道新的pptx为什么用老图片，为一想到的是提供模板的时候图片就是相关的）。
        如果image_stats.json文件不存在，则需要调用caption_images_async方法来生成。
    '''
    labeler = ImageLabler(pptgen.presentation, test_config.config)
    labeler.apply_stats(test_config.get_image_stats())

    
    
    # 对于上传的pdf的全面解析，返回了一个提取pdf信息的句柄document
    document = Document(**test_config.get_document_json())
    
    # TODO
    result = await pptgen.generate_pres(document, 3)
    prs, history = result
    print(f"staffs history\n: {history}\n")