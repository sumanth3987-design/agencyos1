import React, { useState } from 'react';
import { UserRole, Project, Milestone, AgencyStudio } from './types';
import { MOCK_PROJECTS, MOCK_AGENCIES } from './data/mockData';
import { Header } from './components/Header';
import { ProjectWorkspace } from './components/ProjectWorkspace';
import { EscrowHub } from './components/EscrowHub';
import { AgencyStudioView } from './components/AgencyStudioView';
import { MarketplaceView } from './components/MarketplaceView';
import { AdminConsole } from './components/AdminConsole';
import { AiScopingModal } from './components/AiScopingModal';
import { ContractModal } from './components/ContractModal';
import { InvoiceModal } from './components/InvoiceModal';
import { CheckCircle2, AlertCircle, Building2, UserCircle2, ShieldCheck, Sparkles } from 'lucide-react';

export default function App() {
  const [currentRole, setCurrentRole] = useState<UserRole>('client');
  const [activeTab, setActiveTab] = useState<'workspace' | 'studio' | 'marketplace' | 'escrow' | 'admin'>('workspace');
  
  const [projects, setProjects] = useState<Project[]>(MOCK_PROJECTS);
  const [agencies, setAgencies] = useState<AgencyStudio[]>(MOCK_AGENCIES);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(MOCK_PROJECTS[0].id);

  // Modals
  const [isAiScoperOpen, setIsAiScoperOpen] = useState(false);
  const [contractModalProject, setContractModalProject] = useState<Project | null>(null);
  const [invoiceModalData, setInvoiceModalData] = useState<{ milestone: Milestone; project: Project } | null>(null);

  // Notification Toast
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  const activeProject = projects.find((p) => p.id === selectedProjectId) || projects[0];

  const handleUpdateProject = (updated: Project) => {
    setProjects(projects.map((p) => (p.id === updated.id ? updated : p)));
    showToast(`Project updated: ${updated.title}`);
  };

  const handleUpdateAgency = (updated: AgencyStudio) => {
    setAgencies(agencies.map((a) => (a.id === updated.id ? updated : a)));
    showToast(`Agency profile updated: ${updated.name}`);
  };

  const handleProjectCreated = (newProject: Project) => {
    setProjects([newProject, ...projects]);
    setSelectedProjectId(newProject.id);
    setActiveTab('workspace');
    showToast(`New project contract scoped and initiated: ${newProject.title}`);
  };

  const handleSignContract = (projectId: string, signature: string, role: UserRole) => {
    const proj = projects.find((p) => p.id === projectId);
    if (!proj) return;

    const updatedContract = {
      ...proj.contract,
      ...(role === 'client'
        ? {
            signedByClient: true,
            clientSignature: signature,
            clientSignedAt: new Date().toISOString(),
          }
        : {
            signedByAgency: true,
            agencySignature: signature,
            agencySignedAt: new Date().toISOString(),
          }),
    };

    const updatedProject: Project = {
      ...proj,
      contract: updatedContract,
      activityLog: [
        {
          id: `act-${Date.now()}`,
          action: `SOW Digitally Signed by ${role === 'client' ? 'Client' : 'Agency'}`,
          actor: signature,
          role,
          timestamp: new Date().toISOString().split('T')[0],
          details: `Digital cryptographic stamp executed.`,
        },
        ...proj.activityLog,
      ],
    };

    handleUpdateProject(updatedProject);
    setContractModalProject(updatedProject);
    showToast(`SOW signed successfully by ${signature}`);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      
      {/* Top Header */}
      <Header
        currentRole={currentRole}
        onRoleChange={(role) => {
          setCurrentRole(role);
          if (role === 'admin') setActiveTab('admin');
          else if (role === 'agency') setActiveTab('studio');
          else setActiveTab('workspace');
          showToast(`Switched view to ${role.toUpperCase()}`);
        }}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenAiScoper={() => setIsAiScoperOpen(true)}
      />

      {/* Role Demonstration Assistant Bar */}
      <div className="bg-slate-900/60 border-b border-slate-800/80 px-4 py-2">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Current Role Mode:</span>
            <span className="font-semibold text-white px-2 py-0.5 rounded bg-slate-800 border border-slate-700/60 capitalize">
              {currentRole === 'client' && 'Client View (Alexander Hayes - Velo Tech)'}
              {currentRole === 'agency' && 'Agency Studio Lead (Sarah Chen - Aether Studio)'}
              {currentRole === 'admin' && 'Platform Admin & Compliance Arbiter'}
            </span>
          </div>

          <div className="flex items-center gap-2 text-slate-400">
            <span>Switch Role to Test Workflows:</span>
            <div className="flex gap-1">
              <button
                onClick={() => {
                  setCurrentRole('client');
                  setActiveTab('workspace');
                }}
                className={`px-2 py-0.5 rounded transition-colors ${
                  currentRole === 'client' ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:text-white'
                }`}
              >
                Client
              </button>
              <button
                onClick={() => {
                  setCurrentRole('agency');
                  setActiveTab('workspace');
                }}
                className={`px-2 py-0.5 rounded transition-colors ${
                  currentRole === 'agency' ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:text-white'
                }`}
              >
                Agency
              </button>
              <button
                onClick={() => {
                  setCurrentRole('admin');
                  setActiveTab('admin');
                }}
                className={`px-2 py-0.5 rounded transition-colors ${
                  currentRole === 'admin' ? 'bg-amber-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:text-white'
                }`}
              >
                Admin
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Project Selector when viewing Workspace */}
        {activeTab === 'workspace' && (
          <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900 border border-slate-800 p-3.5 rounded-xl">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400 font-medium">Select Active Agreement:</span>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-semibold focus:outline-none focus:border-indigo-500"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title} (${p.totalBudget.toLocaleString()})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setIsAiScoperOpen(true)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer self-start sm:self-auto"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Scope New SOW with AI</span>
            </button>
          </div>
        )}

        {/* TAB 1: WORKSPACE */}
        {activeTab === 'workspace' && (
          <ProjectWorkspace
            project={activeProject}
            currentRole={currentRole}
            onUpdateProject={handleUpdateProject}
            onOpenContract={(proj) => setContractModalProject(proj)}
            onOpenInvoice={(milestone, proj) => setInvoiceModalData({ milestone, project: proj })}
          />
        )}

        {/* TAB 2: ESCROW & INVOICING */}
        {activeTab === 'escrow' && (
          <EscrowHub
            projects={projects}
            onOpenInvoice={(milestone, proj) => setInvoiceModalData({ milestone, project: proj })}
            onOpenContract={(proj) => setContractModalProject(proj)}
            onSelectProject={(projId) => {
              setSelectedProjectId(projId);
              setActiveTab('workspace');
            }}
          />
        )}

        {/* TAB 3: STUDIO & TEAM */}
        {activeTab === 'studio' && (
          <AgencyStudioView
            agency={agencies[0]}
            onUpdateAgency={handleUpdateAgency}
            onSelectProjectWorkspace={() => setActiveTab('workspace')}
          />
        )}

        {/* TAB 4: VETTED MARKETPLACE */}
        {activeTab === 'marketplace' && (
          <MarketplaceView
            agencies={agencies}
            onSelectAgencyForScoping={(agency) => {
              setIsAiScoperOpen(true);
            }}
          />
        )}

        {/* TAB 5: ADMIN ARBITRATION */}
        {activeTab === 'admin' && (
          <AdminConsole projects={projects} />
        )}

      </main>

      {/* AI Scoping Modal */}
      <AiScopingModal
        isOpen={isAiScoperOpen}
        onClose={() => setIsAiScoperOpen(false)}
        onProjectCreated={handleProjectCreated}
      />

      {/* Contract / SOW Modal */}
      <ContractModal
        project={contractModalProject}
        currentRole={currentRole}
        onClose={() => setContractModalProject(null)}
        onSignContract={handleSignContract}
      />

      {/* Official Tax Invoice Modal */}
      <InvoiceModal
        milestone={invoiceModalData?.milestone || null}
        project={invoiceModalData?.project || null}
        onClose={() => setInvoiceModalData(null)}
      />

      {/* Floating Action Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-2.5 bg-slate-900 border border-slate-700 text-white rounded-lg shadow-2xl text-xs animate-in slide-in-from-bottom duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 mt-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-300">AgencyOS</span>
            <span>·</span>
            <span>Enterprise Escrow & SOW Operating System</span>
          </div>
          <p className="font-mono text-[11px] text-slate-500">
            Immutable Milestone Audit Vault · Bank-Grade Escrow Settlement
          </p>
        </div>
      </footer>

    </div>
  );
}
