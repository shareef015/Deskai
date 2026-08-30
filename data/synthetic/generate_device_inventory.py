from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ENDPOINTS=ROOT/"data/synthetic/endpoints.json"
DESTINATION=Path(__file__).with_name("device-inventory.json")

def _inventory(endpoint: dict, index: int)->dict:
    classic=endpoint["installed_software"]["outlook_client"]=="classic"
    apps=[
        {"id":"m365-apps","name":"Microsoft 365 Apps","version":f"16.0.{18000+index}.10000","architecture":"x64","channel":"current_enterprise","health":"healthy"},
        {"id":"outlook","name":"Microsoft Outlook","version":f"1.2026.{800+index}" if not classic else f"16.0.{18000+index}.10000","architecture":"x64","variant":"new" if not classic else "classic","health":"healthy"},
        {"id":"edge","name":"Microsoft Edge","version":f"140.0.{3000+index}.0","architecture":"x64","health":"healthy"},
        {"id":"deskpilot-agent","name":"DeskPilot Windows Agent","version":"1.0.0-synthetic","architecture":"x64","health":"healthy"}
    ]
    services=[
        {"name":"RpcSs","display_name":"Remote Procedure Call","startup":"automatic","expected":"running","observed":"running","dependencies":[]},
        {"name":"EventLog","display_name":"Windows Event Log","startup":"automatic","expected":"running","observed":"running","dependencies":["RpcSs"]},
        {"name":"Spooler","display_name":"Print Spooler","startup":"automatic","expected":"running","observed":"running","dependencies":["RpcSs"]},
        {"name":"stisvc","display_name":"Windows Image Acquisition","startup":"manual_trigger","expected":"running_on_demand","observed":"stopped_idle","dependencies":["RpcSs"]},
        {"name":"Dnscache","display_name":"DNS Client","startup":"automatic","expected":"running","observed":"running","dependencies":["RpcSs"]}
    ]
    drivers=[
        {"id":"net-adapter","class":"network","provider":"Fabrikam","version":f"12.4.{index}.1","signed":True,"status":"healthy"},
        {"id":"print-class","class":"printer","provider":"Microsoft","version":"10.0.26100.1" if endpoint["operating_system"]=="windows_11" else "10.0.19041.1","signed":True,"status":"healthy"},
        {"id":"wia-class","class":"image","provider":"Microsoft","version":"10.0.26100.1" if endpoint["operating_system"]=="windows_11" else "10.0.19041.1","signed":True,"status":"healthy"}
    ]
    peripherals=[
        {"id":f"per-printer-{(index%3)+1}","type":"printer","connection":"tcp_ip" if index%2==0 else "print_server","status":"ready","synthetic":True},
        {"id":f"per-scanner-{(index%2)+1}","type":"scanner","connection":"usb" if index%2==0 else "network","status":"ready","synthetic":True}
    ]
    dependencies=[
        {"consumer":"outlook","requires":["Dnscache","network:internet","identity:m365"]},
        {"consumer":"printing","requires":["Spooler","RpcSs","driver:print-class"]},
        {"consumer":"scanning","requires":["stisvc","RpcSs","driver:wia-class"]},
        {"consumer":"deskpilot-agent","requires":["EventLog","network:private-api","device:certificate"]}
    ]
    return {"endpoint_id":endpoint["id"],"hostname":endpoint["hostname"],"tenant_id":endpoint["tenant_id"],"applications":apps,"services":services,"drivers":drivers,"peripherals":peripherals,"dependencies":dependencies,"health_baseline":{"inventory_complete":True,"unsigned_driver_count":0,"unhealthy_application_count":0,"failed_service_count":0,"missing_peripheral_count":0}}

def build()->dict:
    endpoints=json.loads(ENDPOINTS.read_text(encoding="utf-8"))["endpoints"]
    return {"schema_version":"1.0.0","synthetic_only":True,"seed":45001,"tenant_id":"tenant-demo-kw","inventories":[_inventory(endpoint,index) for index,endpoint in enumerate(endpoints)]}
def canonical_bytes()->bytes: return (json.dumps(build(),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
if __name__=="__main__": DESTINATION.write_bytes(canonical_bytes()); print(DESTINATION)
