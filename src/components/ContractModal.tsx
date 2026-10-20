import React, { useState } from 'react';
import { X, FileText, CheckCircle2, ShieldCheck, Printer, Download, PenTool } from 'lucide-react';
import { Project, UserRole } from '../types';

interface ContractModalProps {
  project: Project | null;
  currentRole: UserRole;
  onClose: () => void;
  onSignContract: (projectId: string, signature: string, role: UserRole) => void;
}

export const ContractModal: React.FC<ContractModalProps> = ({
  project,
  currentRole,
  onClose,
  onSignContract,
}) => {
  if (!project) return null;

  const [signatureInput, setSignatureInput] = useState('');
  const contract = project.contract;

  const handleSign = () => {
    if (!signatureInput.trim()) return;
    onSignContract(project.id, signatureInput.trim(), currentRole);
    setSignatureInput('');
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl max-h-[92vh] flex flex-col bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden my-4">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/60 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Master Services Agreement (SOW)</h2>
              <p className="text-xs text-slate-400">
                Digital contract binding escrow schedules, acceptance criteria, and IP rights
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              title="Print / Save Contract"
            >
              <Printer className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Contract Printable Document Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-300 leading-relaxed bg-slate-950/40">
          
          {/* Agreement Header */}
          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
              <div>
                <span className="text-[10px] uppercase font-mono text-indigo-400 tracking-wider block">Contract Reference</span>
                <span className="text-sm font-bold text-white font-mono">{contract.id}</span>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider block">Effective Date</span>
                <span className="text-xs font-mono text-slate-300">{contract.effectiveDate}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-500 block mb-0.5">The Client</span>
                <p className="font-bold text-white">{project.clientName}</p>
                <p className="text-slate-400 text-[11px]">{project.clientCompany}</p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-mono text-slate-500 block mb-0.5">The Agency</span>
                <p className="font-bold text-white">{project.agencyName}</p>
                <p className="text-slate-400 text-[11px]">Authorized Independent Studio Partner</p>
              </div>
            </div>
          </div>

          {/* Section 1: Statement of Work */}
          <div className="space-y-1.5">
            <h3 className="font-bold text-white text-xs uppercase tracking-wider text-slate-200">
              1. Statement of Work & Project Objectives
            </h3>
            <p className="text-slate-400 leading-relaxed bg-slate-900 p-3 rounded-lg border border-slate-800/80">
              {contract.sowSummary}
            </p>
          </div>

          {/* Section 2: Milestone Schedule & Escrow Allocation */}
          <div className="space-y-2">
            <h3 className="font-bold text-white text-xs uppercase tracking-wider text-slate-200">
              2. Milestone Escrow Schedule & Release Conditions
            </h3>
            <div className="divide-y divide-slate-800 border border-slate-800 rounded-lg overflow-hidden bg-slate-900">
              {project.milestones.map((m, i) => (
                <div key={m.id} className="p-3 flex items-start justify-between gap-4">
                  <div className="space-y-0.5">
                    <span className="font-semibold text-white">Phase {i + 1}: {m.title}</span>
                    <p className="text-slate-400 text-[11px]">{m.description}</p>
                  </div>
                  <div className="text-right shrink-0 font-mono font-bold text-emerald-400">
                    ${m.amount.toLocaleString()} USD
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Intellectual Property (IP) Transfer */}
          <div className="space-y-1.5">
            <h3 className="font-bold text-white text-xs uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
              <span>3. Intellectual Property Assignment & Ownership Handover</span>
            </h3>
            <div className="bg-indigo-950/20 border border-indigo-900/40 p-3.5 rounded-lg text-indigo-200/90 leading-relaxed text-xs">
              {contract.ipTransferClause}
            </div>
          </div>

          {/* Section 4: Confidentiality & Non-Disclosure */}
          <div className="space-y-1.5">
            <h3 className="font-bold text-white text-xs uppercase tracking-wider text-slate-200">
              4. Non-Disclosure & Confidentiality
            </h3>
            <p className="text-slate-400 leading-relaxed bg-slate-900 p-3 rounded-lg border border-slate-800/80">
              {contract.confidentialityTerms}
            </p>
          </div>

          {/* Section 5: Digital E-Signatures Status */}
          <div className="space-y-3 pt-2 border-t border-slate-800">
            <h3 className="font-bold text-white text-xs uppercase tracking-wider text-slate-200">
              5. Digital Execution & Audit Sign-Off
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Client Signature Box */}
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-[10px] uppercase font-mono text-slate-500 block">Client Signature</span>
                {contract.signedByClient ? (
                  <div className="space-y-1">
                    <p className="font-serif italic text-base text-indigo-300 font-semibold">{contract.clientSignature}</p>
                    <div className="flex items-center gap-1.5 text-[10px] text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Cryptographically Signed {contract.clientSignedAt?.split('T')[0]}</span>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-xs text-slate-400">Awaiting client signature</p>
                    {currentRole === 'client' && (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Type full legal name to sign"
                          value={signatureInput}
                          onChange={(e) => setSignatureInput(e.target.value)}
                          className="px-2.5 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-white flex-1"
                        />
                        <button
                          onClick={handleSign}
                          disabled={!signatureInput.trim()}
                          className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded disabled:opacity-40"
                        >
                          Sign SOW
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Agency Signature Box */}
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-[10px] uppercase font-mono text-slate-500 block">Agency Principal Signature</span>
                {contract.signedByAgency ? (
                  <div className="space-y-1">
                    <p className="font-serif italic text-base text-indigo-300 font-semibold">{contract.agencySignature}</p>
                    <div className="flex items-center gap-1.5 text-[10px] text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Authenticated {contract.agencySignedAt?.split('T')[0]}</span>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-xs text-slate-400">Awaiting agency countersignature</p>
                    {currentRole === 'agency' && (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Type agency principal name"
                          value={signatureInput}
                          onChange={(e) => setSignatureInput(e.target.value)}
                          className="px-2.5 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-white flex-1"
                        />
                        <button
                          onClick={handleSign}
                          disabled={!signatureInput.trim()}
                          className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded disabled:opacity-40"
                        >
                          Sign SOW
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-3.5 bg-slate-950/80 shrink-0">
          <span className="text-[11px] text-slate-500 font-mono">
            Encrypted & Timestamped via AgencyOS Legal Audit Vault
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors cursor-pointer"
          >
            Close Agreement
          </button>
        </div>

      </div>
    </div>
  );
};
