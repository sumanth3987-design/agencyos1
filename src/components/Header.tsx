import React from 'react';
import { UserRole } from '../types';
import { Sparkles, ShieldCheck, Briefcase, Building2, UserCircle2 } from 'lucide-react';

interface HeaderProps {
  currentRole: UserRole;
  onRoleChange: (role: UserRole) => void;
  activeTab: 'workspace' | 'studio' | 'marketplace' | 'escrow' | 'admin';
  onTabChange: (tab: 'workspace' | 'studio' | 'marketplace' | 'escrow' | 'admin') => void;
  onOpenAiScoper: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentRole,
  onRoleChange,
  activeTab,
  onTabChange,
  onOpenAiScoper,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-8 px-4 sm:px-6 lg:px-8">
        
        {/* Zone 1: Single text element wordmark */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => onTabChange('workspace')}
            className="flex items-center gap-2.5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 rounded-lg py-1 px-1.5 transition-colors hover:opacity-90"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-linear-to-br from-indigo-500 to-indigo-700 text-white shadow-md shadow-indigo-500/20 font-bold text-base">
              A
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white block leading-none">
                AgencyOS
              </span>
              <span className="text-[11px] font-medium text-slate-400 block mt-0.5">
                Escrow & Delivery Operating System
              </span>
            </div>
          </button>
        </div>

        {/* Zone 2: Clean single-line text navigation links */}
        <nav className="hidden md:flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => onTabChange('workspace')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap shrink-0 transition-colors ${
              activeTab === 'workspace'
                ? 'bg-slate-800/80 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            Project Workspace
          </button>

          <button
            onClick={() => onTabChange('escrow')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap shrink-0 transition-colors ${
              activeTab === 'escrow'
                ? 'bg-slate-800/80 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            Escrow & Invoicing
          </button>

          <button
            onClick={() => onTabChange('studio')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap shrink-0 transition-colors ${
              activeTab === 'studio'
                ? 'bg-slate-800/80 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            Agency Studio & Team
          </button>

          <button
            onClick={() => onTabChange('marketplace')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap shrink-0 transition-colors ${
              activeTab === 'marketplace'
                ? 'bg-slate-800/80 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            Vetted Agencies
          </button>

          <button
            onClick={() => onTabChange('admin')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap shrink-0 transition-colors ${
              activeTab === 'admin'
                ? 'bg-slate-800/80 text-indigo-300 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            Admin Arbitrations
          </button>
        </nav>

        {/* Zone 3: 1 primary action & live role context switcher */}
        <div className="flex items-center gap-3 shrink-0">
          {/* AI Scoping CTA */}
          <button
            onClick={onOpenAiScoper}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-300 bg-indigo-950/70 border border-indigo-800/60 rounded-lg hover:bg-indigo-900/60 transition-colors shadow-sm cursor-pointer whitespace-nowrap shrink-0"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI Project Scoper</span>
          </button>

          {/* Interactive Role Switcher */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
            <button
              onClick={() => onRoleChange('client')}
              title="View as Client (Alex Vance, Velo Tech)"
              className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                currentRole === 'client'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <UserCircle2 className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Client</span>
            </button>

            <button
              onClick={() => onRoleChange('agency')}
              title="View as Agency Lead (Sarah Chen, Aether Studio)"
              className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                currentRole === 'agency'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Agency</span>
            </button>

            <button
              onClick={() => onRoleChange('admin')}
              title="View as Platform Admin & Arbiter"
              className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                currentRole === 'admin'
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Admin</span>
            </button>
          </div>
        </div>

      </div>
    </header>
  );
};
