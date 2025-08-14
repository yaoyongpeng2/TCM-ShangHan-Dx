
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
        clauses=[#元组格式=(id,fang,pattern_list)
            (13,"桂枝汤",["太阳病","发热","恶寒","汗出","恶风"]),
            (14,"桂枝加葛根汤",["太阳病","项背强几几","汗出","恶风"]),
            (27,"桂枝二越婢一汤",["太阳病","发热","恶寒","热多寒少","脉微弱"]),
            (35,"麻黄汤",["太阳病","头痛","发热","身疼","腰痛","骨节疼痛","恶风","无汗","喘"]),
            (42,"桂枝汤",["太阳病","外证未解","脉浮弱"]),
            (44,"桂枝汤",["太阳病","外证未解"]),
            (45,"桂枝汤",["太阳病","先发汗不解","脉浮"])
        ]
        
        clause_fang_patns:list[ClauseFangPatn]=[]
        seg_count=defaultdict(int)#默认值=0
        for clause_id,fang,fang_patns in clauses:
            seg_count[clause_id]+=1#clause_id有重复=条文被拆分了
            patterns={p:Decimal() for p in fang_patns}
            clause_fang_patns.append(ClauseFangPatn(clause_id=clause_id,clause_seg_id=seg_count[clause_id]-1,
                                                    fang_patn=FangPatn(fang=fang,patterns=patterns)))
        self.clause_fang_patns=clause_fang_patns

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

        # self.expected_tf_idf2={#key的格式="条文编号-方名-防同名方剂后缀"，类似数据库的多列主键
        #     "13-0-桂枝汤":{"太阳病":'0.000',"发热":'0.074',"恶寒":'0.109',"汗出":'0.109',"恶风":'0.074'},
        #     "14-0-桂枝加葛根汤":{"太阳病":'0.0',"项背强几几":'0.211',"汗出":'0.136',"恶风":'0.092'},
        #     "27-0-桂枝二越婢一汤":{"太阳病":'0.0',"发热":'0.074',"恶寒":'0.109',"热多寒少":'0.169',"脉微弱":'0.169'},
        #     "35-0-麻黄汤":{"太阳病":'0.00',"头痛":'0.094',"发热":'0.041',"身疼":'0.094',"腰痛":'0.094',"骨节疼痛":'0.094',"恶风":'0.041',"无汗":'0.094',"喘":'0.094'},
        #     "42-0-桂枝汤":{"太阳病":'0.00',"先发汗不解":'0.123',"脉浮弱":'0.282'},
        #     "44-0-桂枝汤":{"太阳病":'0.00',"先发汗不解":'0.184'},
        #     "45-0-桂枝汤":{"太阳病":'0.00',"先发汗不解":'0.123',"脉浮":'0.282'}
        # }
        #以上测试数据被注释的原因：比起BM25唯一区别就是 
        #此算法多除了一次方剂证候数(#从数据本身也极易看出)，
        # 而这在余弦相似度算法里是多余的，无任何作用。
        self.expected_BM25={#key的格式="条文编号-方名-防同名方剂后缀"，类似数据库的多列主键
            "13-0-桂枝汤":{"太阳病":'0.000',"发热":'0.368',"恶寒":'0.544',"汗出":'0.544',"恶风":'0.368'},
            "14-0-桂枝加葛根汤":{"太阳病":'0.000',"项背强几几":'0.845',"汗出":'0.544',"恶风":'0.368'},
            "27-0-桂枝二越婢一汤":{"太阳病":'0.000',"发热":'0.368',"恶寒":'0.544',"热多寒少":'0.845',"脉微弱":'0.845'},
            "35-0-麻黄汤":{"太阳病":'0.000',"头痛":'0.845',"发热":'0.368',"身疼":'0.845',"腰痛":'0.845',"骨节疼痛":'0.845',"恶风":'0.368',"无汗":'0.845',"喘":'0.845'},
            "42-0-桂枝汤":{"太阳病":'0.000',"先发汗不解":'0.368',"脉浮弱":'0.845'},
            "44-0-桂枝汤":{"太阳病":'0.000',"先发汗不解":'0.368'},
            "45-0-桂枝汤":{"太阳病":'0.000',"先发汗不解":'0.368',"脉浮":'0.845'}
        }
        self.fang_file_ids=self.prepare_ids()
    def prepare_ids(self):
        ids=[12,13,14,15,15,16,17,18,19,
            20,21,22,23,23,23,24,25,25,26,27,27,28,29,29,29,29,29,
            31,32,33,34,35,36,37,37,38,38,39,
            40,41,41,42,43,44,45,46,46,47,48,48,48,49,49,
            50,51,52,53,54,55,56,56,56,57,
            61,62,63,63,64,65,66,67,68,69,
            70,70,71,71,72,73,73,74
            #更多待加
        ]
   
        # id_range=(12,75)
        # _no_fang={30,58,59,60}#暂缺，或没有治方，只有医理
        # _2_seg={15,25,27,37,38,41,46,49,63,70,71,73}#分成2段也即id出现2次
        # _3_seg={23,48,56}#分成3段也即id出现3次
        # _4_seg={}#分成4段也即id出现4次
        # _5_seg={29}#分成5段也即id出现5次
        # ids=set(range(*id_range,1))
        # ids.difference_update(_no_fang)
        # ids=list(ids)
        # #ids.append(_2_seg)
        # ids.extend(_2_seg)
        # ids.extend(list(_3_seg)*2)
        # ids.extend(list(_4_seg)*3)
        # ids.extend(list(_5_seg)*4)
        # ids=sorted(ids)
        return ids
    def test_load_from_file(self): 
        self.prepare_data()
        diagnosis=Diagnosis()
        ids=[c.clause_id for c in diagnosis.clause_fang_patns]
        ids=sorted(ids)
        #assert self.fang_file_ids==ids[0:len(self.fang_file_ids)]
        for i in range(len(self.fang_file_ids)):
            assert self.fang_file_ids[i]==ids[i]
    def test_recommend_fang(self):
        self.prepare_data()
        diagnosis=Diagnosis(self.norm,self.clause_fang_patns,Correl.TF_IDF_1)
        #diagnosis.__init__(self.norm,self.clause_fang_patns,Correl.AVG)
        recomends=diagnosis.recommend_fang({'发热','恶寒','汗出'})
        recomend_ids=[r.clause_fang_patn.clause_id for r in recomends]
