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

from diagnosis.diagnosis import Diagnosis
class TestDiagnosis(unittest.TestCase):

    def test_identify_pattern(self):
        diagnosis=Diagnosis()
        # diagnosis.identify_pattern({'发热','恶寒','汗出'})
        recomends=diagnosis.recommend_fang({'发热','恶寒','汗出'})
        assert recomends[0].id==12
        assert recomends[0].fang_synds[0].fang=="桂枝汤"
        import json
        recommend_json="["+",".join(r.model_dump_json() for r in recomends)+"]"
        pretty_obj=json.loads(recommend_json)
        pretty_json=json.dumps(pretty_obj,indent=4)
        print("pretty:\n"+pretty_json)
        print("ugly:\n"+recommend_json)

if  __name__=="__main__":
    unittest.main()