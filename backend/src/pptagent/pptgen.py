import asyncio
import json
import os
import traceback
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from random import shuffle

from pptagent.agent import Agent
from pptagent.apis import API_TYPES, CodeExecutor
from pptagent.document import Document
from pptagent.llms import AsyncLLM
from pptagent.presentation import (
    GroupShape,
    Layout,
    Picture,
    Presentation,
    SlidePage,
    StyleArg,
)
from pptagent.response import EditorOutput, LayoutChoice, Outline, OutlineItem
from pptagent.utils import (
    Language,
    edit_distance,
    get_logger,
    tenacity_decorator,
)

logger = get_logger(__name__)

style = StyleArg.all_true()
style.area = False


def get_length_factor(src_lan: Language, dst_lang: Language):
    if src_lan.latin == dst_lang.latin:  # belong to the same language family
        return 1.2
    elif src_lan.latin:  # source is latin, dst is cjk
        return 0.7
    else:  # source is cjk, dst is latin
        return 2.0


class FunctionalLayouts(Enum):
    OPENING = "opening"
    TOC = "table of contents"
    SECTION_OUTLINE = "section outline"
    ENDING = "ending"


FunctionalContent = {
    FunctionalLayouts.OPENING.value: "This slide is a presentation opening, presenting available meta information, like title, author, date, etc.",
    FunctionalLayouts.TOC.value: "This slide is the Table of Contents, outlining the presentation's sections. Please use the Table of Contents given in the retrieved content, remove numbering and ensure the completeness of the Table of Contents, and generate the final output with the language specified in the input.",
    FunctionalLayouts.SECTION_OUTLINE.value: "This slide marks the beginning of a new section and should present the content from <title>{}</title> as the section title clearly, any existing prefix or numbering should be removed. If section number is provided in the schema, use <section_number>{}</section_number>. And provide a brief summary of the section if additional elements are provided in the schema.",
    FunctionalLayouts.ENDING.value: "This slide is an *ending slide*, simply express your gratitude like 'Thank you!' or '谢谢' as the main title and *do not* include other meta information if not specified.",
}


