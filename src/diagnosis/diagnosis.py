from cmath import log
import csv
from decimal import *
from enum import Enum, auto
from math import sqrt
import os,regex
from pathlib import Path
from collections import defaultdict
import numpy as np
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
    syndromes:dict[str,Decimal]#证：证的权重，用Decimal，不用float，防止二进制表示会丢失精度，不利于比较

class ClauseFangSynd(BaseModel):
    clause_id:int#伤寒论条文编号
#    clause:str#伤寒论条文原文,引用self.clauses
    fang_synds:list[FangSynd]=[]

    # def __init__(self, clause_id, fang_synds:list[FangSynd]=[]):
    #     super().__init__(clause_id=clause_id, fang_synds=fang_synds)
    #     self.clause_id=clause_id
    #     self.fang_synds=fang_synds

class Recommend(BaseModel):
    clause_id:int
    clause:str#伤寒论条文原文
    fang_synd:FangSynd
    match_score:float=0.0
    # def __init__(self, clause_id:int, clause:str,fang_synd:FangSynd,score:float=0.0):
    #     super().__init__(clause_id=clause_id, clause=clause,fang_synd=fang_synd,match_score=score)
    #     self.clause_id=clause_id
    #     self.clause=clause
    #     self.fang_synd=fang_synd
    #     self.match_score=score

class Correl(Enum):
    AVG=auto()
    TF_IDF_1=auto()
    TF_IDF_2=auto()
    BM25=auto()
