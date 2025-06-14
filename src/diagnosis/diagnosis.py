import os,regex
from pathlib import Path
from collections import defaultdict
def find_project_root(file_abs_path:str, anchor_dir:str)->str:
    parts=[part for part in Path(file_abs_path).parts]
    uplevel=len(parts)-1-parts.index(anchor_dir)
    root_dir = Path(file_abs_path).resolve().parents[uplevel]
    return root_dir

PROJECT_ROOT= find_project_root(__file__,"src")

#BASE_DIR=os.path.dirname(os.path.abspath(__file__))+os.path+os.pardir
RESOURCE_DIR=f"{PROJECT_ROOT}/resources"
SHL_BOOK_FILE=f"{RESOURCE_DIR}/古籍/伤寒论_条文.md"
FANG_ZHENG_FILE=f"{RESOURCE_DIR}/方证对应.csv"
TERM_NORM_FILE=f"{RESOURCE_DIR}/近义词.csv"
FANG_NAME_FILE=f"{RESOURCE_DIR}/dict/方名_词典.txt"#方剂名，预先手工提取，比较精确
PULSE_TONGUE_DX_FILE=f"{RESOURCE_DIR}/dict/脉舌诊_词典.txt"#脉象、舌象，预先手工提取，比较精确

from pydantic import BaseModel
class FangSynd(BaseModel):
    fang:str
    syndromes:list[str]
    def __init__(self, fang:str, syndromes:list[str]):
        super().__init__(fang=fang,syndromes=syndromes)
        self.fang=fang
        self.syndromes=syndromes

class Clause(BaseModel):
    id:int
    clause:str#伤寒论条文原文
    def __init__(self, id:int, clause:str):
        super().__init__(id=id,clause=clause)
        self.id=id
        self.clause=clause

class ClauseNE(Clause):
    fang_synds:list[FangSynd]=[]
    score:float=0.0
    
    def __init__(self, id, clause:str,fang_synd:list[FangSynd]=[],score:float=0.0):
        super().__init__(id, clause)
        self.fang_synds=fang_synd
        self.score=score