@dataclass
class PPTGen(ABC):
    """
    Stage II: Presentation Generation
    An base class for generating PowerPoint presentations.
    It accepts a reference presentation as input, then generates a presentation outline and slides.
    """

    roles = [
        "editor",
        "coder",
        "content_organizer",
        "layout_selector",
    ]

    language_model: AsyncLLM
    vision_model: AsyncLLM
    retry_times: int = 3
    sim_bound: float = 0.5
    force_pages: bool = False
    error_exit: bool = False
    record_cost: bool = False
    _initialized: bool = False

    def __post_init__(self):
        self._hire_staffs(self.record_cost, self.language_model, self.vision_model)

    def set_reference(
        self,
        slide_induction: dict,
        presentation: Presentation,
        hide_small_pic_ratio: float | None = 0.2,
        keep_in_background: bool = True,
    ):
        """
        Set the reference presentation and extracted presentation information.

        Args:
            presentation (Presentation): The presentation object.
            slide_induction (dict): The slide induction data.

        Returns:
            PPTGen: The updated PPTGen object.
        """
        self.presentation = presentation

        self.reference_lang = Language(**slide_induction.pop("language"))
        self.functional_layouts = slide_induction.pop("functional_keys")
        
        self.layouts: dict[str, Layout] = {
            k: Layout(title=k, **v) for k, v in slide_induction.items()
        }

        self.empty_prs = deepcopy(self.presentation)
        
        assert hide_small_pic_ratio is None or hide_small_pic_ratio > 0, (
            "hide_small_pic_ratio must be positive or None"
        )
        
        if hide_small_pic_ratio is not None:
            self._hide_small_pics(hide_small_pic_ratio, keep_in_background)

        self.text_layouts = [
            k
            for k in self.layouts.keys()
            if k.endswith("text") and k not in self.functional_layouts
        ]

        self.multimodal_layouts = [
            k
            for k in self.layouts.keys()
            if not k.endswith("text") and k not in self.functional_layouts
        ]

        if len(self.text_layouts) == 0:
            self.text_layouts = self.multimodal_layouts
        if len(self.multimodal_layouts) == 0:
            self.multimodal_layouts = self.text_layouts

        self._initialized = True
        return self

    async def generate_pres(
        self,
        source_doc: Document,
        num_slides: int | None = None,
        outline: list[OutlineItem] | None = None,
        image_dir: str | None = None,
        dst_language: Language | None = None,
        length_factor: float | None = None,
        auto_length_factor: bool = True,
        max_at_once: int | None = None,
    ):
        """
        Generate a PowerPoint presentation.

        Args:
            source_doc (Document): The source document.
            num_slides (int | None): The number of slides to generate.
            outline (list[OutlineItem] | None): The outline of the presentation.
            image_dir (str | None): The directory of the images.
            dst_language (Language | None): The destination language.
            length_factor (float | None): The length factor.
            auto_length_factor (bool): Whether to automatically calculate the length factor.
            max_at_once (int | None): The maximum number of slides to generate at once.

        Returns:
            tuple[Presentation, dict]: A tuple containing the generated presentation and the history of the agents.
        """
        # validate image existence
        source_doc.validate_medias(image_dir)

        source_doc.metadata["presentation-date"] = datetime.now().strftime("%Y-%m-%d")
        

        # 确保初始化正常再生成
        assert self._initialized, "PPTAgent not initialized, call `set_reference` first"
        
        self.source_doc = source_doc
        
        # 显示，不同语言同样的字符，字符框显示的不一样
        length_factor = length_factor or os.getenv("PPTAGENT_LENGTH_FACTOR", None)
        if (
            auto_length_factor or os.getenv("PPTAGENT_AUTO_LENGTH_FACTOR", False)
        ) and length_factor is None:
            self.dst_lang = dst_language or source_doc.language
            self.length_factor = get_length_factor(self.reference_lang, self.dst_lang)
        else:
            self.length_factor = length_factor
        succ_flag = True
        


        # outline本意就是提纲，如果不存在，我们需要通过需要生成的页数，和pdf的文档进行生成
        # self.outline是一个list
        if outline is None:
            self.outline = await self.generate_outline(num_slides, source_doc)
        else:
            self.outline = outline
        



        # logger.info(f"==========NIUOutline: {self.outline}==========\n")
        pre_section = None
        section_idx = 0
        self.simple_outline = ""
        for slide_idx, item in enumerate(self.outline):
            if item.topic != pre_section and item.topic != "Functional":
                section_idx += 1
                self.simple_outline += f"Section {section_idx}: {item.topic}\n"
                pre_section = item.topic
            

            # 将section的index添加到outline_item中，generate_slide函数中需要用到
            if item.purpose == FunctionalLayouts.SECTION_OUTLINE.value:
                item.indexes.append(section_idx)
            
            self.simple_outline += f"Slide {slide_idx + 1}: {item.purpose}\n"
        # logger.debug(f"==========Outline Generated==========\n{self.simple_outline}")


        if max_at_once:
            semaphore = asyncio.Semaphore(max_at_once)
        else:
            semaphore = AsyncExitStack()

        # 为每一页ppt创建一个任务，然后进行并发处理
        slide_tasks = []
        for slide_idx, outline_item in enumerate(self.outline):
            if self.force_pages and slide_idx == num_slides:
                break
            slide_tasks.append(
                self.generate_slide(slide_idx, outline_item, semaphore=semaphore)
            )

        
        # 并发生成每一页slide
        slide_results = await asyncio.gather(*slide_tasks, return_exceptions=True)

        generated_slides = []
        # 针对每一页slide，我们做了哪些操作，这个也要记录下来
        code_executors = []
        for result in slide_results:
            if isinstance(result, Exception):
                if self.error_exit:
                    succ_flag = False
                    break
                continue
            if result is not None:
                # slide是生成的ppt
                slide, code_executor = result
                generated_slides.append(slide)
                code_executors.append(code_executor)

        history = self._collect_history(
            sum(code_executors, start=CodeExecutor(self.retry_times))
        )

        if succ_flag:
            self.empty_prs.slides = generated_slides
            prs = self.empty_prs
        else:
            prs = None

        self.empty_prs = deepcopy(self.presentation)
        return prs, history

    async def generate_outline(
        self,
        num_slides: int,
        source_doc: Document,
    ):
        """
        Asynchronously generate an outline for the presentation.
        """
        # 确保已经初始化过了
        assert self._initialized, (
            "AsyncPPTAgent not initialized, call `set_reference` first"
        )

        _, outline = await self.staffs["planner"](
            num_slides=num_slides,
            document_overview=source_doc.get_overview(),
            response_format=Outline.response_model(source_doc),
        )
        outline = [OutlineItem(**o) for o in outline["outline"]]
        return self._add_functional_layouts(outline)



    
    @abstractmethod
    def generate_slide(
        self, slide_idx: int, outline_item: OutlineItem, semaphore: AsyncExitStack
    ) -> tuple[SlidePage, CodeExecutor]:
        """
        Generate a slide from the outline item.
        """
        raise NotImplementedError("Subclass must implement this method")


    # 添加功能的layout
    def _add_functional_layouts(self, outline: list[OutlineItem]):
        """
        Add functional layouts to the outline.
        """
        toc = []
        for item in outline:
            if item.topic not in toc and item.topic != "Functional":
                toc.append(item.topic)
        self.toc = "\n".join(toc)

        fixed_functional_slides = [
            (FunctionalLayouts.TOC.value, 0),  # toc should be inserted before opening
            (FunctionalLayouts.OPENING.value, 0),
            (FunctionalLayouts.ENDING.value, 999999),  # append to the end
        ]
        for title, pos in fixed_functional_slides:
            layout = max(
                self.functional_layouts,
                key=lambda x: edit_distance(x.lower(), title),
            )
            if edit_distance(layout, title) > 0.7:
                outline.insert(
                    pos,
                    OutlineItem(
                        purpose=layout, topic="Functional", indexes=[], images=[]
                    ),
                )
        '''
            下面针对outline的逻辑彻底懂了，你看我操作：
            首先我们functional_layouts是大模型推理出来的需要我们拥有的功能布局页
            然后我们找一找其中有没有与section_layout，有说明我们需要在所有语义相同的
            内容页面前面加上这个导航页
        '''
        section_layout = FunctionalLayouts.SECTION_OUTLINE.value
        section_outline = max(
            self.functional_layouts,
            key=lambda x: edit_distance(x, section_layout),
        )
        if not edit_distance(section_outline, section_layout) > 0.7:
            return outline

        # pre_section是前一个section的topic, 下面的代码就是看一看当前的section是否与前一个section相同，如果相同，则不添加，如果不同，则添加一个section_outline页
        # 这样我们就能保证每一页pptx的section都是连续的，不会出现跳跃的情况，判断的依据是每一页的topic
        full_outline = []
        pre_section = None
        for item in outline:
            if item.topic == "Functional":
                full_outline.append(item)
                continue
            if item.topic != pre_section:
                new_item = OutlineItem(
                    purpose=section_outline,
                    topic="Functional",
                    indexes=[item.topic],
                    images=[],
                )
                full_outline.append(new_item)
            full_outline.append(item)
            pre_section = item.topic

        return full_outline

    def _hide_small_pics(self, area_ratio: float, keep_in_background: bool):
        for layout in list(self.layouts.values()):
            template_slide = self.presentation.slides[layout.template_id - 1]
            pictures: list[tuple[SlidePage | GroupShape, Picture]] = list(
                template_slide.shape_filter(Picture, return_father=True)
            )
            if len(pictures) == 0:
                continue
            for father, pic in pictures:
                if pic.area / pic.slide_area < area_ratio:
                    father.shapes.remove(pic)
                    if keep_in_background:
                        template_slide.backgrounds.append(pic)
                    layout.remove_item(pic.caption)

            if len(list(template_slide.shape_filter(Picture))) == 0:
                logger.debug(
                    "All pictures in layout %s are too small, set to pure text layout",
                    layout.title,
                )
                self.layouts[layout.title.replace(":image", ":text")] = (
                    self.layouts.pop(layout.title)
                )

    def _collect_history(self, code_executor: CodeExecutor):
        """
        Collect the history of code execution, API calls and agent steps.

        Returns:
            dict: The collected history data. 
        """
        history = {
            "agents": {},
            "command_history": code_executor.command_history,
            "code_history": code_executor.code_history,
            "api_history": code_executor.api_history,
        }

        for role_name, role in self.staffs.items():
            history["agents"][role_name] = role.history
            role._history = []

        return history

    def _hire_staffs(
        self,
        record_cost: bool,
        language_model: AsyncLLM,
        vision_model: AsyncLLM,
    ) -> dict[str, Agent]:
        """
            Initialize agent roles and their models
        """
        llm_mapping = {
            "language": language_model,
            "vision": vision_model,
        }
        self.staffs = {
            role: Agent(
                role,
                record_cost=record_cost,
                llm_mapping=llm_mapping,
            )
            for role in ["planner"] + self.roles
        }


