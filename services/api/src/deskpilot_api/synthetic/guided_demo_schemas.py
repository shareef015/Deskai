from pydantic import BaseModel,ConfigDict,Field

class StartDemoRequest(BaseModel):
 model_config=ConfigDict(extra="forbid",strict=True)
 pack_id:str=Field(min_length=1,max_length=80)
class ResetDemoRequest(BaseModel):
 model_config=ConfigDict(extra="forbid",strict=True)
 confirmation:str=Field(min_length=1,max_length=40)
