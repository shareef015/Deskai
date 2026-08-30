export type WorkspaceMode="live"|"synthetic";export type ConnectionState="connecting"|"connected"|"reconnecting"|"offline";export type EventKind="graph"|"interrupt"|"decision"|"terminal"|"error";
export type TimelineItem={cursor:number;eventId:string;kind:EventKind;title:string;summary:string;status:string;occurredAt:string;evidenceCount:number};
export type EvidenceItem={id:string;kind:string;summary:string;source:string;observedAt:string;freshness:"current"|"stale"};
export type InterruptKind="diagnostic_consent"|"remediation_approval"|"employee_confirmation";
export type InterruptView={id:string;kind:InterruptKind;title:string;summary:string;risk:"read_only"|"low"|"medium"|"high";expiresAt:string;checkpointId:string;actionIds:string[];evidenceIds:string[];rollbackAvailable:boolean};
export type WorkspaceState={mode:WorkspaceMode;connection:ConnectionState;incidentId:string;status:string;route:string;lastCursor:number;timeline:TimelineItem[];evidence:EvidenceItem[];interrupt:InterruptView|null;progress:number};
export type SafeRuntimeEvent={event_id:string;cursor:number;event_type:EventKind;fields:Record<string,string|number|boolean|null>;event_sha256:string};