class PPTAgent(PPTGen):
    """
    Asynchronous subclass of PPTGen that uses Agent for concurrent processing.
    """




    async def generate_slide(
        self, slide_idx: int, outline_item: OutlineItem, semaphore: AsyncExitStack
    ) -> tuple[SlidePage, CodeExecutor]:
        """
        Asynchronously generate a slide from the outline item.
        """


        async with semaphore:
            # 生成功能页
            print(f"\n ====Generating slide {slide_idx} with outline item {outline_item}====\n")
            if outline_item.topic == "Functional":

                # outline_item 表示的是当前的规划是什么，根据这个规划来组织pptx
                layout = self.layouts[outline_item.purpose]

                # 找到这个功能slide的相关描述
                slide_desc = FunctionalContent[outline_item.purpose]
                
                # 如果是section_outline
                if outline_item.purpose == FunctionalLayouts.SECTION_OUTLINE.value:
                    
                    # 这里与generate_outline函数中添加的section_outline页的index有关
                    section, sec_idx = outline_item.indexes


                    slide_desc = slide_desc.format(section, sec_idx + 1)
                    outline_item.purpose = f"Section Outline of {section}"

                    outline_item.indexes = []
                    slide_content = (
                        "Document Structure:\n"
                        + self.source_doc.get_overview(
                            include_summary=True, include_image=False
                        )
                    )
                elif outline_item.purpose == FunctionalLayouts.TOC.value:
                    # 整个pptx的目录，所以需要将每一个slide的topic全部列出来
                    slide_content = "Table of Contents:\n" + self.toc
                else:
                    slide_content = "This slide is a functional layout, please follow the slide description and content schema to generate the slide content."
                header, _, _ = outline_item.retrieve(slide_idx, self.source_doc)
                header += slide_desc

            else:

                # 提取处布局，标题和里面的内容
                '''
                    layout是选择的布局；
                    header是这个slide目的和主要的内容
                    slide_content是这个slide具体的内容来源（pdf）
                '''
                layout, header, slide_content = await self._select_layout(
                    slide_idx, outline_item
                )
                
            try:
                # 在这里我们可以这样理解，layout是这个slide的布局，slide_content 是这个slide1具体的内容；header是这个slide目的是什么？
                command_list, template_id = await self._generate_content(
                    layout, slide_content, header
                )
                
                slide, code_executor = await self._edit_slide(command_list, template_id)
            
            except Exception as e:
                logger.error(f"Failed to generate slide {slide_idx}, error: {e}")
                traceback.print_exc()
                raise e
            return slide, code_executor



    @tenacity_decorator
    async def _select_layout(
        self, slide_idx: int, outline_item: OutlineItem
    ) -> tuple[Layout, str, str]:
        """
        Asynchronously select a layout for the slide.
        """
        header, content_source, images = outline_item.retrieve(
            slide_idx, self.source_doc
        )
        
        
        if len(content_source) == 0:
            key_points = []
        
        else:

            _, key_points = await self.staffs["content_organizer"](
                content_source=content_source
            )

        slide_content = json.dumps(key_points, indent=2, ensure_ascii=False)

        
        layouts = self.text_layouts


        # 因为有图片，所以我们需要选择多模态的布局
        if len(images) > 0:
            slide_content += "\nImages:\n" + "\n".join(images)
            layouts = self.multimodal_layouts


        # 随机打乱布局，然后选择一个布局
        shuffle(layouts)
        
        # 选择布局，返回这个布局的名字，以及为什么选择这个布局
        _, layout_selection = await self.staffs["layout_selector"](
            outline=self.simple_outline,
            slide_description=header,
            slide_content=slide_content,
            available_layouts=layouts,
            response_format=LayoutChoice.response_model(layouts),
        )


        # 选择布局，返回这个布局的名字
        layout = layout_selection["layout"]

        # 讲iamge的部分去除
        if "image" not in layout and len(images) > 0:
            slide_content = slide_content[: slide_content.rfind("\nImages:\n")]
        
        # slide_content是这个slide1具体的内容来源（pdf）；header是这个slide目的是什么？
        return self.layouts[layout], header, slide_content

    async def _generate_content(
        self,
        layout: Layout,
        slide_content: str,
        slide_description: str,
    ) -> tuple[list, int]:
        """
        Asynchronously generate content for the slide.

        """
        '''
            layout: Layout, 选择的布局
            slide_content: str,这个slide具体的内容来源（pdf）
            slide_description: str, 这个slide目的是什么？
        '''

        
        elements = [el.name for el in layout.elements]

        print(f"\n++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        print(f"\n ====Slide content: {slide_content}====\n")
        print(f"\n ====Slide description: {slide_description}====\n")
        print(f"\n ====Simple outline: {self.simple_outline}====\n")
        print(f"\n ====Metadata: {self.source_doc.metainfo}====\n")
        print(f"\n ====Language: {self.dst_lang.lid}====\n")
        print(f"\n ====Elements: {elements}====\n")
        print(f"\n ====Layout: {layout.content_schema}====\n")
        print(f"\n++++++++++++++++++++++++++++++++++++++++++++++++++++\n")


        turn_id, editor_output = await self.staffs["editor"](
            outline=self.simple_outline,
            slide_description=slide_description,
            metadata=self.source_doc.metainfo,
            slide_content=slide_content,
            schema=layout.content_schema,
            language=self.dst_lang.lid,
            response_format=EditorOutput.response_model(elements),
        )
        
        logger.info(f"==========NIUEditor Output: {editor_output}==========\n")
        # 这里其实看源码，可以在里面用parse解决的
        editor_output = EditorOutput(**editor_output)
        
        await self._validate_content(editor_output, layout, turn_id)
        
        
        logger.info(f"==========NIULayout : {layout}==========\n")
        command_list, template_id = self._generate_commands(editor_output, layout)
        logger.info(f"==========NIUCommand List: {command_list}==========\n")
        return command_list, template_id

    async def _edit_slide(
        self, command_list: list, template_id: int
    ) -> tuple[SlidePage, CodeExecutor]:
        """
        Asynchronously edit the slide.
        """
        
        code_executor = CodeExecutor(self.retry_times)
        
        code_executor.command_history.append(command_list)
        
        
        logger.info(f"==========NIUAPI Docs: {code_executor.get_apis_docs(API_TYPES.Agent.value)}==========\n")
        logger.info(f"==========NIUTarget Slide: {self.presentation.slides[template_id - 1].to_html()}==========\n")
        logger.info(f"==========NIUCommand List: \n{'\n'.join([str(i) for i in command_list])}==========\n")
        turn_id, edit_actions = await self.staffs["coder"](
            api_docs=code_executor.get_apis_docs(API_TYPES.Agent.value),
            edit_target=self.presentation.slides[template_id - 1].to_html(),
            command_list="\n".join([str(i) for i in command_list]),
        )
        logger.info(f"==========NIUTurn ID: {turn_id}==========\n")
        logger.info(f"==========NIUEdit Actions: {edit_actions}==========\n")
        
        
        for error_idx in range(self.retry_times):
            edit_slide: SlidePage = deepcopy(self.presentation.slides[template_id - 1])
            print(f"\n &&&&&&&&Edit slide: {edit_actions}&&&&&&&&\n")
            feedback = code_executor.execute_actions(
                edit_actions, edit_slide, self.source_doc
            )
            if feedback is None:
                break
            logger.warning(
                "Failed to generate slide, tried %d/%d times, error: %s\n%s",
                error_idx + 1,
                self.retry_times,
                str(feedback[1]),
                edit_actions,
            )
            if error_idx == self.retry_times:
                raise Exception(
                    f"Failed to generate slide, tried too many times at editing\ntraceback: {feedback[1]}"
                )
            #Self Correction 
            edit_actions = await self.staffs["coder"].retry(
                feedback[0], feedback[1], turn_id, error_idx + 1
            )
        self.empty_prs.validate(edit_slide)
        return edit_slide, code_executor

    async def _validate_content(
        self, editor_output: EditorOutput, layout: Layout, turn_id: int, retry: int = 0
    ):
        """
        Asynchronously generate commands for editing the slide content.

        Args:
            editor_output (dict): The editor output.
            layout (Layout): The layout object containing content schema.
            turn_id (int): The turn ID for retrying.
            retry (int, optional): The number of retries. Defaults to 0.

        Returns:
            list: A list of commands.

        Raises:
            Exception: If command generation fails.
        """
        try:
            allowed_images = [m.path for m in self.source_doc.iter_medias()]
            layout.validate(editor_output, allowed_images)
            if self.length_factor is not None:
                await layout.length_rewrite(
                    editor_output, self.length_factor, self.language_model
                )
        except Exception as e:
            if retry < self.retry_times:
                new_output = await self.staffs["editor"].retry(
                    e,
                    traceback.format_exc(),
                    turn_id,
                    retry + 1,
                    response_format=EditorOutput,
                )
                return await self._validate_content(
                    EditorOutput(**new_output), layout, turn_id, retry + 1
                )
            else:
                raise Exception(
                    f"Failed to generate commands, tried too many times at editing\ntraceback: {e}"
                )

    def _generate_commands(self, editor_output: EditorOutput, layout: Layout):
        command_list = []
        template_id, old_data = layout.index_template_slide(editor_output)
        for el_name, old_content in old_data.items():
            new_content = (
                editor_output[el_name].data if el_name in editor_output else []
            )
            quantity_change = len(new_content) - len(old_content)
            command_list.append(
                (
                    el_name,
                    layout[el_name].type,
                    f"quantity_change: {quantity_change}",
                    old_content,
                    new_content,
                )
            )
        return command_list, template_id
