const widths = [320, 640, 960, 1440, 1920] as const;

function mediaUrl(assetId: string, width: number, representation: "webp" | "fallback") {
  return `/api/v1/media/${encodeURIComponent(assetId)}/${width}?representation=${representation}`;
}

export function ResponsiveMediaImage({
  alt,
  assetId,
  className,
  eager = false,
  sizes = "100vw",
}: {
  alt: string;
  assetId: string;
  className?: string;
  eager?: boolean;
  sizes?: string;
}) {
  const webp = widths.map((width) => `${mediaUrl(assetId, width, "webp")} ${width}w`).join(", ");
  const fallback = widths
    .map((width) => `${mediaUrl(assetId, width, "fallback")} ${width}w`)
    .join(", ");
  return (
    <picture className={className}>
      <source sizes={sizes} srcSet={webp} type="image/webp" />
      {/* Dimensions reserve a stable ratio; CSS may constrain the final presentation. */}
      <img
        alt={alt}
        decoding="async"
        fetchPriority={eager ? "high" : "auto"}
        height={960}
        loading={eager ? "eager" : "lazy"}
        sizes={sizes}
        src={mediaUrl(assetId, 960, "fallback")}
        srcSet={fallback}
        width={960}
      />
    </picture>
  );
}
