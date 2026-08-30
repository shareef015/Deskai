from __future__ import annotations
import hashlib,json,re
from dataclasses import dataclass
from typing import Literal
class FrontendContractDenied(ValueError):pass
@dataclass(frozen=True)
class ViewModelField:name:str;kind:Literal["string","integer","number","boolean","string_list"];required:bool=True
@dataclass(frozen=True)
class ViewModelSchema:schema_id:str;version:str;fields:tuple[ViewModelField,...];allow_unknown:bool=False
@dataclass(frozen=True)
class ValidatedViewModel:schema_id:str;value:dict[str,object];fingerprint:str
def validate_view_model(schema:ViewModelSchema,value:object)->ValidatedViewModel:
 if not isinstance(value,dict):raise FrontendContractDenied("view model must be an object")
 fields={field.name:field for field in schema.fields};unknown=set(value)-set(fields)
 if unknown and not schema.allow_unknown:raise FrontendContractDenied("unknown view-model field")
 clean:dict[str,object]={}
 for name,field in fields.items():
  if name not in value:
   if field.required:raise FrontendContractDenied("required view-model field missing")
   continue
  item=value[name];valid={"string":isinstance(item,str),"integer":isinstance(item,int) and not isinstance(item,bool),"number":isinstance(item,(int,float)) and not isinstance(item,bool),"boolean":isinstance(item,bool),"string_list":isinstance(item,list) and all(isinstance(entry,str) for entry in item)}[field.kind]
  if not valid:raise FrontendContractDenied("view-model field type mismatch")
  clean[name]=tuple(item) if field.kind=="string_list" else item
 payload={"schema":schema.schema_id,"version":schema.version,"value":clean};digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest();return ValidatedViewModel(schema.schema_id,clean,digest)
def contrast_ratio(foreground:str,background:str)->float:
 def channel(value:int)->float:
  number=value/255;return number/12.92 if number<=.04045 else ((number+.055)/1.055)**2.4
 def luminance(color:str)->float:
  if not re.fullmatch(r"#[0-9a-fA-F]{6}",color):raise FrontendContractDenied("invalid color")
  red,green,blue=(int(color[index:index+2],16) for index in (1,3,5));return .2126*channel(red)+.7152*channel(green)+.0722*channel(blue)
 high,low=sorted((luminance(foreground),luminance(background)),reverse=True);return (high+.05)/(low+.05)
