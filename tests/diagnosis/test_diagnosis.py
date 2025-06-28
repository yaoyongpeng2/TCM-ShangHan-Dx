
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
class TestDiagnosis(unittest.TestCase):

    # def __init__(self):
    #     self.diagnosis=Diagnosis()

    def prepare_data(self):
        clauses=[
            {"id":13,"fang":"桂枝汤","syndromes":["太阳病","发热","恶寒","汗出","恶风"]},
            {"id":14,"fang":"桂枝加葛根汤","syndromes":["太阳病","项背强几几","汗出","恶风"]},
            {"id":27,"fang":"桂枝二越婢一汤","syndromes":["太阳病","发热","恶寒","热多寒少","脉微弱"]},
            {"id":35,"fang":"麻黄汤","syndromes":["太阳病","头痛","发热","身疼","腰痛","骨节疼痛","恶风","无汗","喘"]},
            {"id":42,"fang":"桂枝汤","syndromes":["太阳病","外证未解","脉浮弱"]},
            {"id":44,"fang":"桂枝汤","syndromes":["太阳病","外证未解"]},
            {"id":45,"fang":"桂枝汤","syndromes":["太阳病","先发汗不解","脉浮"]}
        ]
        # self.clause_fang_synds=\
        #     [ClauseFangSynd(clause_id=clause["id"],
        #     fang_synds=[FangSynd(fang=clause["fang"],
        #               syndromes={s:Decimal() for s in clause["syndromes"]})]\
        #                 )for clause in clauses]
        
        clause_fang_synds:list[ClauseFangSynd]=[]    
        for clause in clauses:
            clause_id=clause["id"]
            fang=clause["fang"]
            syndromes={s:Decimal() for s in clause["syndromes"]}
            clause_fang_synds.append(ClauseFangSynd(clause_id=clause_id,
                                                    fang_synds=[FangSynd(fang=fang,syndromes=syndromes)]))
        self.clause_fang_synds=clause_fang_synds

        self.norm={
            "翕翕发热":"发热",
            "啬啬恶寒":"恶寒",
            "淅淅恶风":"恶风",
            # "阳浮":"热自发",
            # "阴弱":"汗自出",
            # "热自发":"发热",
            # "汗自出":"汗出",
            # "脉浮弱":"脉浮缓",
            "外证未解":"先发汗不解"           
        }
        self.expected_avg={
            "桂枝汤":{"太阳病":'1',"发热":'0.25',"恶寒":'0.25',"汗出":'0.25',"恶风":'0.25',"先发汗不解":'0.75',"脉浮弱":'0.25',"脉浮":'0.25'},#"先发汗不解"="外证未解"
            "桂枝加葛根汤":{"太阳病":'1.0',"项背强几几":'1.0',"汗出":'1.0',"恶风":'1.0'},
            "桂枝二越婢一汤":{"太阳病":'1.0',"发热":'1.0',"恶寒":'1.0',"热多寒少":'1.0',"脉微弱":'1.0'},
            "麻黄汤":{"太阳病":'1.0',"头痛":'1.0',"发热":'1.0',"身疼":'1.0',"腰痛":'1.0',"骨节疼痛":'1.0',"恶风":'1.0',"无汗":'1.0',"喘":'1.0'}
        }
        self.expected_tf_idf1={
            "桂枝汤":{"太阳病":'0.00',"发热":'0.010',"恶寒":'0.023',"汗出":'0.023',"恶风":'0.010',"先发汗不解":'0.139',"脉浮弱":'0.046',"脉浮":'0.046'},#"先发汗不解"="外证未解"
            "桂枝加葛根汤":{"太阳病":'0.0',"项背强几几":'0.151',"汗出":'0.075',"恶风":'0.031'},
            "桂枝二越婢一汤":{"太阳病":'0.0',"发热":'0.025',"恶寒":'0.06',"热多寒少":'0.120',"脉微弱":'0.120'},
            "麻黄汤":{"太阳病":'0.00',"头痛":'0.067',"发热":'0.014',"身疼":'0.067',"腰痛":'0.067',"骨节疼痛":'0.067',"恶风":'0.014',"无汗":'0.067',"喘":'0.067'}
        }
        self.expected_tf_idf2={#key的格式="条文编号-方名-防同名方剂后缀"，类似数据库的多列主键
            "13-桂枝汤-0":{"太阳病":'0.00',"发热":'0.074',"恶寒":'0.109',"汗出":'0.109',"恶风":'0.074'},
            "14-桂枝加葛根汤-0":{"太阳病":'0.0',"项背强几几":'0.211',"汗出":'0.136',"恶风":'0.092'},
            "27-桂枝二越婢一汤-0":{"太阳病":'0.0',"发热":'0.074',"恶寒":'0.109',"热多寒少":'0.169',"脉微弱":'0.169'},
            "35-麻黄汤-0":{"太阳病":'0.00',"头痛":'0.094',"发热":'0.041',"身疼":'0.094',"腰痛":'0.094',"骨节疼痛":'0.094',"恶风":'0.041',"无汗":'0.094',"喘":'0.094'},
            "42-桂枝汤-0":{"太阳病":'0.00',"先发汗不解":'0.123',"脉浮弱":'0.282'},
            "44-桂枝汤-0":{"太阳病":'0.00',"先发汗不解":'0.184'},
            "45-桂枝汤-0":{"太阳病":'0.00',"先发汗不解":'0.123',"脉浮":'0.282'}

        }

        
    def _test_recommend_fang(self):
        self.prepare_data()
        diagnosis=Diagnosis(self.norm,self.clause_fang_synds,Correl.TF_IDF_1)
        #diagnosis.__init__(self.norm,self.clause_fang_synds,Correl.AVG)
        recomends=diagnosis.recommend_fang({'发热','恶寒','汗出'})#14/27/13/35/42/44/45
        recomend_ids=[r.clause_id for r in recomends]
        assert recomend_ids==[27,14,13,35,42,44,45]
        #[13,42,44,45]=桂枝汤，证候总数太多→TF分母太大→TF太低→导致分数下降，改进TF计算方式？
        # #27的发热(0.025）+恶寒（0.06)=0.085
        # #14的汗出"(0.075)=0.075
        # #13的发热(0.01）+恶寒（0.023)+汗出(0.023)=0.056
        assert recomends[0].clause_id==27
        assert recomends[0].fang_synd.fang=="桂枝二越婢一汤"
        assert recomends[0].clause.startswith("27.")

        diagnosis=Diagnosis(self.norm,self.clause_fang_synds,Correl.TF_IDF_2)
        #diagnosis.__init__(self.norm,self.clause_fang_synds,Correl.AVG)
        recomends=diagnosis.recommend_fang({'发热','恶寒','汗出'})#14/27/13/35/42/44/45
        recomend_ids=[r.clause_id for r in recomends]
        assert recomend_ids==[13,27,14,35,42,44,45]
        # #27虽只有"汗出"一个脉证对号，但它权重(0.08)高
        assert recomends[0].clause_id==13
        assert recomends[0].fang_synd.fang=="桂枝汤"
        assert recomends[0].clause.startswith("13.")

    def test_build_correlation_avg(self):
        self.prepare_data()
        diagnosis=Diagnosis(self.norm,self.clause_fang_synds,Correl.AVG)
        expected=self.expected_avg
        for entry in diagnosis.clause_fang_synds:
            for fang_synd in entry.fang_synds:
                for synd,weight in fang_synd.syndromes.items():
                    norm_synd=diagnosis.normalize_term(synd,self.norm)
                    assert Decimal(expected[fang_synd.fang][norm_synd])==weight

    def _test_build_correlation_tf_idf_1(self):
        self.prepare_data()
        diagnosis=Diagnosis(self.norm,self.clause_fang_synds,Correl.TF_IDF_1)
        expected=self.expected_tf_idf1

        for entry in diagnosis.clause_fang_synds:
            for fang_synd in entry.fang_synds:
                for synd,weight in fang_synd.syndromes.items():
                    norm_synd=diagnosis.normalize_term(synd,self.norm)
                    assert Decimal(expected[fang_synd.fang][norm_synd])==weight

    def _test_build_correlation_tf_idf_2(self):
        self.prepare_data()
        diagnosis=Diagnosis(self.norm,self.clause_fang_synds,Correl.TF_IDF_2)
        expected=self.expected_tf_idf2

        for entry in diagnosis.clause_fang_synds:
            for index,fang_synd in enumerate(entry.fang_synds):
                new_fang_key=f"{entry.clause_id}-{fang_synd.fang}-{index}"
                for synd,weight in fang_synd.syndromes.items():
                    norm_synd=diagnosis.normalize_term(synd,self.norm)
                    assert Decimal(expected[new_fang_key][norm_synd])==weight

if  __name__=="__main__":
    unittest.main()