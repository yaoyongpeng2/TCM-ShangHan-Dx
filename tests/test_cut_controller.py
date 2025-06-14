import sys, os
from pathlib import Path
def find_project_root(fileAbsPath:str)->str:
    parts=[part for part in Path(fileAbsPath).parts]
    uplevel=len(parts)-1-parts.index("tests")#以"tests"目录为锚定点
    root_dir = Path(fileAbsPath).resolve().parents[uplevel]
    return root_dir

PROJECT_ROOT= find_project_root(__file__)
print(f"\n{PROJECT_ROOT=}")
sys.path.insert(0, str(PROJECT_ROOT)+"/src")  # 确保优先搜索项目<根目录>/src

from fastapi.testclient import TestClient
import unittest
#from cutter_controller import CUT_TEXT_PATH, DataRequest, DataResponse
from cutter_controller import *

class TestCutterController(unittest.TestCase):

    def test_cut_text(self):
        #FastAPI的TestClient基于ASGI标准，工作原理如下：
        # 1. ​​绕过网络层​​：不通过HTTP协议通信，而是直接调用FastAPI的ASGI应用 
        # 2. ​​内存通信​​：请求/响应在内存中完成，不经过网络传输 
        # 3. ​​完整流程​​： 
        #   将请求转换为ASGI的scope字典 
        #   → 构建请求头部和内容 
        #   → 调用FastAPI应用的处理逻辑 
        #   → 获取响应对象并转换为TestClient响应格式
        client =TestClient(app)
        #client =TestClient(app,base_url=f"http://{HOST}:{PORT}")#不必指定，因为内存通信

        texts=[
            "397.伤寒解后，虚羸少气，气逆欲吐，竹叶石膏汤主之。"
            ,"188.伤寒转系阳明者，其人濈然微汗出也。"
        ]
        dict=["虚羸少气","竹叶石膏汤"
              ,'濈然微汗出','濈然汗出','濈然','微汗出','微微','微汗','汗出'
            
        ]
        with_dict_expects=[
            ['397', '伤寒', '解后', '虚羸少气', '气逆欲', '吐', '竹叶石膏汤','主之']
            ,['188', '伤寒', '转系', '阳明', '者', '其', '人', '濈然微汗出', '也']
        ]
        for text,expected in zip(texts,with_dict_expects):
            request=DataRequest(text)
            expected=DataResponse(request.text,expected)
            request_dict=request.model_dump()
        #    request_json='{"text":"'+text+'"}'
            response=client.post(CUT_TEXT_PATH,json=request_dict)
            response_json=response.json()
            assert response.status_code==200
            assert expected.raw==response_json["raw"]
            assert expected==response_json["tokens"]

if  __name__=="__main__":
    unittest.main()