from pydantic import BaseModel,ConfigDict,Field
class StrictModel(BaseModel):model_config=ConfigDict(extra="forbid")
class ActivateRequest(StrictModel):scenario_id:str=Field(min_length=1,max_length=100);expected_version:int=Field(ge=0)
class RollbackRequest(StrictModel):expected_version:int=Field(ge=1)
class ResetRequest(StrictModel):confirmation:str=Field(min_length=1,max_length=40)
class CompareRequest(StrictModel):left_snapshot_id:str;right_snapshot_id:str
