import ast
# import inspect 导入的是 Python 的 内省（introspection）模块，它用于在运行时检查（查看、分析）Python 对象的各种信息。
import inspect
import os
import re
# 导入的是 Python 的字符串模板功能，它用于安全的字符串格式化
#  简单的变量替换
from string import Template
from typing import List, Callable, Tuple, Dict
from openai import OpenAI
# import platform 导入的是 Python 的平台信息模块，它用于获取和识别当前运行环境的系统硬件和软件信息。
import platform
from .template import react_system_prompt_template

from ..config import settings


class ReActAgent:
    def __init__(self, 
                 tools: List[Callable],
                 model: str,
                 project_directory: str):
        self.tools = { func.__name__: func for func in tools }
        
        # 获得model的所有信息
        if model == "deepseek-chat":
            self.model_base_url =settings.deepseek_base_url
            self.model_api_key = settings.deepseek_api_key
            self.model_name =  settings.deepseek_chat_model
        elif model == "deepseek-reasoner":
            self.model_base_url =settings.deepseek_base_url
            self.model_api_key = settings.deepseek_api_key
            self.model_name =  settings.deepseek_reasoner_model
        
        # 代码的工作目录
        self.project_directory = project_directory
        
        
        self.client = OpenAI(
            base_url=self.model_base_url,
            api_key=self.model_api_key,
        )
        

    def run(self, user_input: str):
        
        # 详细是一个list，是一个一个的模板
        messages = [
            {
                "role": "system",
                "content": self.render_system_prompt(react_system_prompt_template)},
            # 用户的提问
            {
                "role": "user",
                "content": f"<question>{user_input}</question>"
            }
        ]

        while True:

            # 请求模型
            content = self.call_model(messages)

            # 检测 Thought
            '''
                这里的正则表达式：
                    () :捕获组，用于提取匹配的内容
            '''
            thought_match = re.search(r"<thought>(.*?)</thought>", content, re.DOTALL)
            if thought_match:
                # group 是一个捕获组，group就是获取第一个左括号对应的内容
                thought = thought_match.group(1)
                # 将模型的思考加入上下文
                print(f"\n\n💭 Thought: {thought}")

            # 检测模型是否输出 Final Answer，如果是的话，直接返回
            if "<final_answer>" in content:
                final_answer = re.search(r"<final_answer>(.*?)</final_answer>", content, re.DOTALL)
                return final_answer.group(1)

            
            # 检测 Action
            action_match = re.search(r"<action>(.*?)</action>", content, re.DOTALL)
            if not action_match:
                raise RuntimeError("模型未输出 <action>")
            action = action_match.group(1)
            
            # 解释我们的行为
            tool_name, args = self.parse_action(action)

            print(f"\n\n🔧 Action: {tool_name}({', '.join(args)})")
            
            
            # 只有终端命令才需要询问用户，其他的工具直接执行
            # 重要的改变环境的命令用户确定
            # should_continue = input(f"\n\n是否继续？（Y/N）") if tool_name == "run_terminal_command" else "y"
            should_continue = 'y'
            if should_continue.lower() != 'y':
                print("\n\n操作已取消。")
                return "操作被用户取消"

            
            try:
                # 执行函数并且得到返回值，也就是环境的观察值
                observation = self.tools[tool_name](*args)
            except Exception as e:
                observation = f"工具执行错误：{str(e)}"
            
            # 将用户的观察继续加入到消息队列里面
            print(f"\n\n🔍 Observation：{observation}")
            obs_msg = f"<observation>{observation}</observation>"
            messages.append({"role": "user", "content": obs_msg})


    def get_tool_list(self) -> str:
        """生成工具列表字符串，包含函数签名和简要说明"""
        tool_descriptions = []
        for func in self.tools.values():
            
            # 每一个函数的名字
            name = func.__name__
            
            # 获得参数的字符串表示
            signature = str(inspect.signature(func))
            
            # 获得这个函数的说明
            doc = inspect.getdoc(func)
            
            # 一个函数的说明由三元组确定
            tool_descriptions.append(f"- {name}{signature}: {doc}")
        
        # 使用换行符将所有tool的解释串联在一起
        return "\n".join(tool_descriptions)
    
    
    
    def render_system_prompt(self, system_prompt_template: str) -> str:
        
        """渲染系统提示模板，替换变量"""
        tool_list = self.get_tool_list()
        
        # self.project_directory is /home/ubuntu/ai_agent/target
        # 这个应该就是告诉模型我们工作目录已经定义好了什么文件
        file_list = ", ".join(
            os.path.abspath(os.path.join(self.project_directory, f))
            for f in os.listdir(self.project_directory)
        )
        return Template(system_prompt_template).substitute(
            operating_system=self.get_operating_system_name(),
            tool_list=tool_list,
            file_list=file_list
        )
        
        
    def call_model(self, messages):
        print("\n\n正在请求模型，请稍等...")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        content = response.choices[0].message.content
        # 调用模型，将模型的回答放到对话历史里面
        messages.append({"role": "assistant", "content": content})
        return content

    # 解析出函数的名称和对应的参数
    def parse_action(self, code_str: str) -> Tuple[str, List[str]]:
        
        # (\w+) 提取函数名字，这是转义括号，匹配实际的字符 ( 和 )。
        # . 默认匹配除 \n 外的任何字符，* 表示重复任意次（包含零次），括号定义成第二个捕获组。
        match = re.match(r'(\w+)\((.*)\)', code_str, re.DOTALL)
        
        # 不是一个正常的函数调用
        if not match:
            raise ValueError("Invalid function call syntax")

        func_name = match.group(1)
        args_str = match.group(2).strip()

        # 手动解析参数，特别处理包含多行内容的字符串
        args = []
        current_arg = ""
        
        #
        in_string = False
        string_char = None
        i = 0
        paren_depth = 0
        
        
        while i < len(args_str):
            # 选取某一个字符
            char = args_str[i]
            
            
            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                    current_arg += char
                elif char == '(':
                    paren_depth += 1
                    current_arg += char
                elif char == ')':
                    paren_depth -= 1
                    current_arg += char
                elif char == ',' and paren_depth == 0:
                    # 遇到顶层逗号，结束当前参数
                    args.append(self._parse_single_arg(current_arg.strip()))
                    current_arg = ""
                else:
                    current_arg += char
            else:
                # 这里在字符串里面应该指的是default变量，就是a="hellod"的情况
                # (i == 0 or args_str[i-1] != '\\') 这个指的是 "hello, \"world\""
                current_arg += char
                if char == string_char and (i == 0 or args_str[i-1] != '\\'):
                    in_string = False
                    string_char = None
            
            i += 1
        
        # 添加最后一个参数
        if current_arg.strip():
            args.append(self._parse_single_arg(current_arg.strip()))
        
        return func_name, args
    
    
    # 解析单个单词
    def _parse_single_arg(self, arg_str: str):
        """解析单个参数"""
        
        # 清除收尾的空格
        arg_str = arg_str.strip()
        
        # 如果是字符串字面量
        if (arg_str.startswith('"') and arg_str.endswith('"')) or \
           (arg_str.startswith("'") and arg_str.endswith("'")):
            # 移除外层引号并处理转义字符
            inner_str = arg_str[1:-1]
            # 处理常见的转义字符
            
            # 这里我懂了为了文字传输，我们需要把\n（换行）这样的不能表示的东西转为\t
            # 让python的解释器能够知道这是一个换行符
            inner_str = inner_str.replace('\\"', '"').replace("\\'", "'")
            inner_str = inner_str.replace('\\n', '\n').replace('\\t', '\t')
            inner_str = inner_str.replace('\\r', '\r').replace('\\\\', '\\')
            return inner_str
        
        # 尝试使用 ast.literal_eval 解析其他类型
        try:
            # 就是把字符串变为真实的东西比如 '1' 变为1
            return ast.literal_eval(arg_str)
        except (SyntaxError, ValueError):
            # 如果解析失败，返回原始字符串
            return arg_str

    # 系统对于编码也有影响
    def get_operating_system_name(self):
        os_map = {
            "Darwin": "macOS",
            "Windows": "Windows",
            "Linux": "Linux"
        }

        return os_map.get(platform.system(), "Unknown")



