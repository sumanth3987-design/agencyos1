import React from 'react';
import { ShieldCheck, ArrowUpRight, FileText, CheckCircle2, Clock, AlertCircle, Download, ExternalLink } from 'lucide-react';
import { Project, Milestone } from '../types';

interface EscrowHubProps {
  projects: Project[];
  onOpenInvoice: (milestone: Milestone, project: Project) => void;
  onOpenContract: (project: Project) => void;
  onSelectProject: (projectId: string) => void;
}

export const EscrowHub: React.FC<EscrowHubProps> = ({
  projects,
  onOpenInvoice,
  onOpenContract,
  onSelectProject,
}) => {
  const totalVolume = projects.reduce((acc, p) => acc + p.totalBudget, 0);
  const totalInEscrow = projects.reduce((acc, p) => acc + (p.escrowSecuredAmount - p.releasedAmount), 0);
  const totalReleased = projects.reduce((acc, p) => acc + p.releasedAmount, 0);

  // Collect all approved milestones as generated invoices
  const approvedMilestones = projects.flatMap((p) =>
    p.milestones
      .filter((m) => m.status === 'approved')
      .map((m) => ({ milestone: m, project: p }))
  );

  return (
    <div className="space-y-6">
      
      {/* Top Escrow Financial KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">Total Contracted Volume</span>
          <p className="text-xl font-bold font-mono text-white tabular-nums">
            ${totalVolume.toLocaleString()} <span className="text-xs font-normal text-slate-500">USD</span>
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">Across {projects.length} multi-phase agreements</span>
        </div>

        <div className="p-4 bg-slate-900 border border-indigo-900/60 rounded-xl relative overflow-hidden">
          <div className="absolute right-3 top-3 p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-medium text-indigo-300 block mb-1">Held in Secure Escrow</span>
          <p className="text-xl font-bold font-mono text-indigo-300 tabular-nums">
            ${totalInEscrow.toLocaleString()} <span className="text-xs font-normal text-indigo-400/70">USD</span>
          </p>
          <span className="text-[11px] text-indigo-400/80 mt-1 block">Protected by dual-sign release gates</span>
        </div>

        <div className="p-4 bg-slate-900 border border-emerald-900/50 rounded-xl">
          <span className="text-[11px] font-medium text-emerald-400 block mb-1">Released to Agencies</span>
          <p className="text-xl font-bold font-mono text-emerald-400 tabular-nums">
            ${totalReleased.toLocaleString()} <span className="text-xs font-normal text-emerald-500/70">USD</span>
          </p>
          <span className="text-[11px] text-emerald-400/80 mt-1 block">100% verified deliverable handoff</span>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">Platform Dispute Rate</span>
          <p className="text-xl font-bold font-mono text-white tabular-nums">
            0.0% <span className="text-xs font-normal text-slate-500">Zero disputes</span>
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">Enforceable SOW acceptance criteria</span>
        </div>

      </div>

      {/* Active Escrow Vaults & Milestone Breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-sm font-bold text-white">Active Project Escrow Vaults</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live status of milestone funds deposited, verified in review, and awaiting release
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {projects.length} Active Vaults
          </span>
        </div>

        <div className="space-y-4">
          {projects.map((project) => {
            const progressPercent = Math.round((project.releasedAmount / project.totalBudget) * 100);

            return (
              <div
                key={project.id}
                className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold text-white">{project.title}</h3>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                      <span>Client: {project.clientName}</span>
                      <span aria-hidden="true">·</span>
                      <span>Agency: {project.agencyName}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onSelectProject(project.id)}
                      className="px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-colors cursor-pointer"
                    >
                      Open Workspace
                    </button>
                    <button
                      onClick={() => onOpenContract(project)}
                      className="px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors cursor-pointer"
                    >
                      Contract SOW
                    </button>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                    <span>Released: ${project.releasedAmount.toLocaleString()} ({progressPercent}%)</span>
                    <span>Total Budget: ${project.totalBudget.toLocaleString()}</span>
                  </div>
                  <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-linear-to-r from-indigo-500 to-emerald-500 rounded-full transition-all duration-500"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>

                {/* Milestones Horizontal Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
                  {project.milestones.map((m, mIdx) => (
                    <div
                      key={m.id}
                      className="p-2.5 rounded bg-slate-900/70 border border-slate-800/80 text-xs flex items-center justify-between"
                    >
                      <div className="truncate mr-2">
                        <span className="text-[10px] text-slate-500 font-mono block">Phase {mIdx + 1}</span>
                        <span className="font-medium text-slate-200 truncate block">{m.title}</span>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="font-mono font-bold text-white text-[11px] block">${m.amount.toLocaleString()}</span>
                        <span className={`text-[10px] font-medium ${
                          m.status === 'approved' ? 'text-emerald-400' :
                          m.status === 'in_review' ? 'text-amber-400' :
                          m.status === 'funded' ? 'text-indigo-400' : 'text-slate-500'
                        }`}>
                          {m.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tax Invoices & Compliance Ledger */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-sm font-bold text-white">Automated Tax Invoices Ledger (GST / VAT Compliant)</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Automatically generated and cryptographically stamped upon milestone escrow release
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {approvedMilestones.length} Generated Invoices
          </span>
        </div>

        {approvedMilestones.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Invoice #</th>
                  <th className="px-4 py-2.5">Date Released</th>
                  <th className="px-4 py-2.5">Project & Milestone</th>
                  <th className="px-4 py-2.5">Client & Agency</th>
                  <th className="px-4 py-2.5 text-right">Amount</th>
                  <th className="px-4 py-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-medium text-slate-300">
                {approvedMilestones.map(({ milestone, project }) => (
                  <tr key={milestone.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-indigo-400">
                      INV-2026-081
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono">
                      {milestone.releasedAt ? milestone.releasedAt.split('T')[0] : '2026-09-24'}
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-white font-semibold truncate max-w-xs">{project.title}</p>
                      <p className="text-slate-400 text-[11px] truncate">{milestone.title}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-slate-200">{project.clientCompany}</p>
                      <p className="text-slate-500 text-[11px]">{project.agencyName}</p>
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-emerald-400 tabular-nums">
                      ${milestone.amount.toLocaleString()} USD
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onOpenInvoice(milestone, project)}
                        className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 cursor-pointer"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>View Invoice</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-6 text-slate-500 text-xs">
            No milestones released yet. Invoices generate automatically once milestone funds are released.
          </div>
        )}
      </div>

    </div>
  );
};
