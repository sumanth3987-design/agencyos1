import React from 'react';
import { X, Printer, Download, CheckCircle2, ShieldCheck, Building2 } from 'lucide-react';
import { Milestone, Project } from '../types';

interface InvoiceModalProps {
  milestone: Milestone | null;
  project: Project | null;
  onClose: () => void;
}

export const InvoiceModal: React.FC<InvoiceModalProps> = ({
  milestone,
  project,
  onClose,
}) => {
  if (!milestone || !project) return null;

  const invoiceNumber = `INV-2026-${milestone.id.slice(-3).toUpperCase()}`;
  const issueDate = milestone.releasedAt ? milestone.releasedAt.split('T')[0] : '2026-09-24';
  const taxAmount = Math.round(milestone.amount * 0.08); // 8% enterprise services tax
  const totalAmount = milestone.amount + taxAmount;
  const transactionHash = `0x94b7e8d2${milestone.id.slice(-6)}c41`;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl max-h-[92vh] flex flex-col bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden my-4">
        
        {/* Modal Controls Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-3.5 bg-slate-950/60 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-white">Official Tax Invoice</span>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-900/60 px-2 py-0.5 rounded">
              Paid via Escrow Release
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / Save PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Invoice Printable Sheet */}
        <div className="p-8 overflow-y-auto space-y-6 bg-slate-950 text-slate-300 text-xs font-sans print:bg-white print:text-black">
          
          {/* Invoice Top Header */}
          <div className="flex items-start justify-between border-b border-slate-800 pb-6 print:border-neutral-200">
            <div>
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded bg-indigo-600 text-white font-bold text-xs">
                  A
                </div>
                <span className="text-base font-bold text-white tracking-tight">AgencyOS</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Escrow Vault Settlement Service</p>
            </div>

            <div className="text-right space-y-0.5">
              <h1 className="text-base font-bold font-mono text-white tracking-tight">{invoiceNumber}</h1>
              <p className="text-slate-400 text-[11px]">Date: <span className="font-mono">{issueDate}</span></p>
              <p className="text-slate-400 text-[11px]">Payment Status: <strong className="text-emerald-400">Escrow Released</strong></p>
            </div>
          </div>

          {/* Biller & Payee Addresses */}
          <div className="grid grid-cols-2 gap-6 border-b border-slate-800 pb-6">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold block">Issued By (Agency)</span>
              <p className="font-bold text-white text-xs">{project.agencyName}</p>
              <p className="text-slate-400 text-[11px]">548 Market Street, Suite 39201</p>
              <p className="text-slate-400 text-[11px]">San Francisco, CA 94104, USA</p>
              <p className="text-slate-400 text-[11px]">Tax ID: US-EIN 84-2910394</p>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold block">Billed To (Client)</span>
              <p className="font-bold text-white text-xs">{project.clientCompany}</p>
              <p className="text-slate-400 text-[11px]">Attn: {project.clientName}</p>
              <p className="text-slate-400 text-[11px]">100 Wall Street, 14th Floor</p>
              <p className="text-slate-400 text-[11px]">New York, NY 10005, USA</p>
            </div>
          </div>

          {/* Line Items Table */}
          <div className="space-y-2">
            <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold block">
              Settled Milestone Deliverables
            </span>

            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 uppercase text-[10px] font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Description</th>
                  <th className="py-2.5 px-3 text-center">Revisions</th>
                  <th className="py-2.5 px-3 text-right">Amount (USD)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-medium">
                <tr>
                  <td className="py-3 px-3">
                    <p className="text-white font-semibold">{project.title}</p>
                    <p className="text-slate-400 text-[11px]">{milestone.title}</p>
                    <p className="text-slate-500 text-[10px] mt-0.5">{milestone.description}</p>
                  </td>
                  <td className="py-3 px-3 text-center text-slate-400 font-mono">
                    {milestone.revisionRound} of {milestone.maxRevisions}
                  </td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-white tabular-nums">
                    ${milestone.amount.toLocaleString()}.00
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Calculation summary */}
          <div className="flex justify-end pt-2 border-t border-slate-800">
            <div className="w-64 space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Subtotal:</span>
                <span>${milestone.amount.toLocaleString()}.00</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Services Tax (8%):</span>
                <span>${taxAmount.toLocaleString()}.00</span>
              </div>
              <div className="flex justify-between text-base font-bold text-emerald-400 pt-2 border-t border-slate-800">
                <span>Total Settled:</span>
                <span>${totalAmount.toLocaleString()}.00</span>
              </div>
            </div>
          </div>

          {/* Transaction Hash & Escrow Verification Stamp */}
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Escrow Settlement Hash: {transactionHash}</span>
            </div>
            <span className="text-slate-500">Immutable Ledger</span>
          </div>

        </div>

      </div>
    </div>
  );
};