class Diagnosis:

    _instance=None

    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance=super().__new__(cls)
    #         cls._instance._initialized=False
    #     return cls._instance
 
    def __init__(self,norm:dict[str,str]=None,clause_fang_synds:list[ClauseFangSynd]=None, correl:Correl=Correl.AVG):
        # if self._initialized==True:
        #     return
        if hasattr(self,"norm") and self.norm==norm\
              and hasattr(self,"clause_fang_synds") and self.clause_fang_synds==clause_fang_synds:
            return
        #读入同义词
        self.norm=norm
        if not self.norm:
            self.norm=self.load_synonyms()
        #读入方证对应关系
        self.clause_fang_synds=clause_fang_synds
        if not self.clause_fang_synds:
            self.clause_fang_synds=self.load_fang_zheng_relation()
        #self.synd_set=self.consolidate_term()
        if correl==Correl.AVG:
            self.build_correlation_avg()
        elif correl==Correl.TF_IDF_1:
            self.build_correlation_tf_idf_1()
        elif correl==Correl.TF_IDF_2:
            self.build_correlation_tf_idf_2()
        else:
            self.build_correlation_BM25()
        self._initialized=True

    def load_fang_zheng_relation(self)->list[ClauseFangSynd]:
        clause_fang_synds: list[ClauseFangSynd]=[]
        if not hasattr(self,"clauses"):
            clauses=self.load_SHL_clauses()
            self.clauses=clauses

        try:
            temp_dict=defaultdict[int,list[FangSynd]](list)
            with open(FANG_ZHENG_FILE, "r", encoding="utf-8") as f:
                reader=csv.reader(f,delimiter=',')
                for row in reader:
                    if len(row)<3 or not row[0].strip() or not row[1].strip() or all(cell.strip=='' for cell in row[2:]):#至少包括id,fang,至少一个证候
                        continue
                    id=int(row[0])
                    clause=clauses[id]
                    fang=row[1].strip()
                    synds={synd.strip():Decimal() for synd in row[2:]if synd.strip()}
                    fang_synd=FangSynd(fang=fang,syndromes=synds)
                    temp_dict[id].append(fang_synd)
            clause_fang_synds=[ClauseFangSynd(clause_id=id,fang_synds=v) for id,v in temp_dict.items()]
        except Exception as e:
            print(f"{e.__class__.__name__}:{e}")
        
        return clause_fang_synds
                    
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

    #加载证候近义词，方便归一化
    def load_synonyms(self):
        norm:dict[str,str]={}
        try:
            with open(TERM_NORM_FILE, "r", encoding="utf-8") as f:
                reader=csv.reader(f,delimiter=',')
                norm={row[0].strip():row[1].strip() for row in reader if len(row)>=2 and row[1].strip() and not row[0].strip().startswith('#')}#键为空不影响，但值不为空
        except Exception as e:
            print(f"{e.__class__.__name__}:{e}")
        
        return norm

    # 证候归一化：
    # 1.同义词链转换（如 阳浮→热自发→发热→<不存在>）
    # 2.防止循环(防止['A':'B','B':'A'])
    # 3.无可转换返回自身（如 发热，返回 发热）
    # 
    def normalize_term(self,term,norm:dict[str,str]=None):
        """高效递归标准化中医术语，带循环保护"""
        if not norm and not self.norm:
            self.norm=self.load_synonyms()
            norm=self.norm
        
        visited = set()
        current = term
        
        while True:
            # 如果已访问过此术语，直接返回（防止循环）
            if current in visited:
                return current
            
            # 添加当前术语到访问记录
            visited.add(current)
            
            # 如果当前术语不可标准化，返回
            if current not in norm:#功能等同norm.keys()，但效率更高
                return current
            
            # 否则继续标准化
            current = norm[current]

    def consolidate_term(self,includeNorm=True,includeFang=True)->set[str]:
        term_dict:set[str]=set()
        for entry in self.clause_fang_synds:
            for fang_synd in entry.fang_synds:
                term_dict.update(fang_synd.syndromes.keys())
        if includeNorm and self.norm!=None:
            term_dict.update(self.norm.keys())
            term_dict.update(self.norm.values())
        if includeFang:
            term_dict.add(fang_synd.fang for entry in self.clause_fang_synds for fang_synd in entry.fang_synds )
        return term_dict

    def build_correlation_tf_idf_1(self):
        """
        算法思路：证候=词语,方剂=文档，而且同名的方剂的所有证候都算在一个文档里。
        TF(Term Frequency)-词频
        TF(s, f) = (证候 s 在方剂 f 中出现的次数) / (方剂 f 中所有证候的总数)
        IDF (Inverse Document Frequency) - 逆文档频率
        IDF(s, F) = log(方剂集合 F 中的总方剂数 / 包含证候 s 的方剂数))
        """
         
        #TF的分子=证候 s 在方剂 f 中出现的次数        
        fang_one_synd_count=defaultdict(lambda:defaultdict(int))
        for entry in self.clause_fang_synds:
            for fang_synd in entry.fang_synds:
                fang=fang_synd.fang
                syndromes=fang_synd.syndromes
                for synd in syndromes:
                    fang_one_synd_count[fang][self.normalize_term(synd,self.norm)]+=1
       
        #TF的分母=方剂 f 中所有证候的总数
        fang_all_synd_sum=defaultdict(int)
        for fang in fang_one_synd_count:
            #fang_all_synd_count[fang]=len(co_occurs[fang].keys())#按证候种类计数，错
            #应该按证候词语出现次数总数计数，否则若某个词语出现次数很多次，而按种类只计数1次，则导致此词语TF>1，不符合归一化的初衷。
            fang_all_synd_sum[fang]=sum(fang_one_synd_count[fang][s] for s in fang_one_synd_count[fang])

        #TF(s, f) = (证候 s 在方剂 f 中出现的次数) / (方剂 f 中所有证候的总数)
        tf=defaultdict(lambda:defaultdict(Decimal))
        for fang in fang_one_synd_count:
            for synd in fang_one_synd_count[fang]:
                #避免因二进制浮点数无法精确表示十进制数量而可能出现的问题，使用Decimal,方便相等性测试
                tf[fang][synd]=Decimal(fang_one_synd_count[fang][synd])/Decimal(fang_all_synd_sum[fang])

        #idf的分子=方剂集合 F 中的总方剂数
        fang_count=len(fang_one_synd_count.keys())

        #IDF的分母=包含证候 s 的方剂数
        #synd_fang=defaultdict(list)#若证候被同一方剂包含多次，只算一次,故不用list
        synd_fang=defaultdict(set)#用set
        for fang in fang_one_synd_count:
            for synd in fang_one_synd_count[fang]:
                synd_fang[synd].add(fang)
        
        idf=defaultdict(lambda:defaultdict(Decimal))
        for synd in synd_fang:
            #idf[synd]=Decimal(log(Decimal(len(synd_fang[synd]))/Decimal(fang_count),10))#log()返回float，精度有缺失
            idf[synd]=(Decimal(fang_count)/Decimal(len(synd_fang[synd]))).log10()#保持精度不缺失
        
        correlations=defaultdict(lambda:defaultdict(Decimal))
        for fang in fang_one_synd_count:
            for synd in fang_one_synd_count[fang]:
                #Decimal + 四舍五入 保留精度，方便以后相等性测试
                correlations[fang][synd]=(tf[fang][synd]*idf[synd]).quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
            
        #更新到原始数据
        for entry in self.clause_fang_synds:
            for fang_synd in entry.fang_synds:
                fang=fang_synd.fang
                for synd in fang_synd.syndromes:
                    norm_synd=self.normalize_term(synd,self.norm)
                    fang_synd.syndromes[synd]=correlations[fang][norm_synd]

        #return correlations

    #转成字典，#key的格式="条文编号-方名-防同名方剂后缀（因为同一条文可能多次使用同一方剂，故方名后加数字后缀）
    # def _convert_data(self,clause_fang_synds:list[ClauseFangSynd])->dict[str,dict[str,Decimal]]:
    #     clause_fang_synd_dict=defaultdict(lambda:defaultdict(Decimal))
    #     for entry in clause_fang_synds:
    #         for index, fang_synd in enumerate(entry.fang_synds):
    #             new_key=f"{entry.clause_id}-{fang_synd.fang}-{index}"
    #             clause_fang_synd_dict[new_key]={s:Decimal(0.0) for s in fang_synd.syndromes}
    #     return clause_fang_synd_dict
    def build_correlation_tf_idf_2(self):
        """
        算法思路：证候=词语,方剂=文档，某个条文里的方剂（后简称条文方剂）算一个文档，即使该方剂名重复出现，
        因为一个条文方剂的所有证候是集合，一般不会重复，故TF总是相同，故不再有意义
        好处是：推荐更匹配条文方剂，而不是仅仅是方剂
        TF(Term Frequency)-词频
        TF(s, f) = (证候 s 在方剂 d 中出现的次数) / (方剂 f 中所有证候的总数)
        IDF (Inverse Document Frequency) - 逆文档频率
        IDF(s, F) = log(方剂集合 F 中的总方剂数 / 包含证候 s 的方剂数))
        """
        
        #转成字典，#key的格式="条文编号-方名-防同名方剂后缀（因为同一条文可能多次使用同一方剂，故方名后加数字后缀）
        #TF的分子=证候 s 在方剂 f 中出现的次数=永远为1
        #TF的分母=条文方剂 c_f 中所有证候的总数
        clause_fang_synd_dict=defaultdict(lambda:defaultdict(Decimal))
        for entry in self.clause_fang_synds:
            for index, fang_synd in enumerate(entry.fang_synds):
                new_fang_key=f"{entry.clause_id}-{fang_synd.fang}-{index}"
                clause_fang_synd_dict[new_fang_key]={self.normalize_term(s,self.norm):Decimal() for s in fang_synd.syndromes}

        #TF(s, f) = (证候 s 在方剂 f 中出现的次数) / (方剂 f 中所有证候的总数)
        tf=defaultdict(lambda:defaultdict(Decimal))
        for fang in clause_fang_synd_dict:
            for synd in clause_fang_synd_dict[fang]:
                #避免因二进制浮点数无法精确表示十进制数量而可能出现的问题，使用Decimal,方便相等性测试
                tf[fang][synd]=Decimal(1)/Decimal(len(clause_fang_synd_dict[fang].keys()))#一个条方的证候不会重复，故总是1
        #IDF的分子=方剂集合 F 中的总"条文方剂"数
        fang_count=len(clause_fang_synd_dict.keys())

        #IDF的分母=包含证候 s 的方剂数
        #synd_fang=defaultdict(set)#同一方剂多次包含算多次,故不用set
        synd_fang=defaultdict(list)#因为新方名带claus_id和列表索引，不重复，故set list都可以
        for fang, synds in clause_fang_synd_dict.items():
            for synd in synds:
                synd_fang[self.normalize_term(synd,self.norm)].append(fang)
        
        idf=defaultdict(lambda:defaultdict(Decimal))
        for synd in synd_fang:
            #idf[synd]=Decimal(log(Decimal(len(synd_fang[synd]))/Decimal(fang_count),10))#精度有缺失
            idf[synd]=(Decimal(fang_count)/Decimal(len(synd_fang[synd]))).log10()#精度一直不缺失

                
        #correlations=defaultdict(lambda:defaultdict(Decimal))
        for fang in clause_fang_synd_dict:
            for synd in clause_fang_synd_dict[fang]:
                #Decimal + 四舍五入 保留精度，方便以后相等性测试
                clause_fang_synd_dict[fang][synd]=(tf[fang][synd]*idf[synd]).quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
        
        #更新到原始数据
        for entry in self.clause_fang_synds:
            for index,fang_synd in enumerate(entry.fang_synds):
                new_fang_key=f"{entry.clause_id}-{fang_synd.fang}-{index}"
                for synd in fang_synd.syndromes:
                    norm_synd=self.normalize_term(synd,self.norm)
                    fang_synd.syndromes[synd]=clause_fang_synd_dict[new_fang_key][norm_synd]

    def build_correlation_BM25(self):
        """
        算法思路：证候=词语,方剂=文档，某个条文里的方剂（后简称条文方剂）算一个文档，即使该方剂名重复出现。
        这一点同tf-idf2，但改进之处有2点：
        1.会统计证候在条文方剂中的次数（通常为1），但不再除以条文方剂中所有证候的总数，这个归一化包含在第2点改进中
        2.匹配分数不再是权重求和，而是计算证候权重向量和查询证候向量的余弦相似度，好处：
          2.1 因为余弦取值范围在[-1,1]（本算法实际只会在[0,1])所以天然归一化。
          2.2结果更倾向于完全匹配的条文方剂，举例：
          查询证候：v_query={A,B]
          条文方剂1：{A:0.4,B:0.4, C:0.4,D:0.4}→ 
          sum=0.4*1+0.4*1+0.4*0+0.4*0=0.8,
          cos=sum/sqrt(0.4^2+0.4^2+0.4^2+0.4^2)*sqrt(1*1+1*1)=0.71
          条文方剂2：{A:0.3,B:0.3}→ 
          sum=0.3*1+0.3*1=0.6,
          cos=sum/sqrt(0.3^2+0.3^2)*sqrt(1*1+1*1)=1.00
          按权重求和，当选条文方剂1，按余弦相似度当选条文方剂2。但条文方剂2是完全匹配，所以更应选中，所以余弦相似度更合理
        TC(Term Count)-词次数
        TC(s, f) = (证候 s 在方剂 d 中出现的次数)（注意不再 除以 (方剂 f 中所有证候的总数))
        IDF (Inverse Document Frequency) - 逆文档频率
        IDF(s, F) = log(方剂集合 F 中的总方剂数 / 包含证候 s 的方剂数))
        """
        
        #转成字典，#key的格式="条文编号-方名-防同名方剂后缀（因为同一条文可能多次使用同一方剂，故方名后加数字后缀）
        #TF的分子=证候 s 在方剂 f 中出现的次数=一般为1
        #TF的分母=条文方剂 c_f 中所有证候的总数
        clause_fang_synd_dict=defaultdict(lambda:defaultdict(Decimal))
        for entry in self.clause_fang_synds:
            for index, fang_synd in enumerate(entry.fang_synds):
                new_fang_key=f"{entry.clause_id}-{fang_synd.fang}-{index}"
                clause_fang_synd_dict[new_fang_key]={self.normalize_term(s,self.norm):Decimal() for s in fang_synd.syndromes}

        #TF(s, f) = (证候 s 在方剂 f 中出现的次数) / (方剂 f 中所有证候的总数)
        tf=defaultdict(lambda:defaultdict(Decimal))
        for fang in clause_fang_synd_dict:
            for synd in clause_fang_synd_dict[fang]:
                #避免因二进制浮点数无法精确表示十进制数量而可能出现的问题，使用Decimal,方便相等性测试
                #tf[fang][synd]=Decimal(1)/Decimal(len(clause_fang_synd_dict[fang].keys()))#一个条方的证候不会重复，故总是1
                tf[fang][synd]=Decimal(1)#不再/ (方剂 f 中所有证候的总数)
                #一个条方的证候不会重复，故目前是1，以后会修改：1. 调整词频饱和度，2.减低文档长度的影响
        
        # IDF的分子=方剂集合 F 中的总"条文方剂"数
        fang_count=len(clause_fang_synd_dict.keys())

        #IDF的分母=包含证候 s 的方剂数
        #synd_fang=defaultdict(set)#同一方剂多次包含算多次,故不用set
        synd_fang=defaultdict(list)#因为新方名带claus_id和列表索引，不重复，故set list都可以
        for fang, synds in clause_fang_synd_dict.items():
            for synd in synds:
                synd_fang[self.normalize_term(synd,self.norm)].append(fang)
        
        idf=defaultdict(lambda:defaultdict(Decimal))
        for synd in synd_fang:
            #idf[synd]=Decimal(log(Decimal(len(synd_fang[synd]))/Decimal(fang_count),10))#精度有缺失
            idf[synd]=(Decimal(fang_count)/Decimal(len(synd_fang[synd]))).log10()#精度一直不缺失

        #correlations=defaultdict(lambda:defaultdict(Decimal))
        for fang in clause_fang_synd_dict:
            for synd in clause_fang_synd_dict[fang]:
                #Decimal + 四舍五入 保留精度，方便以后相等性测试
                clause_fang_synd_dict[fang][synd]=(tf[fang][synd]*idf[synd]).quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
        
        #更新到原始数据
        for entry in self.clause_fang_synds:
            for index,fang_synd in enumerate(entry.fang_synds):
                new_fang_key=f"{entry.clause_id}-{fang_synd.fang}-{index}"
                for synd in fang_synd.syndromes:
                    norm_synd=self.normalize_term(synd,self.norm)
                    fang_synd.syndromes[synd]=clause_fang_synd_dict[new_fang_key][norm_synd]

    #平均发相关性统计
    def build_correlation_avg(self):
    #    from collections import defaultdict
        #co_occurs=self.fang_synd_count(self.clause_fang_synds,self.norm)
        co_occurs=defaultdict(lambda:defaultdict(int))
        for entry in self.clause_fang_synds:
            for fang_synd in entry.fang_synds:
                fang=fang_synd.fang
                syndromes=fang_synd.syndromes
                for synd in syndromes:
                    co_occurs[fang][self.normalize_term(synd,self.norm)]+=1

        #为了归一化，因为，如果某个方剂-证候共现次数多，他的相关性数值就越大，代表此证候的权重越大，这不合理,举例：
        # [
        #   {"fang":"桂枝汤",fang_synd{"发热"}} #重复10次
        #   {"fang":"麻黄汤",fang_synd{"发热"，"头痛","身痛"} 仅此1次
        #]
        #则相关性数值统计为：
        # {{"桂枝汤":{"发热":10}}，{"麻黄汤":{"发热":1,"头痛":1,"身痛":1}}，若证候是{"发热","头痛"，"身痛"}，
        # 则相关性求和：桂枝汤=发热(10)+头痛(0)+身痛(0)=10，麻黄汤=发热(1)+头痛(1)+身痛(1)=3，
        # 符合麻黄汤证候更多，却不推荐，这明显不合理，原因就是桂枝汤的证候重复次数太高，导致相关性虚高。所以要除以总数以归一化：
        # 归一化后是：{{"桂枝汤":{"发热":10/10=1}}，{"麻黄汤":{"发热":1,"头痛":1,"身痛":1}}再匹配证候{"发热","头痛"，"身痛"}
        # 则桂枝汤=发热(1)+头痛(0)+身痛(0)=1，麻黄汤=发热(1)+头痛(1)+身痛(1)=3，自然推荐麻黄汤
        # 还有不合理之处：特异性证候被意外平均了？
        # 有没有比平均更合理之法？如TF-IDF？
        
        fang_count=defaultdict(int)
        for entry in self.clause_fang_synds:
            for fang_synd in entry.fang_synds:
                fang=fang_synd.fang
                fang_count[fang]+=1
 
        for fang in co_occurs:
            #fang_count[fang]=sum(co_occurs[fang][synd] for synd in co_occurs)
            for synd in co_occurs[fang]: 
                #co_occurs[fang][synd] /=fang_count[fang]#不利于相等性测试
                co_occurs[fang][synd] =(Decimal(co_occurs[fang][synd])/Decimal(fang_count[fang]))\
                    .quantize(Decimal('0.00'),rounding=ROUND_HALF_UP)

        #更新到原始数据
        for entry in self.clause_fang_synds:
            for fang_synd in entry.fang_synds:
                fang=fang_synd.fang
                for synd in fang_synd.syndromes:
                    norm_synd=self.normalize_term(synd,self.norm)
                    fang_synd.syndromes[synd]=co_occurs[fang][norm_synd]


     #遍历全部条文，逐个计算，然后排序，全程不会丢失 条文-方剂 对应关系
    def recommend_fang(self,query_synds:set[str])->list[Recommend]:
        recommends:list[Recommend]=[]
        if not hasattr(self,"clauses"):
            self.clauses=self.load_SHL_clauses()
        
        query={self.normalize_term(s,self.norm):1 for s in query_synds}
        for entry in self.clause_fang_synds:
            id=entry.clause_id
            clause=self.clauses[id]
            score=Decimal(0)
            for fang_synd in entry.fang_synds:
                clause_fang={self.normalize_term(s,self.norm):\
                                fang_synd.syndromes[s] for s in fang_synd.syndromes}
                dot=sum(query.get(s,0)*clause_fang.get(s,0) for s in query)
                query_norm=Decimal(sum(val**2 for val in query.values())).sqrt()
                clause_fang_norm=Decimal(sum(v**2 for v in clause_fang.values())).sqrt()
                score=dot/query_norm/clause_fang_norm
                recommends.append(Recommend(clause_id=id, clause=clause,fang_synd=fang_synd,match_score=score))#一条文多方剂列表会被拆成多条单方剂
            
            # for synd in fang_synd.syndromes:
            #         norm_synd=self.normalize_term(synd,self.norm)
            #         if norm_synd in norm_query_synds:
            #             score +=fang_synd.syndromes[synd]
        sorted_recommends=sorted(recommends,key=lambda x: x.match_score,reverse=True)
        return sorted_recommends

# if __name__=="__main__":
#     import argparse
#     parse=argparse.ArgumentParser(description='推荐方剂，并给出推荐依据')
#     parse.add_argument('-synds','--syndromes')#-l/--lines可选参数（前缀-），行数（默认 10，须为整数）
#     args=parse.parse_args() #按照add_argument()给的参数结构，
#                             #解析命令行参数（=sys.argv=lanch.json文件的args项的值）
#     print(args)

#     identify_pattern(set(args[1:]))