# 下面是三个工具
def _read_file(file_path):
    """用于读取文件内容"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def _write_to_file(file_path, content):
    """将指定内容写入指定文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content.replace("\\n", "\n"))
    return "写入成功"

def _run_terminal_command(command):
    """用于执行终端命令"""
    import subprocess
    run_result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return "执行成功" if run_result.returncode == 0 else run_result.stderr

# 删除文件
def _delete_file(file_path):
    """删除指定文件，如果文件不存在则静默处理"""
    try:
        os.remove(file_path)
        return f"成功删除文件{file_path}"
    except FileNotFoundError:
        return f"文件不存在: {file_path}"

    except PermissionError:
        return f"权限不足，无法删除: {file_path}"
    except Exception as e:
        return f"删除文件时发生错误: {e}"








# code agent export interface
def get_code_agent_response(
                            task,
                            project_directory,
                            model):
    '''
        task: 用户想要作者实现什么代码
        project_directory：为每一个用户实现单独的代码空间，所以就用userid-sessionid-root来指代
        model： 就是调用模型的名称
    '''
    
    
    project_dir = os.path.abspath(project_directory)
    
    # 三个命令工具
    tools = [_read_file, _write_to_file, _run_terminal_command, _delete_file]
    
    
    # 创建一个agent，我们使用deepseek
    agent = ReActAgent(tools=tools,
                       model=model,
                       project_directory=project_dir)

    final_answer = agent.run(task)

    print(f"Function[get_code_agent_response]:\n\n✅ Final Answer：{final_answer}")
    
    return final_answer 





