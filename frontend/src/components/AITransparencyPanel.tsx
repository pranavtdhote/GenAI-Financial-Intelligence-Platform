"use client";

interface AITransparencyPanelProps {
    data: {
        extracted_source_count: number;
        validation_status: "verified" | "check_needed";
        llm_model: string;
        processing_time: string;
    };
}

export default function AITransparencyPanel({ data }: AITransparencyPanelProps) {
    return (
        <div className="glass-card p-4 text-xs text-muted-foreground flex flex-wrap gap-6 items-center justify-between border-dashed">
            <div className="flex items-center gap-2">
                <span className="font-semibold text-foreground">AI Transparency:</span>
                <span>Groq Llama-3 70B (Versatile)</span>
            </div>

            <div className="flex gap-4">
                <div className="flex flex-col">
                    <span className="uppercase text-[10px] font-bold tracking-wider opacity-70">Source Data</span>
                    <span>{data.extracted_source_count} Data Points Extracted</span>
                </div>

                <div className="flex flex-col">
                    <span className="uppercase text-[10px] font-bold tracking-wider opacity-70">Hallucination Guard</span>
                    <span className={`font-medium ${data.validation_status === 'verified' ? 'text-positive' : 'text-warning'}`}>
                        {data.validation_status === 'verified' ? '✔ active & verified' : '⚠ flagged inconsistencies'}
                    </span>
                </div>

                <div className="flex flex-col">
                    <span className="uppercase text-[10px] font-bold tracking-wider opacity-70">Latency</span>
                    <span>{data.processing_time}</span>
                </div>
            </div>
        </div>
    );
}
