import { useId } from "react";

/** Illustrated portraits for the seeded creators.
 *
 * These are drawn, not photographed and not generated from a face model. The
 * creators are invented, so a photoreal face would put a picture of a person
 * who does not exist next to a real-looking subscriber count and fee — the one
 * dishonest pixel in an otherwise honest console. A flat illustration reads as
 * a profile picture at 44px without claiming to be a photograph of anyone.
 *
 * Every choice below is derived from the creator's id, so a creator looks the
 * same on every load, in every screenshot and on every machine. Nothing is
 * inferred from their name: features are assigned by hash, because guessing
 * someone's appearance from their name would be worse than assigning it at
 * random.
 */

const SKIN_TONES = [
  "#f3d5bb",
  "#ebc19c",
  "#dda878",
  "#c68c5e",
  "#a06e48",
  "#7d5436",
  "#5d3d28",
];

const HAIR = [
  "#1f1a17",
  "#332723",
  "#4d382a",
  "#6b4a2f",
  "#9a6434",
  "#c28b3c",
  "#8e8d8a",
  "#2b2b2f",
];

const TOPS = ["#37474f", "#455a64", "#4e5d4a", "#5b4a52", "#3f4d63", "#6b5745", "#41564f"];

const BACKDROPS = [
  "#dbe6f3",
  "#e6e0f0",
  "#dcece2",
  "#f2e3da",
  "#e9e4d6",
  "#dde8ea",
  "#efdfe2",
];

/** FNV-style mix, then a few independent draws from it. */
function draws(seed: string, n: number): number[] {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    h ^= h << 13;
    h ^= h >>> 17;
    h ^= h << 5;
    out.push(Math.abs(h));
  }
  return out;
}

/** Hair mass and hairline per style. The cap is one ellipse clipped to sit
 *  above a hairline, which is far more reliable across styles than hand-drawn
 *  outlines — volume and fringe length are the two things that actually
 *  distinguish them at this size. */
const STYLES = [
  { rx: 17.8, ry: 19.8, cy: 36, line: 30, back: false, bun: false }, // short
  { rx: 18.4, ry: 20.4, cy: 36, line: 34, back: false, bun: false }, // fringe
  { rx: 21.5, ry: 21, cy: 33, line: 40, back: false, bun: false }, // full curls
  { rx: 18.4, ry: 20.2, cy: 36, line: 33, back: true, bun: false }, // long
  { rx: 17.6, ry: 19.6, cy: 36, line: 28, back: false, bun: true }, // tied up
  { rx: 17.2, ry: 19.2, cy: 36.5, line: 26, back: false, bun: false }, // close crop
];

export function PortraitAvatar({
  name,
  id,
  size = 44,
  ring,
}: {
  name: string;
  id: string;
  size?: number;
  ring?: string;
}) {
  const uid = useId().replace(/:/g, "");
  const [a, b, c, d, e, f] = draws(id, 6);

  const skin = SKIN_TONES[a % SKIN_TONES.length];
  const hair = HAIR[b % HAIR.length];
  const top = TOPS[c % TOPS.length];
  const backdrop = BACKDROPS[d % BACKDROPS.length];
  const style = STYLES[e % STYLES.length];
  const glasses = f % 5 === 0;
  const beard = f % 7 === 0;

  return (
    <span
      aria-hidden="true"
      title={name}
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        flexShrink: 0,
        overflow: "hidden",
        display: "block",
        boxShadow: ring ? `0 0 0 2px var(--surface-1), 0 0 0 4px ${ring}` : undefined,
      }}
    >
      <svg width={size} height={size} viewBox="0 0 80 80" role="presentation">
        <defs>
          <clipPath id={`${uid}-top`}>
            <rect x="0" y="0" width="80" height={style.line} />
          </clipPath>
          <clipPath id={`${uid}-chin`}>
            <rect x="0" y="40" width="80" height="40" />
          </clipPath>
        </defs>

        <rect width="80" height="80" fill={backdrop} />

        {/* hair that falls behind the shoulders */}
        {style.back && <ellipse cx="40" cy="44" rx="22" ry="25" fill={hair} />}
        {style.bun && <circle cx="40" cy="13" r="6.5" fill={hair} />}

        {/* shoulders */}
        <ellipse cx="40" cy="88" rx="27" ry="21" fill={top} />
        {/* neck, shaded so the head reads as in front of it */}
        <rect x="34" y="46" width="12" height="14" rx="5" fill={skin} />
        <rect x="34" y="46" width="12" height="7" rx="3" fill="#000" opacity="0.12" />

        <ellipse cx="40" cy="36" rx="17" ry="19" fill={skin} />
        <circle cx="22.5" cy="38" r="3.4" fill={skin} />
        <circle cx="57.5" cy="38" r="3.4" fill={skin} />

        {beard && (
          <ellipse
            cx="40"
            cy="40"
            rx="17"
            ry="19"
            fill={hair}
            opacity="0.85"
            clipPath={`url(#${uid}-chin)`}
          />
        )}

        <ellipse
          cx="40"
          cy={style.cy}
          rx={style.rx}
          ry={style.ry}
          fill={hair}
          clipPath={`url(#${uid}-top)`}
        />

        <ellipse cx="33.5" cy="37" rx="1.7" ry="2.1" fill="#2b2320" />
        <ellipse cx="46.5" cy="37" rx="1.7" ry="2.1" fill="#2b2320" />
        <path
          d="M36 44.5c1.4 1.5 6.6 1.5 8 0"
          stroke="#2b2320"
          strokeOpacity="0.55"
          strokeWidth="1.4"
          strokeLinecap="round"
          fill="none"
        />

        {glasses && (
          <g stroke="#2b2320" strokeOpacity="0.8" strokeWidth="1.3" fill="none">
            <circle cx="33.5" cy="37" r="5.4" />
            <circle cx="46.5" cy="37" r="5.4" />
            <path d="M38.9 37h2.2" />
          </g>
        )}
      </svg>
    </span>
  );
}
