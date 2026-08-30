const TOKEN_KEY_PATTERN = /(access|refresh|id)[_-]?token|bearer|authorization|session/i;

export function assertNoTokenPersistence(storage: Storage): void {
  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (key && TOKEN_KEY_PATTERN.test(key)) throw new Error(`Sensitive credential must not be stored in browser storage: ${key}`);
  }
}

export function isCredentialLike(value: string): boolean {
  return /^Bearer\s+/i.test(value) || /^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\./.test(value);
}
