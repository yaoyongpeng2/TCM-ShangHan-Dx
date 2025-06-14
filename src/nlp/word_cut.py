import os
import jieba

BASE_DIR=os.getcwd()
RESOURCE_DIR=os.path.dirname(os.path.abspath(__file__))+os.sep+os.pardir+'/resources/dict'
FANG_NAME_FILE=f"{RESOURCE_DIR}/方名_词典.txt"#方剂名，预先手工提取，比较精确
PULSE_TONGUE_DX_FILE=f"{RESOURCE_DIR}/脉舌诊_词典.txt"#脉象、舌象，预先手工提取，比较精确
#USELESS_SEG_FILE=f"{RESOURCE_DIR}/分词_边角料.txt"
#分词技术会产生一些无价值的分词，如 "桂枝汤主之"→桂枝汤+主+之，'主'和'之'，都不是证候，是边角料，当去掉
SYND_NAME_ITER=f"{BASE_DIR}/iter/证候名_迭代.txt"

class WordCutter:

    _instance=None
 

    def __new__(cls):
        if cls._instance is None:
            cls._instance=super().__new__(cls)
            cls._instance._initialized=False
        return cls._instance
        

    def __init__(self):
        if self._initialized==True:
            return
#        import jieba3
#        self.cutter=jieba3.jieba3(cut_all=False,use_hmm=True)
        self._initialized=True

    def load_dicts(self):
        with open(FANG_NAME_FILE, "r", encoding="utf-8") as f:
            lines=[line.strip() for line in f.readlines() if len(line.strip())>0]
            self.load_dict(lines)
        with open(PULSE_TONGUE_DX_FILE, "r", encoding="utf-8") as f:
            lines=[line.strip() for line in f.readlines() if len(line.strip())>0]
            self.load_dict(lines)
        self._dict_loaded=True
    def load_dict(self,termdict=None,dict_feq=10000):
         for term in termdict:
            jieba.add_word(term, dict_feq)

    def __repr__(self):
        return repr(f"{self.termdict}.{self.dict_feq}")

    def cut(self,text,ignorePunct=True)->list[str]:
        #import jieba3
        #tokens_query=cutter.cut_query(text)
        
        #不用cut_query(),它会对长词再次切分，适合搜索，如"桂枝汤"→"桂枝汤"+"桂枝"
        #而cut_text()会最精确地切开，适合文档分析，"桂枝汤"作为一个已经收入词典的词，
        #在切分时，只会优先切出长词"桂枝汤"，不会再细切分出"桂枝"这个短词。
        if ignorePunct:
            import regex
            # puncts=regex.escape("，。、；：‘’“”？！（）【】{}"+",.:'\"?!()[]{}")
            # puncts=r"，。、；：‘’“”？！（）【】{}"+",.:'\"?!()[\]{}"#值：'，。、；：‘’“”？！（）【】{},.:\'"?!()[\\]{}'
            # text=regex.sub(f"[{puncts}]", " ", text)
            text=regex.sub(r"\p{P}", " ", text)#更简洁，但需要regex，re不行
        import jieba
        tokens=jieba.cut(text)#cut_all=False
        tokens= [token.strip() for token in tokens if len(token.strip())>0]#列表生成式，去掉空串
        return tokens
