interface FlagImgProps {
  code: string;
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function FlagImg({ code, size = 24, className, style }: FlagImgProps) {
  if (!code) return null;

  const flagCode = code.toLowerCase();
  const src = `https://flagcdn.com/w40/${flagCode}.png`;

  return (
    <img
      src={src}
      alt={`${code} flag`}
      width={size}
      height={Math.round(size * 0.75)}
      className={className}
      style={{ width: size, height: Math.round(size * 0.75), objectFit: "cover", display: "inline-block", ...style }}
      loading="lazy"
      onError={(event) => {
        (event.currentTarget as HTMLImageElement).style.display = "none";
      }}
    />
  );
}