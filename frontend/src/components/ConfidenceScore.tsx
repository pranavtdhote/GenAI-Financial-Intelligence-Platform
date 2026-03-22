"use client";

interface ConfidenceScoreProps {
  score: number;
}

export default function ConfidenceScore({ score }: ConfidenceScoreProps) {
  const pct = Math.round(score * 100);

  // Circumference for SVG circle
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (pct / 100) * circumference;

  const color =
    pct >= 70 ? "text-positive" : pct >= 40 ? "text-warning" : "text-negative";
  const strokeColor =
    pct >= 70 ? "var(--positive)" : pct >= 40 ? "var(--warning)" : "var(--negative)";

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative h-32 w-32">
        {/* Background Circle */}
        <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="currentColor"
            strokeWidth="8"
            className="text-slate-100 dark:text-slate-800"
          />
          {/* Progress Circle */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke={strokeColor}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-2xl font-bold ${color} animate-count-up`}>
            {pct}%
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-light">
            Confidence
          </span>
        </div>
      </div>

      <div className="mt-4 flex flex-col items-center gap-2">
        <div className={`badge ${pct >= 80 ? 'badge-positive' : pct >= 50 ? 'badge-warning' : 'badge-negative'
          }`}>
          {pct >= 90 ? "High Fidelity" : pct >= 70 ? "Verified" : "Check Sources"}
        </div>

        <div className="text-xs text-muted text-center max-w-[140px]">
          Validating against {pct >= 80 ? "all 3" : "2"} financial documents
        </div>
      </div>
    </div>
  );
}
