"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Dashboard", icon: "M3 12l9-9 9 9M5 10v10h14V10" },
  { href: "/jobs", label: "Jobs", icon: "M9 6h6m-9 4h12a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2v-6a2 2 0 012-2zm3 8h6" },
  { href: "/candidates", label: "Candidates", icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
  { href: "/matching", label: "Matching", icon: "M8 7h8M8 12h5m-5 5h8M4 4h16v16H4z" },
  { href: "/pipeline", label: "Pipeline", icon: "M4 6h16M4 12h10M4 18h7" },
  { href: "/screening", label: "Screening", icon: "M8 10h8m-8 4h5M9 20l-4-2V6a2 2 0 012-2h10a2 2 0 012 2v12l-4 2z" },
  { href: "/health", label: "System Health", icon: "M3 12h4l2-6 4 12 2-6h6" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col bg-slate-900 text-slate-100">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex size-8 items-center justify-center rounded-lg bg-indigo-500 text-sm font-bold text-white">
          TF
        </div>
        <div>
          <p className="text-sm font-semibold leading-tight">TalentFlow AI</p>
          <p className="text-[11px] leading-tight text-slate-400">Hiring pipeline</p>
        </div>
      </div>

      <nav className="mt-2 flex-1 space-y-0.5 px-3" aria-label="Main">
        {NAV.map((item) => {
          const active =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-slate-800 font-medium text-white"
                  : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
              }`}
            >
              <svg
                aria-hidden
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="size-4.5"
              >
                <path d={item.icon} />
              </svg>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 px-5 py-4">
        <p className="text-[11px] leading-relaxed text-slate-400">
          Open-source demo · synthetic data only. AI assists — <span className="text-slate-300">recruiters decide</span>.
        </p>
      </div>
    </aside>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="scroll-thin flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-8 py-8">{children}</div>
      </main>
    </div>
  );
}
