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
class FangPatn(BaseModel):
    fang:str
    patterns:dict[str,Decimal]#证：证的权重，用Decimal，不用float，防止二进制表示会丢失精度，不利于比较

class ClauseFangPatn(BaseModel):
    clause_id:int#伤寒论条文编号
#    clause:str#伤寒论条文原文,引用self.clauses
    clause_seg_id:int=0#见注释如下：
    #一条文可能有宜有禁，如条文15，[(15,禁-桂枝汤,[证候群1,气不上冲]),(15,桂枝汤,[证候群1,气上冲])]
    # 一条文可能有多个方或误用或禁用，如N条文29:
    # [(29,误-桂枝汤,[证候群1])),(29,甘草干姜汤,[证候群2])，(29,芍药甘草汤,[证候群3]),
    #  (29,调胃承气汤,[证候群5]),(29,四逆汤,[证候群6])]
    # 条文id相同的再算出一个段落编号（从0开始，如条文15有段落编号{0,1}，条文29有段落编号{0,1,2,3,4}
    fang_patn:FangPatn
    # fang:str
    # patterns:dict[str,Decimal]#证：证的权重，用Decimal，不用float，防止二进制表示会丢失精度，不利于比较

    # def __init__(self, clause_id, fang_patns:list[FangPatn]=[]):
    #     super().__init__(clause_id=clause_id, fang_patns=fang_patns)
    #     self.clause_id=clause_id
    #     self.fang_patns=fang_patns

class Recommend(BaseModel):
    #clause_id:int
    clause_fang_patn:ClauseFangPatn
    clause_text:str#伤寒论条文原文
    #fang_patn:FangPatn
    
    match_score:float=0.0
    # def __init__(self, clause_id:int, clause:str,fang_patn:FangPatn,score:float=0.0):
    #     super().__init__(clause_id=clause_id, clause=clause,fang_patn=fang_patn,match_score=score)
    #     self.clause_id=clause_id
    #     self.clause=clause
    #     self.fang_patn=fang_patn
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
 
    def __init__(self,norm:dict[str,str]=None,clause_fang_patns:list[ClauseFangPatn]=None, correl:Correl=Correl.AVG):
        # if self._initialized==True:
        #     return
        if hasattr(self,"norm") and self.norm==norm\
              and hasattr(self,"clause_fang_patns") and self.clause_fang_patns==clause_fang_patns:
            return
        #读入同义词
        self.norm=norm
        if not self.norm:
            self.norm=self.load_synonyms()
        #读入方证对应关系
        self.clause_fang_patns=clause_fang_patns
        if not self.clause_fang_patns:
            self.clause_fang_patns=self.load_clause_fang_patn_from_file()
        #self.patn_set=self.consolidate_term()
        if correl==Correl.AVG:
            self.build_correlation_avg()
        elif correl==Correl.TF_IDF_1:
            self.build_correlation_tf_idf_1()
        elif correl==Correl.TF_IDF_2:
            self.build_correlation_tf_idf_2()
        else:
            self.build_correlation_BM25()
        self._initialized=True

    def load_clause_fang_patn_from_file(self)->list[ClauseFangPatn]:
        clause_fang_patns: list[ClauseFangPatn]=[]
        if not hasattr(self,"clauses"):
            clauses=self.load_SHL_clauses()
            self.clauses=clauses

        try:
            #temp_dict=defaultdict[int,list[FangPatn]](list)
            seg_count=defaultdict(int)
            with open(FANG_ZHENG_FILE, "r", encoding="utf-8") as f:
                reader=csv.reader(f,delimiter=',')
                for row in reader:
                    if len(row)<3 or not row[0].strip() or row[0].strip().startswith('#') or not row[1].strip() or all(cell.strip=='' for cell in row[2:]):#至少包括id,fang,至少一个证候
                        continue
                    id=int(row[0])
                    seg_count[id]+=1
                    clause=clauses[id]
                    fang=row[1].strip()
                    patns={p.strip():Decimal() for p in row[2:]if p.strip()}
                    fang_patn=FangPatn(fang=fang,patterns=patns)
                    #temp_dict[id].append(fang_patn)
                    clause_fang_patns.append(ClauseFangPatn(clause_id=id,clause_seg_id=seg_count[id]-1,fang_patn=fang_patn))
            #clause_fang_patns=[ClauseFangPatn(clause_id=id,fang_patns=v) for id,v in temp_dict.items()]
        except Exception as e:
