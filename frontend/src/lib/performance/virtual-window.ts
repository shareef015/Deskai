export interface VirtualWindowInput {
  readonly itemCount: number;
  readonly itemHeight: number;
  readonly viewportHeight: number;
  readonly scrollTop: number;
  readonly overscan?: number;
}

export interface VirtualWindowResult {
  readonly startIndex: number;
  readonly endIndex: number;
  readonly offsetTop: number;
  readonly totalHeight: number;
}

export function calculateVirtualWindow(input: VirtualWindowInput): VirtualWindowResult {
  const overscan = input.overscan ?? 4;
  const safeCount = Math.max(0, input.itemCount);
  const firstVisible = Math.floor(Math.max(0, input.scrollTop) / input.itemHeight);
  const visibleCount = Math.ceil(input.viewportHeight / input.itemHeight);
  const startIndex = Math.max(0, firstVisible - overscan);
  const endIndex = Math.min(safeCount, firstVisible + visibleCount + overscan);
  return {
    startIndex,
    endIndex,
    offsetTop: startIndex * input.itemHeight,
    totalHeight: safeCount * input.itemHeight,
  };
}
