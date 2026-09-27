import { fmtCompact } from "../lib/format";
import { PortraitAvatar } from "../v3/PortraitAvatar";

/** The KAIROS skin draws creators as illustrated portraits instead of
 *  initials. Checked at render rather than at module load: the build inlines
 *  the dynamic import of App, which hoists this module's body above the line
 *  in main.tsx that sets the attribute. */
function portraits(): boolean {
  return typeof document !== "undefined" && document.documentElement.dataset.skin === "kairos";
}

/** A stable colour pair per creator, derived from their id.
 *
 * Deterministic so a creator looks the same on every load and in every
 * screenshot. Hues are spread around the wheel and kept off pure red, which
 * belongs to the brand accent. */
function hues(seed: string): [string, string] {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 360;
  const a = (h + 25) % 360;
  const b = (h + 85) % 360;
  return [`hsl(${a} 62% 48%)`, `hsl(${b} 58% 38%)`];
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .map((p) => p[0] ?? "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

/**
 * Real channel art when we have it, a generated mark when we don't.
 *
 * The seeded creators are fictional people, so they get an obviously drawn
 * avatar rather than a stock photograph or a generated face — showing an
 * invented person's "photo" would be the one dishonest pixel in the whole
 * console.
 */
export function Avatar({
  name,
  id,
  src,
  size = 44,
  ring,
}: {
  name: string;
  id: string;
  src?: string | null;
  size?: number;
  ring?: string;
}) {
  if (portraits() && !src) {
    return <PortraitAvatar name={name} id={id} size={size} ring={ring} />;
  }

  const [from, to] = hues(id);
  const style: React.CSSProperties = {
    width: size,
    height: size,
    borderRadius: "50%",
    flexShrink: 0,
    boxShadow: ring ? `0 0 0 2px var(--surface-1), 0 0 0 4px ${ring}` : undefined,
  };

  if (src) {
    return (
      <img
        src={src}
        alt=""
        width={size}
        height={size}
        loading="lazy"
        style={{ ...style, objectFit: "cover" }}
      />
    );
  }

  return (
    <span
      aria-hidden="true"
      title={name}
      className="grid place-items-center font-medium text-white"
      style={{
        ...style,
        background: `linear-gradient(135deg, ${from}, ${to})`,
        fontSize: Math.round(size * 0.34),
        letterSpacing: "0.02em",
      }}
    >
      {initials(name)}
    </span>
  );
}

function duration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function howLongAgo(iso: string): string {
  const days = Math.round((Date.now() - new Date(`${iso}T00:00:00`).getTime()) / 86_400_000);
  if (days < 7) return `${Math.max(days, 1)}d ago`;
  if (days < 60) return `${Math.round(days / 7)}w ago`;
  return `${Math.round(days / 30)}mo ago`;
}

export interface CreatorVideo {
  id: string;
  title: string;
  views: number;
  published_at: string;
  duration_seconds: number;
  thumbnail_url?: string | null;
}

/**
 * One of the creator's actual videos about this trend.
 *
 * These are evidence, not decoration: they are the reason the content-fit
 * score is what it is, so a brand can read the titles and judge for
 * themselves. Real thumbnails arrive in live mode; the seeded world gets a
 * drawn placeholder rather than a borrowed screenshot.
 */
export function VideoCard({ video, seed }: { video: CreatorVideo; seed: string }) {
  const [from, to] = hues(seed + video.id);
  return (
    <article className="w-[164px] shrink-0">
      <div
        className="relative grid aspect-video w-full place-items-center overflow-hidden rounded-lg"
        style={
          video.thumbnail_url
            ? undefined
            : { background: `linear-gradient(135deg, ${from}, ${to})` }
        }
      >
        {video.thumbnail_url ? (
          <img
            src={video.thumbnail_url}
            alt=""
            loading="lazy"
            className="h-full w-full object-cover"
          />
        ) : (
          <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true" opacity="0.9">
            <path d="M21 12 6 21V3z" fill="#fff" />
          </svg>
        )}
        <span
          className="absolute bottom-1 right-1 rounded px-1 py-0.5 text-[10px] font-medium text-white"
          style={{ background: "rgba(0,0,0,0.75)" }}
        >
          {duration(video.duration_seconds)}
        </span>
      </div>
      <h4 className="mt-1.5 line-clamp-2 text-[12px] font-medium leading-snug">{video.title}</h4>
      <p className="mt-0.5 text-[11px] text-muted">
        {fmtCompact(video.views)} views · {howLongAgo(video.published_at)}
      </p>
    </article>
  );
}

export function VideoStrip({
  videos,
  seed,
  label = "What they actually make about this",
}: {
  videos: CreatorVideo[];
  seed: string;
  label?: string;
}) {
  if (!videos.length) return null;
  return (
    <div>
      <div className="mb-2 text-[12px] font-medium text-ink-2">{label}</div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {videos.map((v) => (
          <VideoCard key={v.id} video={v} seed={seed} />
        ))}
      </div>
    </div>
  );
}
