from __future__ import annotations
import hashlib, json
from pathlib import Path
from uuid import UUID, uuid5

DESTINATION=Path(__file__).with_name("endpoints.json")
NAMESPACE=UUID("8be9ad56-804f-530a-a778-c86cb670bafd")
USERS=["usr-002","usr-004","usr-006","usr-008","usr-010","usr-001","usr-003","usr-005","usr-007","usr-009"]
SCENARIOS=["outlook_disconnected","outlook_corrupt_ost","stuck_print_queue","print_spooler_failure","lifecycle_esu_warning","outlook_addin_crash","outlook_authentication_loop","incorrect_printer_tcpip_port","wia_scanner_failure","vpn_dns_connectivity"]

def _endpoint(index: int) -> dict:
    win10=index<5; ordinal=index+1 if win10 else index-4; hostname=f"WIN{'10' if win10 else '11'}-{ordinal:02d}"
    esu=win10 and index<4; lifecycle="restricted" if win10 and not esu else "active"
    return {"id":str(uuid5(NAMESPACE,hostname)),"tenant_id":"tenant-demo-kw","hostname":hostname,"operating_system":"windows_10" if win10 else "windows_11","edition":"Enterprise","release":"22H2" if win10 else ("24H2" if ordinal<=3 else "25H2"),"build":"19045.6456" if win10 else ("26100.6584" if ordinal<=3 else "26200.6584"),"architecture":"x64","lifecycle_status":lifecycle,"support_entitlement":"enterprise_esu" if esu else ("none" if win10 else "standard_servicing"),"primary_user_id":USERS[index],"location_id":"loc-warehouse" if index==4 else ("loc-branch" if index in {3,7} else "loc-hq"),"serial_fingerprint":hashlib.sha256(f"synthetic-serial:{hostname}".encode()).hexdigest(),"hardware":{"manufacturer":"Fabrikam","model":f"DeskPro-{100+index}","cpu_cores":4+(index%3)*2,"memory_gb":8+(index%3)*8,"disk_gb":256+(index%2)*256,"tpm_version":"2.0","secure_boot":True},"installed_software":{"microsoft_365_apps":"current_enterprise_channel","outlook_client":"classic" if index%2==0 else "new","deskpilot_agent":"1.0.0-synthetic","windows_security":"platform"},"security_posture":{"disk_encryption":"enabled","antimalware":"healthy","firewall":"managed","local_admin_user":False},"baseline_health":{"agent_connected":True,"cpu_percent":12+index,"memory_percent":38+index,"disk_free_percent":42-index,"pending_restart":index in {2,8}},"primary_scenario":SCENARIOS[index]}

def build()->dict: return {"schema_version":"1.0.0","synthetic_only":True,"seed":44001,"tenant_id":"tenant-demo-kw","endpoints":[_endpoint(i) for i in range(10)]}
def canonical_bytes()->bytes: return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__": DESTINATION.write_bytes(canonical_bytes()); print(DESTINATION)
