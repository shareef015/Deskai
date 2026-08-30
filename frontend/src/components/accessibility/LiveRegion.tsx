type LiveRegionProps = {
  message: string;
  urgent?: boolean;
};

export function LiveRegion({ message, urgent = false }: LiveRegionProps) {
  if (!message) return null;
  return urgent ? (
    <div role="alert">{message}</div>
  ) : (
    <div role="status" aria-live="polite" aria-atomic="true">
      {message}
    </div>
  );
}
