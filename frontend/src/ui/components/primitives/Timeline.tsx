import React from "react";

export interface TimelineEvent {
  id: string;
  timestamp: string;
  sequenceNumber: number;
  actor: string;
  timezone: string;
  type: "operational" | "note";
  title: string;
  description: string;
}

export const Timeline: React.FC<{ events: TimelineEvent[] }> = ({ events }) => {
  const sorted = events.slice().sort((a, b) => {
    const timeDiff = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
    if (timeDiff !== 0) return timeDiff;
    return a.sequenceNumber - b.sequenceNumber;
  });

  return (
    <ol className="relative border-l border-slate-800 ml-3 space-y-4 my-2">
      {sorted.map((ev) => {
        const isOp = ev.type === "operational";
        return (
          <li key={ev.id} className="ml-6 text-left">
            <span
              className={`absolute -left-2.5 flex items-center justify-center w-5 h-5 rounded-full ring-4 ring-slate-900 ${isOp ? "bg-blue-600" : "bg-amber-600"
                }`}
            />
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white">{ev.title}</span>
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${isOp
                  ? "bg-blue-950 text-blue-300 border-blue-800"
                  : "bg-amber-950 text-amber-300 border-amber-800"
                  }`}
              >
                {isOp ? "Operativo" : "Nota"}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">{ev.description}</p>
            <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-1">
              <span>{ev.actor}</span>
              <span>·</span>
              <span>{ev.timestamp}</span>
              <span>·</span>
              <span>{ev.timezone}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
};
