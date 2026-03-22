"use client";

import { useCallback, useState, useEffect } from "react";

interface UploadZoneProps {
  onProcess: (file: File) => Promise<void>;
  isProcessing: boolean;
}

export default function UploadZone({ onProcess, isProcessing }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState<"upload" | "extract" | "analyze" | "graph">("upload");

  // Simulate progress steps when processing
  useEffect(() => {
    if (!isProcessing) {
      setProgress(0);
      setStep("upload");
      return;
    }

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) return prev;
        const inc = Math.random() * 5;
        const newProgress = prev + inc;

        // Update step based on progress
        if (newProgress < 30) setStep("extract");
        else if (newProgress < 70) setStep("analyze");
        else setStep("graph");

        return newProgress;
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isProcessing]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file?.type === "application/pdf") onProcess(file);
    },
    [onProcess]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onProcess(file);
    },
    [onProcess]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`
        relative overflow-hidden rounded-2xl border-2 border-dashed transition-all duration-300
        glass-card min-h-[300px] flex flex-col items-center justify-center p-12 text-center
        ${isDragging
          ? "border-primary bg-primary/5 scale-[1.02]"
          : "border-slate-300 dark:border-slate-700 hover:border-primary/50 dark:hover:border-primary/50"
        }
      `}
    >
      <input
        type="file"
        accept=".pdf"
        onChange={handleFileChange}
        disabled={isProcessing}
        className="absolute inset-0 cursor-pointer opacity-0 z-20"
      />

      {/* Decorative gradient blob */}
      <div className="absolute -top-20 -right-20 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

      {isProcessing ? (
        <div className="z-10 w-full max-w-md space-y-8 animate-fade-in">
          {/* Progress Circle */}
          <div className="relative mx-auto h-24 w-24">
            <svg className="h-full w-full -rotate-90 text-slate-200 dark:text-slate-700" viewBox="0 0 36 36">
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="var(--primary)" />
                  <stop offset="100%" stopColor="var(--accent)" />
                </linearGradient>
              </defs>
              <path strokeWidth="3" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" />
              <path strokeWidth="3" strokeDasharray={`${progress}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="url(#gradient)" className="transition-all duration-500 ease-out" />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-bold text-foreground">{Math.round(progress)}%</span>
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-xl font-semibold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent animate-pulse">
              Processing Financial Report
            </h3>
            <p className="text-sm text-muted">
              {step === "extract" && "Extracting text and tables..."}
              {step === "analyze" && "Analyzing financial metrics..."}
              {step === "graph" && "Building knowledge graph..."}
            </p>
          </div>

          <div className="flex justify-center gap-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className={`h-2 w-2 rounded-full transition-colors duration-300 ${(step === "extract" && i === 1) || (step === "analyze" && i <= 2) || (step === "graph" && i <= 3)
                  ? "bg-primary"
                  : "bg-slate-200 dark:bg-slate-700"
                  }`}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="z-10 flex flex-col items-center space-y-6 animate-slide-up">
          <div className="relative group">
            <div className={`
              absolute inset-0 bg-primary/20 rounded-full blur-xl transition-all duration-300
              ${isDragging ? "scale-125 opacity-100" : "scale-100 opacity-0 group-hover:opacity-100"}
            `} />
            <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-surface shadow-sm ring-1 ring-slate-900/5 dark:ring-slate-100/10">
              <svg className="h-10 w-10 text-primary transition-transform duration-300 group-hover:-translate-y-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="text-2xl font-bold tracking-tight text-foreground">
              Financial Report Analysis
            </h3>
            <p className="text-muted max-w-sm mx-auto">
              Drop your PDF report here to generate investor-grade insights,
              risk analysis, and predictive models.
            </p>
          </div>

          <div className="flex gap-3 text-xs font-medium text-muted-light uppercase tracking-wider">
            <span className="bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">10-K / 10-Q</span>
            <span className="bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">Annual Reports</span>
            <span className="bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">Financial Statements</span>
          </div>
        </div>
      )}
    </div>
  );
}
