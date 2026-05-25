export function Sparkline({ points, width = 120, height = 36, stroke = "#58A6FF" }: { points: number[]; width?: number; height?: number; stroke?: string }) {
  if (!points || points.length === 0) return <svg width={width} height={height} />;

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const step = width / (points.length - 1);

  const coords = points.map((p, i) => {
    const x = Math.round(i * step);
    const y = Math.round(height - ((p - min) / range) * height);
    return `${x},${y}`;
  });

  const path = `M${coords.join(" L ")}`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <path d={path} fill="none" stroke={stroke} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default Sparkline;
