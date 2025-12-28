from typing import Literal
from pydantic import BaseModel, Field, create_model

class SlideElement(BaseModel):
    name: str
    data: list[str]

    @classmethod
    def response_model(cls, elements: list[str]):
        if not elements:
            raise ValueError("elements 不能为空！")
        return create_model(
            cls.__name__,  # 新类名叫 "SlideElement"
            name=(Literal[tuple(elements)], Field(...)),  # 必填，且只能是 elements 中的值
            data=(list[str], Field(...)),                  # 必填，字符串列表
            __base__=BaseModel,                           # 继承 BaseModel
        )

# Field表示的是必填的意思
SlideElementResponse = SlideElement.response_model(["title", "content"])
slide_element = SlideElementResponse(name="title", data=["我爱南京"])
slide_element = SlideElementResponse(name="content", data=["我爱南京", "我爱北京"])
print(slide_element)
print(slide_element.model_dump_json())

slide_element = SlideElementResponse(name="asdf", data=["我爱东京"])
print(slide_element)