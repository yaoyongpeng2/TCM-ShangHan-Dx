
from collections import defaultdict
import unittest
import sys, os
from pathlib import Path
import json
def find_project_root(fileAbsPath:str)->str:
    parts=[part for part in Path(fileAbsPath).parts]
    uplevel=len(parts)-1-parts.index("tests")#以"tests"目录为锚定点
    root_dir = Path(fileAbsPath).resolve().parents[uplevel]
    return root_dir

PROJECT_ROOT= find_project_root(__file__)
print(f"\n{PROJECT_ROOT=}")
sys.path.insert(0, str(PROJECT_ROOT)+"/src")  # 确保优先搜索项目<根目录>/src

from diagnosis.diagnosis import *
#目的：
# 1.更多的数据比较不同算法的推荐准确率
# 2. 放在测试用例里的好处：启动方便，隔离输入数据：一个测试函数vs一个输入数据vs一个功能模块
class TestCaseVerify(unittest.TestCase):

    # def __init__(self):
    #     self.diagnosis=Diagnosis()

    def prepare_data(self):
        split_dict={
            "死循环检测":{"死循环检测"},
            "太阳病":{"脉浮","头项强痛","恶寒"},
            "中风":{"太阳病","发热","汗出","恶风","脉缓"},
            "伤寒":{"太阳病","恶寒","体痛","呕逆","脉阴阳俱紧"}
        }
        expected={
            "不存在":{"不存在"},
            "死循环检测":{"死循环检测"},
            "太阳病":{"脉浮","头项强痛","恶寒"},
            "中风":{"脉浮","头项强痛","恶寒","发热","汗出","恶风","脉缓"},
            "伤寒":{"脉浮","头项强痛","恶寒","体痛","呕逆","脉阴阳俱紧"}#两个"恶寒"（太阳病+本身），去重一个
        }
        return (split_dict,expected)      

    def test_split_term(self):
        split_dict,expected=self.prepare_data()
        for t in expected:
            assert expected[t]==Diagnosis.split_term(t,split_dict)

if  __name__=="__main__":
    unittest.main()