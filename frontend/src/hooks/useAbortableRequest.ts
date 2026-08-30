"use client";

import { useCallback, useEffect, useRef } from "react";

export function useAbortableRequest(): {
  nextSignal: () => AbortSignal;
  cancel: () => void;
} {
  const controllerRef = useRef<AbortController | null>(null);
  const cancel = useCallback(() => {
    controllerRef.current?.abort(new DOMException("Request cancelled", "AbortError"));
    controllerRef.current = null;
  }, []);
  const nextSignal = useCallback(() => {
    cancel();
    const controller = new AbortController();
    controllerRef.current = controller;
    return controller.signal;
  }, [cancel]);
  useEffect(() => cancel, [cancel]);
  return { nextSignal, cancel };
}
