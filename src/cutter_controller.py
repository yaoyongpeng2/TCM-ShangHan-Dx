from fastapi import FastAPI,Depends,Path
from nlp.word_cut import WordCutter
from pydantic import BaseModel
# import logging
# logger=logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app=FastAPI()

class DataRequest(BaseModel):
    text:str
    def __init__(self, text:str):
        super().__init__(text=text)
        self.text=text

class DataResponse(BaseModel):
    raw:str
    tokens:list[str]

    def __init__(self,raw:str,tokens:list[str]):
        super().__init__(raw=raw,tokens=tokens)
        self.raw=raw
        self.tokens=tokens
    def __eq__(self,other)->bool:
        if not isinstance(other,DataResponse):#隐含了None的判断
            return False
        return (self.raw==other.raw and self.tokens==other.tokens)
def get_cutter():
    cutter=WordCutter()
    if not hasattr(cutter,"_dict_loaded") or cutter._dict_loaded==False:
        cutter.load_dicts()
    return cutter

CUT_TEXT_PATH="/tokon/cut"
ADD_DICT_PATH="/tokon/add-dict"
HOST="127.0.0.1"
PORT=8000
@app.post(CUT_TEXT_PATH)
async def cut_text(data:DataRequest, cutter:WordCutter=Depends(get_cutter)):
    logger.debug(f"Request text={data.text}")
    tokens=cutter.cut(data.text)
    logger.debug(f"Response tokens={tokens}")
    return DataResponse(raw=data.text,tokens=tokens)

@app.post(ADD_DICT_PATH)
async def add_dict(dict:set[str], cutter:WordCutter=Depends(get_cutter)):
    logger.debug(f"Request dict={dict}")
    cutter.load_dict(dict)
    return

if __name__ == "__main__":
    # import logging
    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # )
    # logger = logging.getLogger(__name__)
    logger.info("Starting service...")

    import uvicorn, os
    file_name=os.path.basename(__file__)
    module_name=file_name.split(".")[0]
    uvicorn.run(module_name+":app", host=HOST, port=PORT, reload=False,log_level="debug")
    #uvicorn.run(__name__+":app", host=HOST, port=PORT, reload=False,log_level="debug")