#        assert recomend_ids==[13, 27, 14, 35, 42, 44, 45]
        assert recomend_ids==[13, 14, 27,35, 42, 44, 45]

        
        #TF_IDF_2算法被废弃
        # diagnosis=Diagnosis(self.norm,self.clause_fang_patns,Correl.TF_IDF_2)
        # #diagnosis.__init__(self.norm,self.clause_fang_patns,Correl.AVG)
        # recomends=diagnosis.recommend_fang({'发热','恶寒','汗出'})#14/27/13/35/42/44/45
        # recomend_ids=[r.clause_fang_patn.clause_id for r in recomends]
        # assert recomend_ids==[13,14,27,35,42,44,45]
        # assert recomends[0].clause_fang_patn.fang_patn.fang=="桂枝汤"
        # assert recomends[0].clause_text.startswith("13.")#条文正确加载了

        diagnosis=Diagnosis(self.norm,self.clause_fang_patns,Correl.BM25)
        recomends=diagnosis.recommend_fang({'发热','恶寒','汗出'})#14/27/13/35/42/44/45
        recomend_ids=[r.clause_fang_patn.clause_id for r in recomends]
        assert recomend_ids==[13,14,27,35,42,44,45]
        assert recomends[0].clause_fang_patn.fang_patn.fang=="桂枝汤"
        assert recomends[0].clause_text.startswith("13.")#条文正确加载了


    def test_build_correlation_avg(self):
        self.prepare_data()
        diagnosis=Diagnosis(self.norm,self.clause_fang_patns,Correl.AVG)
        expected=self.expected_avg
        for entry in diagnosis.clause_fang_patns:
            for patn,weight in entry.fang_patn.patterns.items():
                norm_patn=diagnosis.normalize_term(patn,self.norm)
                assert Decimal(expected[entry.fang_patn.fang][norm_patn])==weight

    def test_build_correlation_tf_idf_1(self):
        self.prepare_data()
        diagnosis=Diagnosis(self.norm,self.clause_fang_patns,Correl.TF_IDF_1)
        expected=self.expected_tf_idf1

        for entry in diagnosis.clause_fang_patns:
                for patn,weight in entry.fang_patn.patterns.items():
                    norm_patn=diagnosis.normalize_term(patn,self.norm)
                    assert Decimal(expected[entry.fang_patn.fang][norm_patn])==weight
    
    #vs BM25,此算法多余，故删除
    # def test_build_correlation_tf_idf_2(self):
    #     self.prepare_data()
    #     diagnosis=Diagnosis(self.norm,self.clause_fang_patns,Correl.TF_IDF_2)
    #     expected=self.expected_tf_idf2

    #     for entry in diagnosis.clause_fang_patns:
    #             new_fang_key=f"{entry.clause_id}-{entry.clause_seg_id}-{entry.fang_patn.fang}"
    #             for patn,weight in entry.fang_patn.patterns.items():
    #                 norm_patn=diagnosis.normalize_term(patn,self.norm)
    #                 assert Decimal(expected[new_fang_key][norm_patn])==weight

    def test_build_correlation_BM25(self):
        self.prepare_data()
        diagnosis=Diagnosis(self.norm,self.clause_fang_patns,Correl.BM25)
        expected=self.expected_BM25

        for entry in diagnosis.clause_fang_patns:
            new_fang_key=f"{entry.clause_id}-{entry.clause_seg_id}-{entry.fang_patn.fang}"
            for patn,weight in entry.fang_patn.patterns.items():
                norm_patn=diagnosis.normalize_term(patn,self.norm)
                assert Decimal(expected[new_fang_key][norm_patn])==weight

if  __name__=="__main__":
    unittest.main()