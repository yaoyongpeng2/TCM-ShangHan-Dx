import unittest
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

from nlp.word_cut import WordCutter

class TestWordSegmenter(unittest.TestCase):
    
    def test_segment(self):
        cutter=WordCutter()
        texts=[
            "397.伤寒解后，虚羸少气，气逆欲吐，竹叶石膏汤主之。"
            ,"188.伤寒转系阳明者，其人濈然微汗出也。"
            ,"濈然微汗出，濈然汗出，濈然单列，微汗出，微微汗出,"#词典里有'濈然微汗出','濈然汗出','濈然','微微','汗出'时
           #,"寸脉浮、关脉小细沉紧，名曰脏结。舌上白苔滑者，难治",
        ]
        no_dict_expects=[
             ['397', '伤寒', '解后', '虚', '羸少气', '气逆欲', '吐', '竹叶', '石膏', '汤主', '之']
            ,['188', '伤寒', '转系', '阳明', '者', '其人', '濈', '然微', '汗', '出', '也']
            #'微汗'、'汗出'都是词，但同长，'微汗'在前的吃掉'汗'字，'汗出'就没了，先到先得
            #,['寸脉', '浮', '、', '关脉', '小细', '沉紧', '，', '名曰', '脏结', '。', '舌上', '白苔', '滑者', '，', '难治']
            ,['濈', '然微', '汗', '出', '濈', '然汗', '出', '濈', '然', '单列', '微汗', '出', '微微', '汗出']
        ]

        dict=["虚羸少气","竹叶石膏汤"
              ,'濈然微汗出','濈然汗出','濈然','微汗出','微微','微汗','汗出'
             #,'寸脉浮','关脉小细沉紧','舌上白苔滑'
        ]
        with_dict_expects=[#有了长词，短词不再切分
            ['397', '伤寒', '解后', '虚羸少气', '气逆欲', '吐', '竹叶石膏汤','主之']
            #长词“虚羸少气” 遮盖了短词“羸少气”
            #长词“竹叶石膏汤” 遮盖了短词“竹叶”、“石膏”
            ,['188', '伤寒', '转系', '阳明', '者', '其', '人', '濈然微汗出', '也']
            #‘其人’的切分奇怪
            #,['寸脉浮', '、', '关脉小细沉紧', '，', '名曰', '脏结', '。', '舌上白苔滑', '者', '，', '难治'],
            ,['濈然微汗出', '濈然汗出', '濈然', '单列', '微汗出', '微微', '汗出']
            #为何'濈然汗出'不被遮盖住？想象‘濈然’之后，后续字符已再无‘微汗出’只有’汗出‘，只能剩余之中取最长的。
            #为何’濈然‘不被遮盖住？想象‘濈然’之后，后续字符既无‘微汗出’，也无’汗出‘，构不成更长词，自身已是最长。
            #'微微汗出'→微微/汗出，为何不是 微/微汗出？解释如下：
            #jieba分词有2个阶段：
            #·阶段1（构建分词图=一个有向无环图）​​：​​绝对优先匹配'用户'词典中的最长词
            # 微微汗出的2个路径：路径1=微微/汗出，路径2=微/微汗出，
            # ‘用户’词典会强制阻断短词路径，在jieba发现‘微’字时，发现用户辞典有‘微微’
            # 所以优先选择‘微微’构建路径节点，路径2不会构建
            #·阶段2（路径选择）​​：在已构建的分词图中，选择概率乘积最大的路径。
            #（假设用户辞典的词频2000，否则默认辞典的词频10000
            # 如微微/汗出=20000*20000=4亿，微/微汗出=10000*20000=2亿。
            # 所以路径2不仅阶段1就被排除，即使进入阶段2，词频更低，也要落选
            # 默认词典中的长词不会像用户词典那样强制阻断短词路径，分词结果完全由阶段2 ​概率乘积最大化​​ 决定
        ]
        for expected,text in zip(no_dict_expects,texts):
            out=cutter.cut(text)
            self.assertEqual(expected,out)
        cutter.load_dict(dict,10000)
        for expected,text in zip(with_dict_expects,texts):
            out=cutter.cut(text)
            self.assertEqual(expected,out)
    
    def test_sigleton(self):
        extractor=WordCutter()
        extractor2=WordCutter()
        assert(extractor2 is extractor)
    
    def test_init_once(self):
        extractor=WordCutter()
        extractor2=WordCutter(True)#若未曾初始化，则实例属性_dict_loaded值False→True
        assert(extractor._dict_loaded==False)#实例属性值未变，所以说明没有再次调用__init__()
        assert(extractor2._dict_loaded==False)
        
 
if  __name__=="__main__":
    unittest.main()