#            print(f"{e.__class__.__name__}:{e}")
            print(repr(e))
            raise#向外层再次抛出
        
        return clause_fang_patns
                    
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
        for entry in self.clause_fang_patns:
            for fang_patn in entry.fang_patns:
                term_dict.update(fang_patn.patterns.keys())
        if includeNorm and self.norm!=None:
            term_dict.update(self.norm.keys())
            term_dict.update(self.norm.values())
        if includeFang:
            term_dict.add(fang_patn.fang for entry in self.clause_fang_patns for fang_patn in entry.fang_patns )
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
        fang_patn_count=defaultdict(lambda:defaultdict(int))
        for entry in self.clause_fang_patns:
            for patn in entry.fang_patn.patterns:
                fang_patn_count[entry.fang_patn.fang][self.normalize_term(patn,self.norm)]+=1
       
        #TF的分母=方剂 f 中所有证候的总数
        fang_all_patn_sum=defaultdict(int)
        for fang in fang_patn_count:
            #fang_all_patn_count[fang]=len(co_occurs[fang].keys())#按证候种类计数，错
            #应该按证候词语出现次数总数计数，否则若某个词语出现次数很多次，而按种类只计数1次，则导致此词语TF>1，不符合归一化的初衷。
            fang_all_patn_sum[fang]=sum(fang_patn_count[fang][s] for s in fang_patn_count[fang])

        #TF(s, f) = (证候 s 在方剂 f 中出现的次数) / (方剂 f 中所有证候的总数)
        tf=defaultdict(lambda:defaultdict(Decimal))
        for fang in fang_patn_count:
            for patn in fang_patn_count[fang]:
                #避免因二进制浮点数无法精确表示十进制数量而可能出现的问题，使用Decimal,方便相等性测试
                tf[fang][patn]=Decimal(fang_patn_count[fang][patn])/Decimal(fang_all_patn_sum[fang])

        #idf的分子=方剂集合 F 中的总方剂数
        fang_count=len(fang_patn_count.keys())

        #IDF的分母=包含证候 s 的方剂数
        #patn_fang=defaultdict(list)#若证候被同一方剂包含多次，只算一次,故不用list
        patn_fang=defaultdict(set)#用set
        for fang in fang_patn_count:
            for patn in fang_patn_count[fang]:
                patn_fang[patn].add(fang)
        
        idf=defaultdict(lambda:defaultdict(Decimal))
        for patn in patn_fang:
            #idf[patn]=Decimal(log(Decimal(len(patn_fang[patn]))/Decimal(fang_count),10))#log()返回float，精度有缺失
            idf[patn]=(Decimal(fang_count)/Decimal(len(patn_fang[patn]))).log10()#保持精度不缺失
        
        tf_idf=defaultdict(lambda:defaultdict(Decimal))
        for fang in fang_patn_count:
            for patn in fang_patn_count[fang]:
                #Decimal + 四舍五入 保留精度，方便以后相等性测试
                tf_idf[fang][patn]=(tf[fang][patn]*idf[patn]).quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
            
        #更新到原始数据
        for entry in self.clause_fang_patns:
            for patn in entry.fang_patn.patterns:
                norm_patn=self.normalize_term(patn,self.norm)
                entry.fang_patn.patterns[patn]=tf_idf[entry.fang_patn.fang][norm_patn]

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
        
        #转成字典，#key的格式="条文编号-段落编号-方剂名，顺便归一化证候
        #TF的分子=证候 s 在方剂 f 中出现的次数=永远为1
        #TF的分母=条文方剂 c_f 中所有证候的总数
        clause_fang_patn_dict=defaultdict(lambda:defaultdict(Decimal))
        for entry in self.clause_fang_patns:
                new_fang_key=f"{entry.clause_id}-{entry.clause_seg_id}-{entry.fang_patn.fang}"
                clause_fang_patn_dict[new_fang_key]={self.normalize_term(s,self.norm):Decimal() for s in entry.fang_patn.patterns}

        #TF(s, f) = (证候 s 在方剂 f 中出现的次数) / (方剂 f 中所有证候的总数)
        tf=defaultdict(lambda:defaultdict(Decimal))
        for new_key in clause_fang_patn_dict:
            for patn in clause_fang_patn_dict[new_key]:
                #避免因二进制浮点数无法精确表示十进制数量而可能出现的问题，使用Decimal,方便相等性测试
                tf[new_key][patn]=Decimal(1)/Decimal(len(clause_fang_patn_dict[new_key].keys()))#一个条方的证候不会重复，故总是1
        #IDF的分子=方剂集合 F 中的总"条文方剂"数
        fang_count=len(clause_fang_patn_dict.keys())

        #IDF的分母=包含证候 s 的方剂数
        #patn_fang=defaultdict(set)#同一方剂多次包含算多次,故不用set
        patn_fang=defaultdict(list)#因为新方名带clause_id和列表索引，不重复，故set list都可以
        for new_key, patns in clause_fang_patn_dict.items():
            for patn in patns:
                #用能new_key，不用其中的方剂名。因为本算法不再是1方剂=1文档，而是1条文段落=1文档
                patn_fang[self.normalize_term(patn,self.norm)].append(new_key)
               
        
        idf=defaultdict(lambda:defaultdict(Decimal))
        for patn in patn_fang:
            #idf[patn]=Decimal(log(Decimal(len(patn_fang[patn]))/Decimal(fang_count),10))#精度有缺失
            idf[patn]=(Decimal(fang_count)/Decimal(len(patn_fang[patn]))).log10()#精度一直不缺失

                
        #correlations=defaultdict(lambda:defaultdict(Decimal))
        for new_key in clause_fang_patn_dict:
            for patn in clause_fang_patn_dict[new_key]:
                #Decimal + 四舍五入 保留精度，方便以后相等性测试
                clause_fang_patn_dict[new_key][patn]=(tf[new_key][patn]*idf[patn]).quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
        
        #更新到原始数据
        for entry in self.clause_fang_patns:
                new_fang_key=f"{entry.clause_id}-{entry.clause_seg_id}-{entry.fang_patn.fang}"
                for patn in entry.fang_patn.patterns:
                    norm_patn=self.normalize_term(patn,self.norm)
                    entry.fang_patn.patterns[patn]=clause_fang_patn_dict[new_fang_key][norm_patn]

    def build_pattern_fang_idf(self):
        """
        算法思路，举例：证候“往来寒热”，在所有条文方剂中出现20次，
        在所有条文桂枝汤中出现1次，则=idf[发热][桂枝汤]=log(20/1)，
        所有条文小柴胡汤中出现19次，idf[发热][小柴胡汤]=log(20/19)，
        在所有条文麻黄汤中出现1次，则=idf[发热][麻黄汤]=log(20/1)，
        在所有条文其它汤1中出现0次，则=idf[发热][其它汤1]=log((20+0.5)/(0+0.5))，0.5是平滑处理
        在所有条文其它汤2中出现0次，则=idf[发热][其它汤2]=log((20+0.5)/(0+0.5))，0.5是防止除以0
        ...
        非小柴胡汤的idf虽然较大，但因为都比较大，所以更接近均值，所以方差反而小，而小柴胡汤的方差更大
        所以var[往来寒热][小柴胡汤]=[idf[往来寒热][小柴胡汤]里的方差的权重=1+idf方差
 
        因为一个条文方剂的所有证候是集合，一般不会重复，故TF总是相同，故不再有意义
        好处是：推荐更匹配条文方剂，而不是仅仅是方剂
        TF(Term Frequency)-词频
        TF(s, f) = (证候 s 在方剂 d 中出现的次数) / (方剂 f 中所有证候的总数)
        IDF (Inverse Document Frequency) - 逆文档频率
        IDF(s, F) = log(方剂集合 F 中的总方剂数 / 包含证候 s 的方剂数))
        """
        
        #转成字典，#key的格式="条文编号-段落编号-方剂名，顺便归一化证候
        #TF的分子=证候 s 在方剂 f 中出现的次数=永远为1
        #TF的分母=条文方剂 c_f 中所有证候的总数
        clause_fang_patn_dict=defaultdict(lambda:defaultdict(Decimal))
        for entry in self.clause_fang_patns:
                new_fang_key=f"{entry.clause_id}-{entry.clause_seg_id}-{entry.fang_patn.fang}"
                clause_fang_patn_dict[new_fang_key]={self.normalize_term(s,self.norm):Decimal() for s in entry.fang_patn.patterns}

        #TF(s, f) = (证候 s 在方剂 f 中出现的次数) / (方剂 f 中所有证候的总数)
        tf=defaultdict(lambda:defaultdict(Decimal))
        for new_key in clause_fang_patn_dict:
            for patn in clause_fang_patn_dict[new_key]:
                #避免因二进制浮点数无法精确表示十进制数量而可能出现的问题，使用Decimal,方便相等性测试
                tf[new_key][patn]=Decimal(1)/Decimal(len(clause_fang_patn_dict[new_key].keys()))#一个条方的证候不会重复，故总是1
        #IDF的分子=方剂集合 F 中的总"条文方剂"数
        fang_count=len(clause_fang_patn_dict.keys())

        #IDF的分母=包含证候 s 的方剂数
        #patn_fang=defaultdict(set)#同一方剂多次包含算多次,故不用set
        patn_fang=defaultdict(list)#因为新方名带clause_id和列表索引，不重复，故set list都可以
        for new_key, patns in clause_fang_patn_dict.items():
            for patn in patns:
                #用能new_key，不用其中的方剂名。因为本算法不再是1方剂=1文档，而是1条文段落=1文档
                patn_fang[self.normalize_term(patn,self.norm)].append(new_key)
               
        
        idf=defaultdict(lambda:defaultdict(Decimal))
        for patn in patn_fang:
            #idf[patn]=Decimal(log(Decimal(len(patn_fang[patn]))/Decimal(fang_count),10))#精度有缺失
            idf[patn]=(Decimal(fang_count)/Decimal(len(patn_fang[patn]))).log10()#精度一直不缺失

                
        #correlations=defaultdict(lambda:defaultdict(Decimal))
        for new_key in clause_fang_patn_dict:
            for patn in clause_fang_patn_dict[new_key]:
                #Decimal + 四舍五入 保留精度，方便以后相等性测试
                clause_fang_patn_dict[new_key][patn]=(tf[new_key][patn]*idf[patn]).quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
        
        #更新到原始数据
        for entry in self.clause_fang_patns:
                new_fang_key=f"{entry.clause_id}-{entry.clause_seg_id}-{entry.fang_patn.fang}"
                for patn in entry.fang_patn.patterns:
                    norm_patn=self.normalize_term(patn,self.norm)
                    entry.fang_patn.patterns[patn]=clause_fang_patn_dict[new_fang_key][norm_patn]

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
        
        #转成字典，#key的格式="条文编号-段落编号-方剂名"，顺便归一化证候
        #TF的分子=证候 s 在方剂 f 中出现的次数=一般为1
        #TF的分母=条文方剂 c_f 中所有证候的总数
        clause_fang_patn_dict=defaultdict(lambda:defaultdict(Decimal))
        for entry in self.clause_fang_patns:
                new_fang_key=f"{entry.clause_id}-{entry.clause_seg_id}-{entry.fang_patn.fang}"
                clause_fang_patn_dict[new_fang_key]={self.normalize_term(p,self.norm):Decimal() for p in entry.fang_patn.patterns}

        #TF(s, f) = (证候 s 在方剂 f 中出现的次数) / (方剂 f 中所有证候的总数)
        tf=defaultdict(lambda:defaultdict(Decimal))
        for fang in clause_fang_patn_dict:
            for patn in clause_fang_patn_dict[fang]:
                #避免因二进制浮点数无法精确表示十进制数量而可能出现的问题，使用Decimal,方便相等性测试
                #tf[fang][patn]=Decimal(1)/Decimal(len(clause_fang_patn_dict[fang].keys()))#一个条方的证候不会重复，故总是1
                tf[fang][patn]=Decimal(1)#不再/ (方剂 f 中所有证候的总数)，理由如下：
                #一向量*常数→不会改变向量的方向（只是在此方向的伸缩）→与查询向量的余弦夹角也不会改变→余弦相似度不变
                #一个条方的证候不会重复，故目前是1，以后会修改：1. 调整词频饱和度，2.减低文档长度的影响
        
        # IDF的分子=方剂集合 F 中的总"条文方剂"数
        fang_count=len(clause_fang_patn_dict.keys())

        #IDF的分母=包含证候 s 的方剂数
        #patn_fang=defaultdict(set)#同一方剂多次包含算多次,故不用set
        patn_fang=defaultdict(list)#因为新方名带clause_id和段落索引，不重复，故set list都可以
        for new_key, patn_dict in clause_fang_patn_dict.items():
            #fang=regex.match(r"\d+-\d+-(\w+)",new_key).group(1)
            for patn in patn_dict:
                #用new_key，不用其中抽取的方剂名。因为本算法不再是1方剂=1文档，而是1条文段落=1文档
                patn_fang[self.normalize_term(patn,self.norm)].append(new_key)
        
        idf=defaultdict(lambda:defaultdict(Decimal))
        for patn in patn_fang:
            #idf[patn]=Decimal(log(Decimal(len(patn_fang[patn]))/Decimal(fang_count),10))#精度有缺失
            idf[patn]=(Decimal(fang_count)/Decimal(len(patn_fang[patn]))).log10()#全程不失精度

        #correlations=defaultdict(lambda:defaultdict(Decimal))
        for fang in clause_fang_patn_dict:
            for patn in clause_fang_patn_dict[fang]:
                #Decimal + 四舍五入 保留精度，方便以后相等性测试
                clause_fang_patn_dict[fang][patn]=(tf[fang][patn]*idf[patn]).quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
        
        #更新到原始数据
        for entry in self.clause_fang_patns:
            new_fang_key=f"{entry.clause_id}-{entry.clause_seg_id}-{entry.fang_patn.fang}"
            for patn in entry.fang_patn.patterns:
                norm_patn=self.normalize_term(patn,self.norm)
                entry.fang_patn.patterns[patn]=clause_fang_patn_dict[new_fang_key][norm_patn]

    #平均发相关性统计
    def build_correlation_avg(self):

        fang_patn_count=defaultdict(lambda:defaultdict(int))#每种方（不同条文同名方算一种）的每种证候（同名方的同名证候算一种）的计数
        for entry in self.clause_fang_patns:
            for patn in entry.fang_patn.patterns:
                fang_patn_count[entry.fang_patn.fang][self.normalize_term(patn,self.norm)]+=1

        #为了归一化，因为，如果某个方剂-证候共现次数多，他的相关性数值就越大，代表此证候的权重越大，这不合理,举例：
        # [
        #   {"fang":"桂枝汤",fang_patn{"发热"}} #重复10次
        #   {"fang":"麻黄汤",fang_patn{"发热"，"头痛","身痛"} 仅此1次
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
        for entry in self.clause_fang_patns:
                fang_count[entry.fang_patn.fang]+=1#不同条文里的重名方剂算一个
 
        for fang in fang_patn_count:
            #fang_count[fang]=sum(co_occurs[fang][patn] for patn in co_occurs)
            for patn in fang_patn_count[fang]: 
                #co_occurs[fang][patn] /=fang_count[fang]#不利于相等性测试
                fang_patn_count[fang][patn] =(Decimal(fang_patn_count[fang][patn])/Decimal(fang_count[fang]))\
                    .quantize(Decimal('0.00'),rounding=ROUND_HALF_UP)

        #更新到原始数据
        for entry in self.clause_fang_patns:
            for patn in entry.fang_patn.patterns:
                norm_patn=self.normalize_term(patn,self.norm)
                #原始数据证候处理时归一化，但保留原始值，用原patn的权重，被赋予归一化patn的权重
                entry.fang_patn.patterns[patn]=fang_patn_count[entry.fang_patn.fang][norm_patn]


     #遍历全部条文，逐个计算，然后排序，全程不会丢失 条文-方剂 对应关系
    def recommend_fang(self,query_patns:set[str])->list[Recommend]:
        recommends:list[Recommend]=[]
        if not hasattr(self,"clauses"):
            self.clauses=self.load_SHL_clauses()
        
        #query={self.normalize_term(p,self.norm):1 for p in query_patns}
        norm_query_patn={self.normalize_term(p,self.norm) for p in query_patns}
        for entry in self.clause_fang_patns:
            id=entry.clause_id
            clause_text=self.clauses[id]
            score=Decimal(0)
            norm_fang_patns={self.normalize_term(p,self.norm):entry.fang_patn.patterns[p]\
                              for p in entry.fang_patn.patterns}
            overlap=norm_query_patn.intersection(norm_fang_patns.keys())
            #dot=sum(query.get(s,0)*norm_fang_patns.get(s,0) for s in query)
            #query的默认权重不该是1，而应该是fang_patn的权重，否则：
            # 即使query与fang_patn的证候完全重叠，相似度也达不到100%，这不合理，故改成如下：
            dot=sum(norm_fang_patns[p]**2 for p in overlap)
            if dot==Decimal(0):
                score=0
            else:#dot>0，因为所有权重非负数，则方剂证候权重中必有一个>0，则fang_norm>0，查询证候权重同理，不会除0
                fang_norm=Decimal(sum(v**2 for v in norm_fang_patns.values())).sqrt()
                #不重叠部分，点积时不计入，合理；但"模"计算时必须计入，这样虽降低了相似度，但降得合理：
                #因为不共有部分就是不相似部分更多了，而且也是数学公式决定的，但有个问题：
                #方剂证候权重总是有值的，查询证候重叠部分共享方剂证候权重值；
                # 但若不重叠部分呢？缺省值？缺省=0？理由？
                query_norm=Decimal(sum(norm_fang_patns.get(p,0)**2 for p in norm_query_patn)).sqrt()
                score=dot/query_norm/fang_norm
            recommends.append(Recommend(clause_id=id, clause_text=clause_text,
                                        clause_fang_patn=entry,match_score=score))
        
        sorted_recommends=sorted(recommends,key=lambda x: x.match_score,reverse=True)
        return sorted_recommends
    