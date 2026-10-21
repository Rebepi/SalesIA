

export function areQueryKeysDistinct(keyA: readonly unknown[], keyB: readonly unknown[]): boolean {
  if (keyA.length !== keyB.length) return true;
  for (let i = 0;i < keyA.length;i++) {
    if (keyA[i] !== keyB[i]) return true;
  }
  return false;
}
