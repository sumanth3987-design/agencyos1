import React, { useState } from 'react';
import { ShieldCheck, AlertTriangle, Scale, CheckCircle2, XCircle, ArrowUpRight, Search, FileText } from 'lucide-react';
import { Project } from '../types';

interface AdminConsoleProps {
  projects: Project[];
}

export const AdminConsole: React.FC<AdminConsoleProps> = ({ projects }) => {
  const [resolvedDispute, setResolvedDispute] = useState<string | null>(null);

  const handleResolveDispute = (outcome: string) => {
    setResolvedDispute(outcome);
  };

  return (
    <div className="space-y-6">
      
      {/* Admin Security Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
              Platform Arbitration & Security Officer
            </span>
          </div>
          <h1 className="text-xl font-bold text-white">Trust, Escrow & Compliance Overseer</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Supervise legal contract adherence, manage milestone escrow vaults, and arbitrate formal SOW disputes.
          </p>
        </div>

        <div className="flex items-center gap-3 bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-xs">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-slate-300">Escrow Security: <strong>Dual-Signature Vault Active</strong></span>
        </div>
      </div>

      {/* Live Dispute Resolution Room */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-white">Arbitration Queue (Case #ARB-904)</h2>
          </div>
          <span className="text-xs font-mono px-2 py-0.5 bg-amber-950 text-amber-300 rounded border border-amber-900/60">
            Priority Arbitration
          </span>
        </div>

        {resolvedDispute ? (
          <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-900/50 text-xs text-emerald-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span><strong>Dispute Resolved:</strong> {resolvedDispute}. Escrow balances updated and legal record archived.</span>
            </div>
            <button
              onClick={() => setResolvedDispute(null)}
              className="text-xs text-slate-400 hover:text-white underline cursor-pointer"
            >
              Reset Simulation
            </button>
          </div>
        ) : (
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-4 text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <span className="font-bold text-white text-sm">Dispute: Sub-Second WebSocket Latency SLA</span>
                <p className="text-slate-400 text-xs mt-0.5">
                  Client: <strong>Quantum Growth Partners</strong> vs Agency: <strong>Vanguard Interactive Labs</strong>
                </p>
              </div>
              <span className="font-mono font-bold text-amber-400 text-sm">$8,500 Escrow Disputed</span>
            </div>

            {/* Evidence comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 bg-slate-900 rounded border border-slate-800 space-y-1">
                <span className="font-bold text-slate-200 block">Client Claim:</span>
                <p className="text-slate-400 leading-relaxed text-[11px]">
                  "The feed spikes to 180ms during heavy market volume. Acceptance Criteria specified average response times strictly below 50ms under synthetic load."
                </p>
              </div>

              <div className="p-3 bg-slate-900 rounded border border-slate-800 space-y-1">
                <span className="font-bold text-slate-200 block">Agency Evidence:</span>
                <p className="text-slate-400 leading-relaxed text-[11px]">
                  "Delivered benchmarks show 38ms average latency in staging environment. Spikes occurred due to external sandbox rate-limiting outside the agreed SOW boundaries."
                </p>
              </div>
            </div>

            {/* Arbiter Actions */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <span className="text-[11px] text-slate-400">
                Official Platform Arbiter Determination:
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleResolveDispute('50/50 Split Compromise ($4,250 to Agency, $4,250 Refunded to Client)')}
                  className="px-3 py-1.5 font-semibold text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors cursor-pointer"
                >
                  Split Escrow (50/50 Compromise)
                </button>
                <button
                  onClick={() => handleResolveDispute('Full Escrow Released to Agency ($8,500)')}
                  className="px-3 py-1.5 font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg transition-colors cursor-pointer"
                >
                  Release to Agency (Criteria Met)
                </button>
                <button
                  onClick={() => handleResolveDispute('Full Escrow Refunded to Client ($8,500)')}
                  className="px-3 py-1.5 font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-lg transition-colors cursor-pointer"
                >
                  Refund Client (SLA Breach)
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Agency Vetting & Compliance Queue */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-sm font-bold text-white">Pending Studio Onboarding Applications</h2>
          <span className="text-xs text-slate-500 font-mono">2 Studios in Queue</span>
        </div>

        <div className="space-y-3 text-xs">
          <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <span className="font-bold text-white">Monolith Design Labs</span>
              <p className="text-slate-400 text-[11px]">Applied for: Enterprise Certified Studio · Location: Zurich, Switzerland</p>
              <p className="text-slate-500 text-[11px]">Audit: GitHub verified, 12 previous off-platform client references validated.</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button className="px-3 py-1.5 font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg transition-colors">
                Approve Studio
              </button>
              <button className="px-3 py-1.5 font-medium text-slate-400 hover:text-white bg-slate-800 rounded-lg transition-colors">
                Request Audit
              </button>
            </div>
          </div>

          <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <span className="font-bold text-white">Vector & Pixel Interactive</span>
              <p className="text-slate-400 text-[11px]">Applied for: Three.js & Mobile Verified · Location: Tokyo, Japan</p>
              <p className="text-slate-500 text-[11px]">Audit: Awwwards portfolio submitted, identity documents authenticated.</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button className="px-3 py-1.5 font-semibold text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg transition-colors">
                Approve Studio
              </button>
              <button className="px-3 py-1.5 font-medium text-slate-400 hover:text-white bg-slate-800 rounded-lg transition-colors">
                Request Audit
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};
