export type Capability =
  | "incident:read"
  | "incident:update"
  | "diagnostic:run"
  | "remediation:request"
  | "remediation:approve"
  | "admin:manage";

export interface Principal {
  readonly userId: string;
  readonly tenantId: string;
  readonly capabilities: ReadonlySet<Capability>;
}

export interface ResourceScope {
  readonly tenantId: string;
  readonly required: Capability;
}

export function canAccess(principal: Principal | null, resource: ResourceScope): boolean {
  return Boolean(principal && principal.tenantId === resource.tenantId && principal.capabilities.has(resource.required));
}

export function requireAccess(principal: Principal | null, resource: ResourceScope): void {
  if (!canAccess(principal, resource)) throw new Error("Frontend authorization guard denied access");
}
