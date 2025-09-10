
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
        
        # clauses=[#元组格式=(id,fang,pattern_list)
        #     (13,"桂枝汤",["太阳病","发热","恶寒","汗出","恶风"]),
        #     (14,"桂枝加葛根汤",["太阳病","项背强几几","汗出","恶风"]),
        #     (27,"桂枝二越婢一汤",["太阳病","发热","恶寒","热多寒少","脉微弱"]),
        #     (35,"麻黄汤",["太阳病","头痛","发热","身疼","腰痛","骨节疼痛","恶风","无汗","喘"]),
        #     (42,"桂枝汤",["太阳病","外证未解","脉浮弱"]),
        #     (44,"桂枝汤",["太阳病","外证未解"]),
        #     (45,"桂枝汤",["太阳病","先发汗不解","脉浮"])
        # ]
        
        # clause_fang_patns:list[ClauseFangPatn]=[]
        # seg_count=defaultdict(int)#默认值=0
        # for clause_id,fang,fang_patns in clauses:
        #     seg_count[clause_id]+=1#clause_id有重复=条文被拆分了
        #     patterns={p:Decimal() for p in fang_patns}
        #     clause_fang_patns.append(ClauseFangPatn(clause_id=clause_id,clause_seg_id=seg_count[clause_id]-1,
        #                                             fang_patn=FangPatn(fang=fang,patterns=patterns)))
        # self.clause_fang_patns=clause_fang_patns
        # self.expected_BM25={#key的格式="条文编号-方名-防同名方剂后缀"，类似数据库的多列主键
        #     "太阳病":'0.000',"发热":'0.368',"恶寒":'0.544',"汗出":'0.544',"恶风":'0.368',
        #     "项背强几几":'0.845',"热多寒少":'0.845',"脉微弱":'0.845',
        #     "头痛":'0.845',"身疼":'0.845',"腰痛":'0.845',"骨节疼痛":'0.845',"无汗":'0.845',"喘":'0.845',
        #     "先发汗不解":'0.368',"脉浮弱":'0.845',"脉浮":'0.845'
        # }

        # 经常出现的方剂用法可靠性低于偶尔出现的用法，不合理
        # self.expected_avg={
        #     "桂枝汤":{"太阳病":'1',"发热":'0.25',"恶寒":'0.25',"汗出":'0.25',"恶风":'0.25',"先发汗不解":'0.75',"脉浮弱":'0.25',"脉浮":'0.25'},#"先发汗不解"="外证未解"
        #     "桂枝加葛根汤":{"太阳病":'1.0',"项背强几几":'1.0',"汗出":'1.0',"恶风":'1.0'},
        #     "桂枝二越婢一汤":{"太阳病":'1.0',"发热":'1.0',"恶寒":'1.0',"热多寒少":'1.0',"脉微弱":'1.0'},
        #     "麻黄汤":{"太阳病":'1.0',"头痛":'1.0',"发热":'1.0',"身疼":'1.0',"腰痛":'1.0',"骨节疼痛":'1.0',"恶风":'1.0',"无汗":'1.0',"喘":'1.0'}
        # }

        #缺陷：适应症越多的方剂，其TF的分母越大，导致权重降低，不合理
        # self.expected_tf_idf1={
        #     "桂枝汤":{"太阳病":'0.00',"发热":'0.010',"恶寒":'0.023',"汗出":'0.023',"恶风":'0.010',"先发汗不解":'0.139',"脉浮弱":'0.046',"脉浮":'0.046'},#"先发汗不解"="外证未解"
        #     "桂枝加葛根汤":{"太阳病":'0.0',"项背强几几":'0.151',"汗出":'0.075',"恶风":'0.031'},
        #     "桂枝二越婢一汤":{"太阳病":'0.0',"发热":'0.025',"恶寒":'0.06',"热多寒少":'0.120',"脉微弱":'0.120'},
        #     "麻黄汤":{"太阳病":'0.00',"头痛":'0.067',"发热":'0.014',"身疼":'0.067',"腰痛":'0.067',"骨节疼痛":'0.067',"恶风":'0.014',"无汗":'0.067',"喘":'0.067'}
        # }

        #以下测试数据被注释的原因：比起BM25唯一区别就是 
        #此算法多除了一次方剂证候数(#从数据本身也极易看出)，
        # 而这在余弦相似度算法里是多余的，无任何作用。
        # self.expected_tf_idf2={#key的格式="条文编号-方名-防同名方剂后缀"，类似数据库的多列主键
        #     "13-0-桂枝汤":{"太阳病":'0.000',"发热":'0.074',"恶寒":'0.109',"汗出":'0.109',"恶风":'0.074'},
        #     "14-0-桂枝加葛根汤":{"太阳病":'0.0',"项背强几几":'0.211',"汗出":'0.136',"恶风":'0.092'},
        #     "27-0-桂枝二越婢一汤":{"太阳病":'0.0',"发热":'0.074',"恶寒":'0.109',"热多寒少":'0.169',"脉微弱":'0.169'},
        #     "35-0-麻黄汤":{"太阳病":'0.00',"头痛":'0.094',"发热":'0.041',"身疼":'0.094',"腰痛":'0.094',"骨节疼痛":'0.094',"恶风":'0.041',"无汗":'0.094',"喘":'0.094'},
        #     "42-0-桂枝汤":{"太阳病":'0.00',"先发汗不解":'0.123',"脉浮弱":'0.282'},
        #     "44-0-桂枝汤":{"太阳病":'0.00',"先发汗不解":'0.184'},
        #     "45-0-桂枝汤":{"太阳病":'0.00',"先发汗不解":'0.123',"脉浮":'0.282'}
        # }

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

    def prepare_SHL_data(self)->tuple[
        dict[str,str],
        list[ClauseFangPatn],
        dict[str,str],
        list[list[str]]
    ]:
        norm={
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

        clauses=[#元组格式=(id,fang,pattern_list)
            (12,"桂枝汤",["太阳中风","阳浮","阴弱","啬啬恶寒","淅淅恶风","翕翕发热","鼻鸣","干呕"]),
            (13,"桂枝汤",["太阳病","发热","恶寒","汗出","恶风"]),
            (14,"桂枝加葛根汤",["太阳病","项背强几几","汗出","恶风"]),
            (15,"禁-桂枝汤",["太阳病","下后","气不上冲"]),
            (15,"桂枝汤",["太阳病","下后","气上冲"]),#1条文分两段--1禁1可
            (25,"桂枝汤",["服桂枝汤","大汗出","脉浮"]),#另一例：1条文，不同证候，不同治方
            (25,"桂枝二麻黄一汤",["服桂枝汤","无汗","脉浮","形似疟","一日再发"]),
            (27,"禁-汗",["热多寒少","脉微弱"]),
            (27,"桂枝二越婢一汤",["太阳病","发热","恶寒","热多寒少","脉微弱","无汗"]),
            (35,"麻黄汤",["太阳病","头痛","发热","身疼","腰痛","骨节疼痛","恶风","无汗","喘"]),
            (42,"桂枝汤",["太阳病","外证未解","脉浮弱"]),
            (44,"桂枝汤",["太阳病","外证未解"]),
            (45,"桂枝汤",["太阳病","先发汗不解","脉浮"])
        ]
                
         #统计条文段落编号并改变格式
        clause_fang_patns:list[ClauseFangPatn]=[]
        seg_count=defaultdict(int)#默认值=0
        for clause_id,fang,patns in clauses:
            seg_count[clause_id]+=1#clause_id有重复=条文被拆分了
            clause_fang_patns.append(ClauseFangPatn(clause_id=clause_id,clause_seg_id=seg_count[clause_id]-1,
                                                    fang=fang,patterns=set(patns)))

        expected_weight={
            "太阳病":'0.176',"发热":'0.528',"恶风":'0.528',
            "无汗":'0.653',"先发汗不解":'0.653',"恶寒":'0.653',"脉浮":'0.653',
            "服桂枝汤":'0.829',"下后":'0.829',"汗出":'0.829',"热多寒少":'0.829',"脉微弱":'0.829',
            "太阳中风":'1.13',"阳浮":'1.13',"阴弱":'1.13',"项背强几几":'1.13',"大汗出":'1.13',"头痛":'1.13',
            "气不上冲":'1.13',"气上冲":'1.13',"脉浮弱":'1.13',"形似疟":'1.13',"一日再发":'1.13',
            "身疼":'1.13',"腰痛":'1.13',"骨节疼痛":'1.13',"鼻鸣":'1.13',"干呕":'1.13',"喘":'1.13'
        }

        expected_recommend_score=[  #clauses[i]的证候列表分别与所有条文（包括自己]）做匹配，所得推荐分数列表存于本列表第i行
                                    #未清晰表示意图，本列表只存储半个矩阵，另一半通过matrix[j][i]==matrix[i][j]获得
            ['1'	,'0.278','0.068','0'	,'0'	,'0'	,'0'	,'0'	,'0.163','0.076','0'	,'0'	,'0'	],
            [		'1'		,'0.507','0.017','0.017','0'	,'0'	,'0'	,'0.354','0.166','0.018','0.035','0.025'],
            [				'1'		,'0.015','0.015','0'	,'0'	,'0'	,'0.013','0.076','0.016','0.03' ,'0.022'],
            [						'1'		,'0.36' ,'0'    ,'0'	,'0'	,'0.014','0.008','0.017','0.032','0.023'],
            [								'1'		,'0'    ,'0'	,'0'	,'0.014','0.008','0.017','0.032','0.023'],
            [										'1'		,'0.356','0'	,'0'	,'0'	,'0'	,'0'	,'0.293'],
            [												'1'		,'0'	,'0.132','0.077','0'	,'0'	,'0.224'],
            [														'1'		,'0.736','0'	,'0'	,'0'	,'0'	],
            [																'1'		,'0.17','0.015','0.029' ,'0.021'],
            [																		'1'		,'0.009','0.017','0.012'],
            [																				'1'		,'0.514','0.369'],
            [																						'1'		,'0.719'],
            [																								'1'		]
        ]

        cols=rows=len(expected_recommend_score)
        for i in range(rows):
            expected_recommend_score[i][:0]=['' for _ in range(i)]#在列表头部插入空元素，使每行列数相同
        for i in range(rows):
            for j in range(i,cols):
                expected_recommend_score[j][i]=expected_recommend_score[i][j]#对角值相同

        return (norm,clause_fang_patns,expected_weight,expected_recommend_score)
    def prepare_makeup_data(self)->tuple[
        dict[str,str],
        list[ClauseFangPatn],
        dict[str,str],
        list[list[str]]
        ]:
        norm={
            "占位证候":"灵异事件"
        }
        raw_input=[
            #阶梯型：(证|特异证)\d，后面数字越大→idf大→权重高；
            (1001,"方1001-0",["证1"]),
            (1002,"方1002-0",["证1","证2"]),
            (1003,"方1003-0",["证1","证2","证3"]),
            (1004,"方1004-0",["证1","证2","证3","证4"]),
            (1005,"方1005-0",["证1","证2","证3","证4","证5"]),
            (1006,"方1006-0",["证1","证2","证3","证4","证5","证6"]),
            (1007,"方1007-0",["证1","证2","证3","证4","证5","证6","特异证1"]),
            (1008,"方1008-0",["证1","证2","证3","证4","证5","证6","特异证1","特异证2"]),#1008条第0段
            (1008,"方1008-1",["证1","证2","证3","证4","证5","证6","特异证1","特异证2","特异证3"])#1008条第1段
        ]
 
        #统计条文段落编号并改变格式
        clause_fang_patns:list[ClauseFangPatn]=[]
        seg_count=defaultdict(int)#默认值=0
        for clause_id,fang,patns in raw_input:
            seg_count[clause_id]+=1#clause_id有重复=条文被拆分了
            clause_fang_patns.append(ClauseFangPatn(clause_id=clause_id,clause_seg_id=seg_count[clause_id]-1,
                                                    fang=fang,patterns=set(patns)))

        expected_weight={
            "证1":'0.023',"证2":'0.075',"证3":'0.133',
            "证4":'0.200',"证5":'0.279',"证6":'0.376',
            "特异证1":'0.501',"特异证2":'0.677',"特异证3":'0.978'
        }
        expected_recommend_score=[#raw_input[i]的证候列表分别与所有条文（包括自己]）做匹配，所得推荐分数列表存于本列表第i行
                                    #未清晰表示意图，本列表只存储半个矩阵，另一半通过matrix[j][i]==matrix[i][j]获得
            #同一行，A·B/(||A||X||B||),A·B及||A||不变，后列||B||变大，故后列分数变小
            ['1.'	,'0.3'	,'0.152','0.093','0.062','0.044','0.032','0.024','0.017'],
            [		'1.'	,'0.508','0.31'	,'0.208','0.147','0.107','0.079','0.056'],
            [				'1.'	,'0.611','0.41'	,'0.29'	,'0.211','0.155','0.11'	],
            [						'1.'	,'0.671','0.474','0.345','0.253','0.181'],
            [								'1.'	,'0.707','0.515','0.378','0.269'],
            [										'1.'	,'0.728','0.534','0.381'],
            [												'1.'	,'0.733','0.523'],
            [														'1.'	,'0.713'],
            [																'1.'	]
        ]
        cols=rows=len(expected_recommend_score)
        #full_matrix_score=[['' for _ in range(rows)] for _ in range(rows)]#一个全空字符的矩阵
        for i in range(rows):
            expected_recommend_score[i][:0]=['' for _ in range(i)]#在列表头部插入空元素，使每行列数相同
        for i in range(rows):
            for j in range(i,cols):
                expected_recommend_score[j][i]=expected_recommend_score[i][j]#对角值相同


                
        return (norm,clause_fang_patns,expected_weight,expected_recommend_score)
     
    def prepare_JFSYL_case(self)->list[tuple]:
        split_dict={
            "脉浮缓":{"脉浮","脉缓"}
        }

        #《经方实验录》案例：
        JFSYL_case=[
            (1,["发热","汗出","恶风","头痛","鼻塞","脉浮缓"],"桂枝汤"),
            (2,[],"")
        ]

        return (JFSYL_case) 
    def test_load_from_file(self): 
        self.prepare_data()
        diagnosis=Diagnosis()
        ids=[c.clause_id for c in diagnosis.clause_fang_patns]
        ids=sorted(ids)
        #assert self.fang_file_ids==ids[0:len(self.fang_file_ids)]
        for i in range(len(self.fang_file_ids)):
            assert self.fang_file_ids[i]==ids[i]
    def test_build_correlation_BM25(self):
        #真实的测试数据，取自《伤寒论》------
        norm,clause_fang_patns,expected_weight,score=self.prepare_SHL_data()
        diagnosis=Diagnosis(norm,clause_fang_patns,Correl.BM25)

        for p,expected_weight in expected_weight.items():
            weight=diagnosis.patn_weight[diagnosis.normalize_term(p,norm)]\
                                        .quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
            assert Decimal(expected_weight)==weight

        #编造的测试数据，为了全覆盖各种可能------
        norm,clause_fang_patns,expected_weight,score=self.prepare_makeup_data()
        diagnosis=Diagnosis(norm,clause_fang_patns,Correl.BM25)

        for p,expected_weight in expected_weight.items():
            weight=diagnosis.patn_weight[diagnosis.normalize_term(p,norm)]\
                                        .quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)
            assert Decimal(expected_weight)==weight
       
    def test_recommend_fang(self):
        #真实的测试数据，取自《伤寒论》------
        norm,clause_fang_patns,expected_weight,scores=self.prepare_SHL_data()
        diagnosis=Diagnosis(norm,clause_fang_patns,Correl.BM25)
        for i in range(len(clause_fang_patns)):
            query=clause_fang_patns[i].patterns
            recommends=diagnosis.recommend_fang(query)
            recommend_scores=[r.match_score.quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)\
                               for r in recommends]
            expected_scores=[Decimal(s) for s in scores[i]]
            expected_scores=sorted(expected_scores,reverse=True)
            assert recommend_scores==expected_scores

        #编造的测试数据，为了全覆盖各种可能------
        norm,clause_fang_patns,expected_weight,scores=self.prepare_makeup_data()
        diagnosis=Diagnosis(norm,clause_fang_patns,Correl.BM25)
        for i in range(len(clause_fang_patns)):
            query=clause_fang_patns[i].patterns
            recommends=diagnosis.recommend_fang(query)
            recommend_scores=[r.match_score.quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)\
                               for r in recommends]
            expected_scores=[Decimal(s) for s in scores[i]]
            expected_scores=sorted(expected_scores,reverse=True)
            assert recommend_scores==expected_scores

        #以全局皆无证做干扰项，验证结果不变
        #全局皆无证=所有学习数据里都没有的证候
        no_such_patns=[f'全局皆无证{i}' for i in range(len(clause_fang_patns))]
        for i in range(len(clause_fang_patns)):
            original_query=set(clause_fang_patns[i].patterns)
            #插入不同数量的不是证候的证（全局皆无证），以模拟干扰项
            #query.extend(no_such_patns[0:i])#错，query是dict_keys类型，不可修改
            query=original_query|set(no_such_patns[0:i+1])
            recommends=diagnosis.recommend_fang(query)
            recommend_scores=[r.match_score.quantize(Decimal('0.000'),rounding=ROUND_HALF_UP)\
                               for r in recommends]
            expected_scores=[Decimal(s) for s in scores[i]]
            expected_scores=sorted(expected_scores,reverse=True)
            assert recommend_scores==expected_scores#虽有干扰项，但得分仍然相同，因为全局皆无证的权重==0

        #《经方实验录》数据
        norm,clause_fang_patns,_,_=self.prepare_SHL_data()
        diagnosis=Diagnosis(norm,clause_fang_patns,Correl.BM25)
        JFSYL_data=self.prepare_JFSYL_case()
        for entry in JFSYL_data:
            _, query,fang=entry
            recommends=diagnosis.recommend_fang(query)
            assert recommends[0].clause_fang_patn.fang==fang


if  __name__=="__main__":
    unittest.main()