class Diagnosis:

    _instance=None

    def __new__(cls):
        if cls._instance is None:
            cls._instance=super().__new__(cls)
            cls._instance._initialized=False
        return cls._instance
 
    def __init__(self):
        #self.clause_NEs=load_clause_NE()
        #关于证候权重的设想：
        #若：统计用桂枝汤处10次，'汗出'出现10次，'发热'5次，'恶寒'5次，'恶风'4次，
        #则：桂枝汤-汗出-发热-恶寒-恶风关联率=10:10:5:5:4
        # clause_NEs_json=[
        #     {"id":12,"clause":"12.太阳中风，阳浮而阴弱，阳浮者，热自发；阴弱者，汗自出。啬啬恶寒，淅淅恶风，翕翕发热，鼻鸣干呕者，桂枝汤主之。","fang_synds":[{"fang":"桂枝汤","syndromes":["阳浮","阴弱","啬啬恶寒","淅淅恶风","翕翕发热","鼻鸣","干呕"]}]},
        #     {"id":13,"clause":"13.太阳病，头痛、发热、汗出、恶风，桂枝汤主之。","fang_synds":[{"fang":"桂枝汤","syndromes":["发热","恶寒","汗出"]}]},
        #     {"id":35,"clause":"35.太阳病，头痛、发热、身疼、腰痛、骨节疼痛、恶风、无汗而喘者，麻黄汤主之。","fang_synds":[{"fang":"麻黄汤","syndromes":["太阳病","头痛","发热","身疼","腰痛","骨节疼痛","恶风","无汗","喘"]}]},
        #     {"id":42,"clause":"42.太阳病，外证未解，脉浮弱者，当以汗解，宜桂枝汤","fang_synds":[{"fang":"桂枝汤","syndromes":["太阳病","外证未解","脉浮弱"]}]}
        # ]

        #读入方证对应关系
        self.clause_NEs=self.load_fang_zheng_relation()

        # self.norm={#同义词，近义词
        #     "翕翕发热":"发热",
        #     "啬啬恶寒":"恶寒",
        #     "淅淅恶风":"恶风",
        #     "阳浮":"热自发",
        #     "阴弱":"汗自出",
        #     "热自发":"发热",
        #     "汗自出":"汗出",
        #     "脉浮弱":"脉浮缓"
        # }
        self.norm=self.load_synonyms()
        self.correlations=self.build_correlation()
    #加载证候近义词，方便归一化
    def load_synonyms(self):
        #norm:dict[str,str]={}
        import csv
        try:
            with open(TERM_NORM_FILE, "r", encoding="utf-8-sig") as f:
                reader=csv.reader(f,delimiter=',')
                norm={row[0].strip():row[1].strip() for row in reader if len(row[1].strip())>0}#键为空不影响，但值不为空
        except Exception as e:
            print(f"{e.__class__.__name__}:{e}")
        
        return norm

    def load_fang_zheng_relation(self)->list[ClauseNE]:
        clause_NEs: list[ClauseNE]=[]
        clauses=self.load_SHL_clauses()
        import csv
        try:
            with open(FANG_ZHENG_FILE, "r", encoding="utf-8-sig") as f:
                reader=csv.reader(f,delimiter=',')
                for row in reader:
                    id=int(row[0])
                    clause=clauses[id]
                    fang=row[1].strip()
                    synds=[synd.strip() for synd in row[2:]if len(synd.strip())>0]
                    fang_synd=FangSynd(fang,synds)
                    clauseNE=ClauseNE(id,clause, [fang_synd])
                    clause_NEs.append(clauseNE)
        except Exception as e:
            print(f"{e.__class__.__name__}:{e}")
        
        return clause_NEs
                    
    def load_SHL_clauses(self)->dict[int,str]:
        clauses:dict[int,str]=[]
        try:
            with open(SHL_BOOK_FILE, 'r',encoding='utf-8') as f:
                import regex as re
                pattern=re.compile(r'(^\d+).+')
                clauses={int(pattern.match(line).group(1)):line for line in f.readlines() if pattern.match(line)}#只取有编号开头的条文，会忽略注释行和空行
        except Exception as e:
            print(f"{e.__class__.__name__}:{e}")
        return clauses
    def load_fang_names(self)->list[str]:
        try:
            with open(FANG_NAME_FILE, 'r',encoding='utf-8') as f:
                import regex as re
                pattern=regex.compile(r'(^\d+)(.+)')
                lines=[line for line in f.readlines() if re.match(pattern,line)]#只取有编号的条文，会忽略注释行和空行
                clause=sorted(lines,key=lambda line:int(re.match(pattern,line).group(1)))
        except Exception as e:
            print(f"{e.__class__.__name__}:{e}")

    def load_clause_NE(self):
        import json
        clauseNEs=json.loads(self.clause_NEs)
        return clauseNEs

    # 证候归一化：
    # 1.同义词链转换（如 阳浮→热自发→发热→<不存在>）
    # 2.防止循环(防止['A':'B','B':'A'])
    # 3.无可转换返回自身（如 发热，返回 发热）
    # 
    def normalize_term(self,term):
        """高效递归标准化中医术语，带循环保护"""
        visited = set()
        current = term
        
        while True:
            # 如果已访问过此术语，直接返回（防止循环）
            if current in visited:
                return current
            
            # 添加当前术语到访问记录
            visited.add(current)
            
            # 如果当前术语不可标准化，返回
            if current not in self.norm:#功能等同norm.keys()，但效率更高
                return current
            
            # 否则继续标准化
            current = self.norm[current]
        
    #相关性统计
    def build_correlation(self):
        """
        
        """
    #    from collections import defaultdict
        correlations=defaultdict(lambda:defaultdict(int))
        #为了归一化，因为，如果某个方剂-证候出现次数多，他的相关性数值就越大，代表此证候的权重越大，这不合理,举例：
        # [{"fang":"桂枝汤",fang_synd{"发热"}} #重复10次
        # {"fang":"麻黄汤",fang_synd{"发热"，"头痛","身痛"} 仅此1次]
        #则相关性数值统计为：
        # {{"桂枝汤":{"发热":10}}，{"麻黄汤":{"发热":1,"头痛":1,"身痛":1}}，若证候是{"发热","头痛"，"身痛"}，
        # 则相关性求和：桂枝汤=发热(10)+头痛(0)+身痛(0)=10，麻黄汤=发热(1)+头痛(1)+身痛(1)=3，
        # 符合麻黄汤证候更多，却不推荐，这明显不合理，原因就是桂枝汤的证候重复次数太高，导致相关性虚高。所以要除以总数以归一化：
        # 归一化后是：{{"桂枝汤":{"发热":10/10=1}}，{"麻黄汤":{"发热":1,"头痛":1,"身痛":1}}再匹配证候{"发热","头痛"，"身痛"}
        # 则桂枝汤=发热(1)+头痛(0)+身痛(0)=1，麻黄汤=发热(1)+头痛(1)+身痛(1)=3，自然推荐麻黄汤
        # 还有不合理之处：特异性证候被意外平均了？
        # 有没有比平均更合理之法？如TF-IDF？
        
        fang_count=defaultdict(int)
        for entry in self.clause_NEs:
            for fang_synd in entry.fang_synds:
                fang=fang_synd.fang
                fang_count[fang]+=1
                syndromes=fang_synd.syndromes
                for synd in syndromes:
                    correlations[fang][self.normalize_term(synd)]+=1
        for fang in correlations.keys():
            for synd in correlations[fang]:
                correlations[fang][synd] /= fang_count[fang]

        return correlations

    # def identify_pattern(self,syndromes:set[str])->ClauseNE:
    #     scores=defaultdict(float)
    #     for fang,synd_weights in self.correlations.items():
    #         overlap=syndromes & set(synd_weights.keys())
    #         scores[fang]=sum(synd_weights[s] for s in overlap)
    #     sorted_scores=sorted(scores.items(),key=lambda x: x[1],reverse=True)
    #     recommend=ClauseNE()#TODO 获得《伤寒论》条文内容
    #     #recommend.fang_synd={scores.}
    #     return recommend

    #遍历全部条文，逐个计算，然后排序，全程不会丢失 条文-方剂 对应关系
    def recommend_fang(self,syndromes:set[str])->list[ClauseNE]:
        recommends:list[ClauseNE]=[]
        scores=defaultdict(float)
        norm_input_synds={self.normalize_term(s) for s in syndromes}
        for entry in self.clause_NEs:
            id=entry.id
            clause=entry.clause
            for fang_synd in entry.fang_synds:
                norm_fang_synds={self.normalize_term(s)for s in fang_synd.syndromes}
                overlap=norm_input_synds & norm_fang_synds
                score=sum(self.correlations[fang_synd.fang][s] for s in overlap)
                recommends.append(ClauseNE(id, clause,entry.fang_synds,score))
        sorted_recommends=sorted(recommends,key=lambda x: x.score,reverse=True)
        # import json
        # return json.dumps(recommends[0:3])#返回前3个
        return recommends[0:3]

# if __name__=="__main__":
#     import argparse
#     parse=argparse.ArgumentParser(description='推荐方剂，并给出推荐依据')
#     parse.add_argument('-synds','--syndromes')#-l/--lines可选参数（前缀-），行数（默认 10，须为整数）
#     args=parse.parse_args() #按照add_argument()给的参数结构，
#                             #解析命令行参数（=sys.argv=lanch.json文件的args项的值）
#     print(args)

#     identify_pattern(set(args[1:]))