export function formatMatchTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();

  const isToday =
    date.getDate() === now.getDate() &&
    date.getMonth() === now.getMonth() &&
    date.getFullYear() === now.getFullYear();

  const timeStr = date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  if (isToday) {
    return `Today · ${timeStr}`;
  }

  const dateStr = date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
  });

  return `${dateStr} · ${timeStr}`;
}