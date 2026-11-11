export function Stick({ pose = "wave" }: { pose?: "wave" | "flex" | "celebrate" | "coach" }) {
  const arms =
    pose === "flex"
      ? "M40 58 l-22 -6 m44 0 l22 -6"
      : pose === "celebrate"
        ? "M40 58 l-18 -22 m44 0 l18 -22"
        : pose === "coach"
          ? "M40 58 l-16 10 m44 0 l20 -18"
          : "M40 58 l-16 4 m44 0 l18 -16";
  return (
    <svg viewBox="0 0 80 110" width="92" height="120" aria-hidden>
      <circle cx="52" cy="22" r="12" fill="none" stroke="#111" strokeWidth="3" />
      <path d="M52 34 v28" fill="none" stroke="#111" strokeWidth="3" strokeLinecap="round" />
      <path d={arms} fill="none" stroke="#111" strokeWidth="3" strokeLinecap="round" />
      <path d="M52 62 l-12 36 M52 62 l12 36" fill="none" stroke="#111" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function StatusBar() {
  return (
    <div className="status">
      <span>9:41</span>
      <span className="icons">●●● ︎☾</span>
    </div>
  );
}

export function MuscleMap({ active }: { active: string[] }) {
  const on = (name: string) => (active.includes(name) ? "#111" : "#d8d8d8");
  return (
    <div className="muscle-wrap">
      <svg viewBox="0 0 120 260" aria-label="Front muscles">
        <text x="60" y="16" textAnchor="middle" fontSize="11">FRONT</text>
        <circle cx="60" cy="36" r="12" fill="none" stroke="#111" strokeWidth="2" />
        <rect x="48" y="48" width="24" height="18" rx="6" fill="none" stroke="#111" strokeWidth="2" />
        <ellipse cx="44" cy="78" rx="14" ry="16" fill={on("chest")} />
        <ellipse cx="76" cy="78" rx="14" ry="16" fill={on("chest")} />
        <ellipse cx="28" cy="78" rx="8" ry="14" fill={on("shoulders")} />
        <ellipse cx="92" cy="78" rx="8" ry="14" fill={on("shoulders")} />
        <ellipse cx="22" cy="108" rx="7" ry="16" fill={on("biceps")} />
        <ellipse cx="98" cy="108" rx="7" ry="16" fill={on("biceps")} />
        <ellipse cx="60" cy="118" rx="16" ry="18" fill={on("core")} />
        <ellipse cx="46" cy="168" rx="12" ry="28" fill={on("quads")} />
        <ellipse cx="74" cy="168" rx="12" ry="28" fill={on("quads")} />
        <ellipse cx="46" cy="214" rx="8" ry="18" fill={on("calves")} />
        <ellipse cx="74" cy="214" rx="8" ry="18" fill={on("calves")} />
      </svg>
      <svg viewBox="0 0 120 260" aria-label="Back muscles">
        <text x="60" y="16" textAnchor="middle" fontSize="11">BACK</text>
        <circle cx="60" cy="36" r="12" fill="none" stroke="#111" strokeWidth="2" />
        <rect x="48" y="48" width="24" height="18" rx="6" fill="none" stroke="#111" strokeWidth="2" />
        <ellipse cx="38" cy="82" rx="14" ry="20" fill={on("lats")} />
        <ellipse cx="82" cy="82" rx="14" ry="20" fill={on("lats")} />
        <ellipse cx="60" cy="86" rx="12" ry="16" fill={on("upper_back")} />
        <ellipse cx="60" cy="58" rx="10" ry="8" fill={on("traps")} />
        <ellipse cx="22" cy="108" rx="7" ry="16" fill={on("triceps")} />
        <ellipse cx="98" cy="108" rx="7" ry="16" fill={on("triceps")} />
        <ellipse cx="46" cy="150" rx="12" ry="14" fill={on("glutes")} />
        <ellipse cx="74" cy="150" rx="12" ry="14" fill={on("glutes")} />
        <ellipse cx="46" cy="186" rx="10" ry="22" fill={on("hamstrings")} />
        <ellipse cx="74" cy="186" rx="10" ry="22" fill={on("hamstrings")} />
        <ellipse cx="46" cy="222" rx="8" ry="16" fill={on("calves")} />
        <ellipse cx="74" cy="222" rx="8" ry="16" fill={on("calves")} />
      </svg>
    </div>
  );
}
