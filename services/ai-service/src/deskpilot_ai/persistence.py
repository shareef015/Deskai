from __future__ import annotations

import hashlib
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any,AsyncIterator,Mapping

THREAD_NAMESPACE=uuid.UUID("84cbdb17-2e9a-5afd-8475-7e7d13014bee")
MAX_CHECKPOINT_BYTES=2_097_152;MAX_HISTORY_ITEMS=500;LEASE_SECONDS=60
TERMINAL_STATES=frozenset({"completed","failed","cancelled"})

class CheckpointConflict(RuntimeError):pass
class CheckpointScopeError(ValueError):pass

@dataclass(frozen=True,slots=True)
class ThreadScope:
 tenant_id:str
 incident_id:str
 run_id:str
 configuration_fingerprint:str
 def __post_init__(self)->None:
  for value in (self.tenant_id,self.incident_id,self.run_id):
   try:uuid.UUID(value)
   except (ValueError,TypeError) as exc:raise CheckpointScopeError("tenant, incident and run ids must be UUIDs") from exc
  if len(self.configuration_fingerprint)!=64 or any(c not in "0123456789abcdef" for c in self.configuration_fingerprint):raise CheckpointScopeError("configuration fingerprint must be sha256")
 @property
 def thread_id(self)->str:return str(uuid.uuid5(THREAD_NAMESPACE,f"{self.tenant_id}:{self.incident_id}:{self.run_id}"))

def checkpoint_config(scope:ThreadScope,*,checkpoint_id:str|None=None,checkpoint_ns:str="")->dict[str,dict[str,str]]:
 configurable={"thread_id":scope.thread_id,"checkpoint_ns":checkpoint_ns,"tenant_id":scope.tenant_id,"incident_id":scope.incident_id,"run_id":scope.run_id,"configuration_fingerprint":scope.configuration_fingerprint}
 if checkpoint_id is not None:configurable["checkpoint_id"]=checkpoint_id
 return {"configurable":configurable}

def state_digest(payload:bytes)->str:
 if len(payload)>MAX_CHECKPOINT_BYTES:raise ValueError("checkpoint payload exceeds policy")
 return hashlib.sha256(payload).hexdigest()

@dataclass(frozen=True,slots=True)
class CheckpointHead:
 checkpoint_id:str|None
 version:int
 state_version:str
 state_sha256:str|None

def advance_head(current:CheckpointHead,*,expected_checkpoint_id:str|None,new_checkpoint_id:str,state_version:str,state_payload:bytes)->CheckpointHead:
 if current.checkpoint_id!=expected_checkpoint_id:raise CheckpointConflict("expected checkpoint does not match current head")
 if not new_checkpoint_id or new_checkpoint_id==current.checkpoint_id:raise CheckpointConflict("new checkpoint id must advance")
 if state_version!="1.0.0":raise ValueError("unsupported graph state version")
 return CheckpointHead(new_checkpoint_id,current.version+1,state_version,state_digest(state_payload))

def assert_resume_scope(requested:ThreadScope,stored:Mapping[str,str])->None:
 checks={"tenant_id":requested.tenant_id,"incident_id":requested.incident_id,"run_id":requested.run_id,"configuration_fingerprint":requested.configuration_fingerprint,"thread_id":requested.thread_id}
 if any(stored.get(key)!=value for key,value in checks.items()):raise CheckpointScopeError("checkpoint resume scope mismatch")

def cleanup_eligible(*,status:str,legal_hold:bool,delete_after_reached:bool)->bool:return status in TERMINAL_STATES and not legal_hold and delete_after_reached

@asynccontextmanager
async def open_async_postgres_checkpointer(*,dsn:str,encryption_key:bytes,run_setup:bool=False)->AsyncIterator[Any]:
 if not dsn.startswith(("postgresql://","postgresql+psycopg://")):raise ValueError("PostgreSQL DSN required")
 if len(encryption_key) not in {16,24,32}:raise ValueError("AES key must be 16, 24 or 32 bytes")
 from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
 from langgraph.checkpoint.serde.encrypted import EncryptedSerializer
 serde=EncryptedSerializer.from_pycryptodome_aes(key=encryption_key)
 async with AsyncPostgresSaver.from_conn_string(dsn,serde=serde) as saver:
  if run_setup:await saver.setup()
  yield saver
