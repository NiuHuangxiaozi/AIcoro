import asyncio
import os
import re
from contextlib import AsyncExitStack
from os.path import basename, exists, join

from jinja2 import Environment, StrictUndefined
from pydantic import BaseModel, Field, create_model

from pptagent.agent import Agent
from pptagent.llms import AsyncLLM
from pptagent.model_utils import language_id
from pptagent.utils import (
    Language,
    get_logger,
    package_join,
)

from .doc_utils import (
    get_tree_structure,
    process_markdown_content,
    split_markdown_by_headings,
)
from .element import Media, Metadata, Section, SubSection, Table, link_medias

logger = get_logger(__name__)

env = Environment(undefined=StrictUndefined)

MERGE_METADATA_PROMPT = env.from_string(
    open(
        package_join("prompts", "document", "merge_metadata.txt"), encoding="utf-8"
    ).read()
)
LITERAL_CONSTRAINT = os.getenv("LITERAL_CONSTRAINT", "false").lower() == "true"


class Document(BaseModel):
    image_dir: str
    language: Language
    metadata: dict[str, str]
    sections: list[Section]

    # image_dir存放了原本pdf的相关路径，我们需要确保pdf里面图片的路径都存在
    def validate_medias(self, image_dir: str | None = None):
        """Validate and fix media file paths"""
        if image_dir is not None:
            self.image_dir = image_dir
        assert exists(self.image_dir), f"image directory is not found: {self.image_dir}"
        for media in self.iter_medias():
            if exists(media.path):
                continue
            base_name = basename(media.path)
            if exists(join(self.image_dir, base_name)):
                media.path = join(self.image_dir, base_name)
            else:
                raise FileNotFoundError(f"image file not found: {media.path}")

    def get_overview(self, include_summary: bool = False, include_image: bool = True):
        """Get document overview with sections and subsections"""
        overview = ""
        for section in self.sections:
            overview += f"<section>{section.title}</section>\n"
            if include_summary:
                overview += f"\tSummary: {section.summary}\n"
            for subsection in section.content:
                if isinstance(subsection, SubSection):
                    overview += f"\t<subsection>{subsection.title}</subsection>\n"
                elif include_image and isinstance(subsection, Media):
                    overview += (
                        f"\t<image>{subsection.path}</image>: {subsection.caption}\n"
                    )
            overview += "\n"
        return overview

    def iter_medias(self):
        """Iterate over all media items in the document"""
        for section in self.sections:
            yield from section.iter_medias()

    def find_media(self, caption: str | None = None, path: str | None = None):
        """Find media by caption or path"""
        for media in self.iter_medias():
            if caption is not None and media.caption == caption:
                return media
            if path is not None and media.path == path:
                return media
        raise ValueError(f"Image caption or path not found: {caption} or {path}")

    @classmethod
    async def _parse_chunk(
        cls,
        extractor: Agent,
        markdown_chunk: str,
        image_dir: str,
        language_model: AsyncLLM,
        vision_model: AsyncLLM,
        limiter: asyncio.Semaphore | AsyncExitStack,
    ):
        # 读入每一段md文字，然后将里面的文字全部提取出来，然后返回为markdown，然后对于每一种模态（图片）返回一个list
        markdown, medias = process_markdown_content(
            markdown_chunk,
        )
        async with limiter:
            # 对于这个文字chunk进行总结，并且划分为多喝subection
            _, section = await extractor(
                markdown_document=markdown,
                response_format=Section.response_model(),
            )
            metadata = section.pop("metadata", {})
            section["content"] = section.pop("subsections")
            
            # 为每一个chunk创建一个Section
            section = Section(**section, markdown_content=markdown_chunk)
            
            
            # 本质是将medias添加进如section里面的list里面
            # 对于每一个分块，作者将其抽象为了一个Section，Section里面有有一个list，里面的元素
            # 就是一个文本段Subsection，表格（Table）和图片（Medias）的集合
            # 所以这里的link的意思是将图片插到与之最相关的Subsection的周围，使用到的办法是计算文本相似度
            # 
            link_medias(medias, section)
            
            async with asyncio.TaskGroup() as tg:
                for media in section.iter_medias():
                    # 针对每一个图片，作者调用parse函数，这个函数的作用是解析图片的path，并且将图片的path保存到media的path属性中
                    media.parse(image_dir)
                    if isinstance(media, Table):
                        tg.create_task(media.get_caption(language_model))
                    # 针对每一个图片，作者调用get_caption函数，这个函数的作用是使用vision_model生成图片的caption
                    # 针对每一个表格，作者调用get_caption函数，这个函数的作用是使用language_model生成表格的caption
                    else:
                        # 针对每一个图片，作者调用get_caption函数，这个函数的作用是使用vision_model生成图片的caption
                        tg.create_task(media.get_caption(vision_model))
        return metadata, section

    @classmethod
    async def from_markdown(
        cls,
        markdown_content: str,
        language_model: AsyncLLM,
        vision_model: AsyncLLM,
        image_dir: str,
        max_at_once: int | None = None,
    ):
        doc_extractor = Agent(
            "doc_extractor",
            llm_mapping={"language": language_model, "vision": vision_model},
        )
        
        # 正因为manerU返回的是md格式的pdf解析，所以这列才能调用from_markdown函数
        # 也就是说markdown_content指的是这个content指的是markdown格式
        document_tree = get_tree_structure(markdown_content)
        
        headings = re.findall(r"^#+\s+.*", markdown_content, re.MULTILINE)
        
        # 按照md的标题进行切分 ，比如 #， ##， ###， 等等
        splited_chunks = await split_markdown_by_headings(
            markdown_content, headings, document_tree, language_model
        )

        metadata = []
        sections = []
        tasks = []

        limiter = (
            asyncio.Semaphore(max_at_once)
            if max_at_once is not None
            else AsyncExitStack()
        )
        async with asyncio.TaskGroup() as tg:
            for chunk in splited_chunks:
                tasks.append(
                    tg.create_task(
                        cls._parse_chunk(
                            doc_extractor,
                            chunk,
                            image_dir,
                            language_model,
                            vision_model,
                            limiter,
                        )
                    )
                )

        # Process results in order
        for task in tasks:
            meta, section = task.result()
            metadata.append(meta)
            sections.append(section)

        merged_metadata = await language_model(
            MERGE_METADATA_PROMPT.render(metadata=metadata),
            return_json=True,
            response_format=create_model(
                "MetadataList",
                metadata=(list[Metadata], Field(...)),
                __base__=BaseModel,
            ),
        )
        metadata = {meta["name"]: meta["value"] for meta in merged_metadata["metadata"]}
        
        '''
            所以我现在才看懂，原来image_dir 保存原来md里里面图片或者表格的图像的把文件夹，照片的名字是
            内容的md5值调取专业的模型判断传入的md的语言
            最后两个返回的是metadata 元信息，作者为每一个不大也不小的文本块都使用llmagent提取了元信息，将这些信息全部整合
            在一起形成一个list，这样就成为了metadata这个list
            同理，我们也可以看到sections这个list，这个list里面存储的是每一个不大也不小的文本块的Section，也就是Section这个类
            作者将每一个Section都存储在了sections这个list里面，这样就成为了sections这个list
            每一个Section的content也是一个list，里面包含图片、文本和表格
        '''
        return cls(
            image_dir=image_dir,
            language=language_id(markdown_content),
            metadata=metadata,
            sections=sections,
        )

    def index(self, target_item: SubSection | Media | Table):
        """Get the index position of a content item"""
        for i, (_, content) in enumerate(self):
            if content is target_item:
                return i
        raise ValueError("Item not found in document")

    def pop(self, index: int):
        """Remove and return content item at specified index position"""
        for idx, (section, content) in enumerate(self):
            if idx == index:
                return section.content.pop(section.content.index(content))
        raise IndexError("Index out of range")

    def insert(self, item: SubSection | Media | Table, target_index: int):
        """Insert content item after the specified index position"""
        for idx, (section, content) in enumerate(self):
            if idx == target_index:
                section.content.insert(section.content.index(content), item)
                return

        self.sections[-1].content.append(item)

    def remove(self, target_item: SubSection | Media | Table):
        """Remove content item from document"""
        for section, content in self:
            if content is target_item:
                section.content.remove(target_item)
                return
        raise ValueError("Item not found in document")

    def __contains__(self, key: str):
        for section in self.sections:
            if section.title == key:
                return True
        return False

    def __iter__(self):
        for section in self.sections:
            for content in section.content:
                yield section, content

    def __getitem__(self, key: int | slice | str):
        """Get content item by index, slice or section title"""
        if isinstance(key, slice):
            return [content for _, content in list(self)[key]]
        else:
            for i, (sec, content) in enumerate(self):
                if i == key:
                    return content
                elif sec.title == key:
                    return sec
            raise IndexError(f"Index out of range: {key}")

    @property
    def metainfo(self):
        return "\n".join([f"{k}: {v}" for k, v in self.metadata.items()])
