from __future__ import annotations


def jain_fairness_index(allocations: list[float] | tuple[float, ...]) -> float:
    if not allocations:
        raise ValueError("allocations cannot be empty")
    if any(v < 0 for v in allocations):
        raise ValueError("allocations cannot be negative")
    total = sum(allocations)
    squares = sum(v * v for v in allocations)
    if total == 0 or squares == 0:
        return 1.0
    return (total * total) / (len(allocations) * squares)


def enforce_tenant_share(
    requested: dict[str, int], *, total_slots: int, max_share: float = 0.5
) -> dict[str, int]:
    if total_slots < 0:
        raise ValueError("total_slots cannot be negative")
    if not 0 < max_share <= 1:
        raise ValueError("max_share must be in (0, 1]")
    if any(v < 0 for v in requested.values()):
        raise ValueError("requested slots cannot be negative")
    cap = max(1, int(total_slots * max_share)) if total_slots else 0
    allocation = {tenant: min(value, cap) for tenant, value in requested.items()}
    overflow = max(0, sum(allocation.values()) - total_slots)
    if overflow:
        for tenant in sorted(allocation, key=lambda key: allocation[key], reverse=True):
            if overflow == 0:
                break
            reducible = min(allocation[tenant], overflow)
            allocation[tenant] -= reducible
            overflow -= reducible
    return allocation
