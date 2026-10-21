

export function calculateValidPageAfterDeletion(
  currentPage: number,
  itemsOnCurrentPage: number,
  totalItems: number,
  pageSize: number
): number {
  if (itemsOnCurrentPage === 1 && currentPage > 1) {
    return currentPage - 1;
  }
  const newTotal = Math.max(0, totalItems - 1);
  const maxPage = Math.max(1, Math.ceil(newTotal / pageSize));
  return Math.min(currentPage, maxPage);
}
