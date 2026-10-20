import React, { useState } from 'react';
import { 
  CheckCircle2, Clock, DollarSign, ShieldCheck, AlertTriangle, 
  MessageSquare, FileText, Download, ExternalLink, Plus, 
  ChevronRight, ArrowUpRight, Check, Sparkles, RefreshCw, Layers, Shield
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { Project, Milestone, UserRole, AnnotationPin, Deliverable } from '../types';

interface ProjectWorkspaceProps {
  project: Project;
  currentRole: UserRole;
  onUpdateProject: (updated: Project) => void;
  onOpenContract: (project: Project) => void;
  onOpenInvoice: (milestone: Milestone, project: Project) => void;
}

export const ProjectWorkspace: React.FC<ProjectWorkspaceProps> = ({
  project,
  currentRole,
  onUpdateProject,
  onOpenContract,
  onOpenInvoice,
}) => {
  const [selectedMilestoneIndex, setSelectedMilestoneIndex] = useState(1); // default to Phase 2 (in_review)
  const [activeTab, setActiveTab] = useState<'deliverable' | 'criteria' | 'activity' | 'team'>('deliverable');
  
  // New pin form state
  const [isPlacingPin, setIsPlacingPin] = useState(false);
  const [activePin, setActivePin] = useState<AnnotationPin | null>(null);
  const [newPinCoords, setNewPinCoords] = useState<{ x: number; y: number } | null>(null);
  const [newPinText, setNewPinText] = useState('');

  // Revision request modal/state
  const [showRevisionModal, setShowRevisionModal] = useState(false);
  const [revisionNotes, setRevisionNotes] = useState('');

  const currentMilestone = project.milestones[selectedMilestoneIndex] || project.milestones[0];
  const deliverable = currentMilestone?.deliverable;

  const triggerConfetti = () => {
    try {
      confetti({
        particleCount: 120,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#6366f1', '#10b981', '#38bdf8', '#fbbf24']
      });
    } catch {
      // fallback
    }
  };

  // Client funds milestone into escrow
  const handleFundMilestone = () => {
    const updatedMilestones = [...project.milestones];
    updatedMilestones[selectedMilestoneIndex] = {
      ...currentMilestone,
      status: 'funded',
      escrowDepositedAt: new Date().toISOString(),
    };

    const updatedProject: Project = {
      ...project,
      escrowSecuredAmount: project.escrowSecuredAmount + currentMilestone.amount,
      milestones: updatedMilestones,
      activityLog: [
        {
          id: `act-${Date.now()}`,
          action: `${currentMilestone.title} Funded in Escrow`,
          actor: project.clientName,
          role: 'client',
          timestamp: new Date().toISOString().split('T')[0],
          details: `$${currentMilestone.amount.toLocaleString()} secured into cryptographic escrow vault.`,
        },
        ...project.activityLog,
      ],
    };

    onUpdateProject(updatedProject);
  };

  // Agency starts work
  const handleStartWork = () => {
    const updatedMilestones = [...project.milestones];
    updatedMilestones[selectedMilestoneIndex] = {
      ...currentMilestone,
      status: 'in_progress',
    };

    const updatedProject: Project = {
      ...project,
      milestones: updatedMilestones,
      activityLog: [
        {
          id: `act-${Date.now()}`,
          action: 'Milestone Development Started',
          actor: project.agencyName,
          role: 'agency',
          timestamp: new Date().toISOString().split('T')[0],
          details: `Sprint started for ${currentMilestone.title}.`,
        },
        ...project.activityLog,
      ],
    };

    onUpdateProject(updatedProject);
  };

  // Agency submits deliverable for review
  const handleSubmitDeliverable = () => {
    const updatedMilestones = [...project.milestones];
    const newDeliverable: Deliverable = currentMilestone.deliverable || {
      id: `del-${Date.now()}`,
      title: `${currentMilestone.title} - Build Candidate`,
      version: `v${currentMilestone.revisionRound + 1}.0`,
      previewUrl: project.category.includes('Mobile')
        ? '/src/assets/images/mobile_app_mockup_1792401017957.jpg'
        : '/src/assets/images/workspace_sample_mockup_1792401018038.jpg',
      description: 'Submitted milestone deliverable ready for client verification and pin review.',
      submissionDate: new Date().toISOString().split('T')[0],
      fileSize: '38.4 MB Release',
      annotations: [],
    };

    updatedMilestones[selectedMilestoneIndex] = {
      ...currentMilestone,
      status: 'in_review',
      autoReleaseDaysRemaining: 7,
      deliverable: newDeliverable,
    };

    const updatedProject: Project = {
      ...project,
      status: 'in_review',
      milestones: updatedMilestones,
      activityLog: [
        {
          id: `act-${Date.now()}`,
          action: 'Deliverable Submitted for Client Review',
          actor: project.agencyName,
          role: 'agency',
          timestamp: new Date().toISOString().split('T')[0],
          details: `${currentMilestone.title} candidate submitted. 7-day auto-release timer initiated.`,
        },
        ...project.activityLog,
      ],
    };

    onUpdateProject(updatedProject);
  };

  // Client approves and releases escrow
  const handleApproveAndRelease = () => {
    triggerConfetti();

    const updatedMilestones = [...project.milestones];
    updatedMilestones[selectedMilestoneIndex] = {
      ...currentMilestone,
      status: 'approved',
      releasedAt: new Date().toISOString(),
      autoReleaseDaysRemaining: undefined,
    };

    const allApproved = updatedMilestones.every((m) => m.status === 'approved');

    const updatedProject: Project = {
      ...project,
      releasedAmount: project.releasedAmount + currentMilestone.amount,
      status: allApproved ? 'completed' : 'active',
      milestones: updatedMilestones,
      activityLog: [
        {
          id: `act-${Date.now()}`,
          action: `${currentMilestone.title} Approved & Escrow Released`,
          actor: project.clientName,
          role: 'client',
          timestamp: new Date().toISOString().split('T')[0],
          details: `$${currentMilestone.amount.toLocaleString()} released to agency wallet. Official tax invoice generated.`,
        },
        ...project.activityLog,
      ],
    };

    onUpdateProject(updatedProject);

    // Prompt invoice
    setTimeout(() => {
      onOpenInvoice(updatedMilestones[selectedMilestoneIndex], updatedProject);
    }, 600);
  };

  // Client requests revision
  const handleConfirmRevision = () => {
    if (!revisionNotes.trim()) return;

    const updatedMilestones = [...project.milestones];
    updatedMilestones[selectedMilestoneIndex] = {
      ...currentMilestone,
      status: 'in_progress',
      revisionRound: currentMilestone.revisionRound + 1,
      autoReleaseDaysRemaining: undefined,
    };

    const updatedProject: Project = {
      ...project,
      milestones: updatedMilestones,
      activityLog: [
        {
          id: `act-${Date.now()}`,
          action: `Revision Requested on ${currentMilestone.title}`,
          actor: project.clientName,
          role: 'client',
          timestamp: new Date().toISOString().split('T')[0],
          details: `Round ${currentMilestone.revisionRound + 1} of ${currentMilestone.maxRevisions}: "${revisionNotes}"`,
        },
        ...project.activityLog,
      ],
    };

    onUpdateProject(updatedProject);
    setShowRevisionModal(false);
    setRevisionNotes('');
  };

  // Interactive Image Pin Placement
  const handleImageClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isPlacingPin || !deliverable) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    setNewPinCoords({ x: Math.round(x), y: Math.round(y) });
  };

  const handleSavePin = () => {
    if (!newPinCoords || !newPinText.trim() || !deliverable) return;

    const newPin: AnnotationPin = {
      id: `pin-${Date.now()}`,
      xPercent: newPinCoords.x,
      yPercent: newPinCoords.y,
      author: currentRole === 'client' ? project.clientName : project.agencyName,
      authorRole: currentRole,
      text: newPinText,
      timestamp: new Date().toISOString(),
      resolved: false,
    };

    const updatedAnnotations = [...(deliverable.annotations || []), newPin];
    const updatedDeliverable = { ...deliverable, annotations: updatedAnnotations };

    const updatedMilestones = [...project.milestones];
    updatedMilestones[selectedMilestoneIndex] = {
      ...currentMilestone,
      deliverable: updatedDeliverable,
    };

    const updatedProject: Project = {
      ...project,
      milestones: updatedMilestones,
      activityLog: [
        {
          id: `act-${Date.now()}`,
          action: 'Visual Annotation Pin Added',
          actor: currentRole === 'client' ? project.clientName : project.agencyName,
          role: currentRole,
          timestamp: new Date().toISOString().split('T')[0],
          details: `Pin placed at (${newPinCoords.x}%, ${newPinCoords.y}%): "${newPinText}"`,
        },
        ...project.activityLog,
      ],
    };

    onUpdateProject(updatedProject);
    setNewPinCoords(null);
    setNewPinText('');
    setIsPlacingPin(false);
  };

  const handleToggleResolvePin = (pinId: string) => {
    if (!deliverable) return;
    const updatedAnnotations = deliverable.annotations.map((p) =>
      p.id === pinId ? { ...p, resolved: !p.resolved } : p
    );

    const updatedDeliverable = { ...deliverable, annotations: updatedAnnotations };
    const updatedMilestones = [...project.milestones];
    updatedMilestones[selectedMilestoneIndex] = {
      ...currentMilestone,
      deliverable: updatedDeliverable,
    };

    onUpdateProject({ ...project, milestones: updatedMilestones });
    if (activePin?.id === pinId) {
      setActivePin({ ...activePin, resolved: !activePin.resolved });
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Project Header Banner & Contract Lock Status */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="font-medium text-indigo-400">{project.category}</span>
              <span aria-hidden="true">·</span>
              <span>Started {project.startDate}</span>
              <span aria-hidden="true">·</span>
              <span>Target Delivery {project.targetEndDate}</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              {project.title}
            </h1>
          </div>

          {/* Quick Financial Health Pill & Contract Trigger */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-4 bg-slate-950/70 border border-slate-800 px-4 py-2 rounded-lg text-xs">
              <div>
                <span className="text-[11px] text-slate-400 block">Total Contract</span>
                <span className="font-mono font-bold text-white tabular-nums">${project.totalBudget.toLocaleString()}</span>
              </div>
              <div className="h-6 w-px bg-slate-800" />
              <div>
                <span className="text-[11px] text-indigo-400 block">Secured Escrow</span>
                <span className="font-mono font-bold text-indigo-300 tabular-nums">${project.escrowSecuredAmount.toLocaleString()}</span>
              </div>
              <div className="h-6 w-px bg-slate-800" />
              <div>
                <span className="text-[11px] text-emerald-400 block">Released</span>
                <span className="font-mono font-bold text-emerald-400 tabular-nums">${project.releasedAmount.toLocaleString()}</span>
              </div>
            </div>

            <button
              onClick={() => onOpenContract(project)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-200 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 rounded-lg transition-colors cursor-pointer shrink-0"
            >
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span>SOW & IP Contract</span>
            </button>
          </div>
        </div>

        {/* Client & Agency Attribution Bar */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <img
                src={project.clientAvatar}
                alt={project.clientName}
                className="w-6 h-6 rounded-full object-cover border border-slate-700"
              />
              <span className="text-slate-400">Client:</span>
              <span className="font-semibold text-white">{project.clientName}</span>
              <span className="text-slate-400">({project.clientCompany})</span>
            </div>

            <div className="flex items-center gap-2">
              <img
                src={project.agencyAvatar}
                alt={project.agencyName}
                className="w-6 h-6 rounded-full object-cover border border-slate-700"
              />
              <span className="text-slate-400">Agency:</span>
              <span className="font-semibold text-white">{project.agencyName}</span>
            </div>
          </div>

          {/* Auto-Release Protection Notice */}
          {currentMilestone?.autoReleaseDaysRemaining !== undefined && currentMilestone.status === 'in_review' && (
            <div className="flex items-center gap-1.5 text-xs text-amber-300 bg-amber-950/40 border border-amber-900/40 px-3 py-1 rounded-md">
              <Clock className="w-3.5 h-3.5" />
              <span>Anti-Ghosting Protected: Auto-releases in {currentMilestone.autoReleaseDaysRemaining} days if unreviewed</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Workspace Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Milestone Navigator & Escrow Action Bar */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Contract Milestone Pipeline
            </h3>

            <div className="space-y-2">
              {project.milestones.map((m, idx) => {
                const isSelected = selectedMilestoneIndex === idx;
                
                const statusBadge = {
                  pending_funding: { text: 'Awaiting Escrow', color: 'text-slate-400 bg-slate-800' },
                  funded: { text: 'Funded in Escrow', color: 'text-indigo-300 bg-indigo-950 border border-indigo-800/40' },
                  in_progress: { text: 'In Production', color: 'text-sky-300 bg-sky-950 border border-sky-800/40' },
                  in_review: { text: 'Ready for Review', color: 'text-amber-300 bg-amber-950 border border-amber-800/40' },
                  approved: { text: 'Approved & Released', color: 'text-emerald-300 bg-emerald-950 border border-emerald-800/40' },
                  disputed: { text: 'In Arbitration', color: 'text-rose-300 bg-rose-950 border border-rose-800/40' },
                }[m.status];

                return (
                  <button
                    key={m.id}
                    onClick={() => {
                      setSelectedMilestoneIndex(idx);
                      setActivePin(null);
                    }}
                    className={`w-full text-left p-3 rounded-lg border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-indigo-500 bg-slate-950 shadow-md'
                        : 'border-slate-800/80 bg-slate-950/40 hover:bg-slate-800/40 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-mono text-slate-400 font-semibold">
                        Phase {idx + 1}
                      </span>
                      <span className="text-xs font-mono font-bold text-white tabular-nums">
                        ${m.amount.toLocaleString()}
                      </span>
                    </div>

                    <p className={`text-xs font-semibold line-clamp-1 mb-2 ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                      {m.title}
                    </p>

                    <div className="flex items-center justify-between text-[11px]">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${statusBadge.color}`}>
                        {statusBadge.text}
                      </span>
                      <span className="text-slate-400">Due {m.dueDate}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Primary Role-Aware Action Box */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
              <span>Milestone Action Gate</span>
              <span className="text-slate-400 font-mono text-[11px]">Role: {currentRole}</span>
            </h4>

            {/* Client: Fund to Escrow */}
            {currentMilestone.status === 'pending_funding' && (
              <div className="space-y-2">
                <p className="text-xs text-slate-300">
                  Deposit <strong className="text-white">${currentMilestone.amount.toLocaleString()}</strong> into the secure platform escrow vault to authorize the agency to begin work.
                </p>
                {currentRole === 'client' ? (
                  <button
                    onClick={handleFundMilestone}
                    className="w-full py-2.5 px-4 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-colors shadow-md shadow-indigo-600/20 cursor-pointer"
                  >
                    Deposit ${currentMilestone.amount.toLocaleString()} into Escrow
                  </button>
                ) : (
                  <div className="p-2.5 rounded-lg bg-slate-950 text-xs text-slate-400 border border-slate-800">
                    Awaiting client escrow deposit before sprint commences.
                  </div>
                )}
              </div>
            )}

            {/* Agency: Start Work */}
            {currentMilestone.status === 'funded' && (
              <div className="space-y-2">
                <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-900/40 text-xs text-indigo-300">
                  <ShieldCheck className="w-3.5 h-3.5 inline mr-1 text-indigo-400" />
                  <strong>Funds Secured:</strong> ${currentMilestone.amount.toLocaleString()} is locked in escrow.
                </div>
                {currentRole === 'agency' ? (
                  <button
                    onClick={handleStartWork}
                    className="w-full py-2.5 px-4 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-colors cursor-pointer"
                  >
                    Start Milestone Engineering
                  </button>
                ) : (
                  <p className="text-xs text-slate-400">
                    Funds are secured in escrow. Awaiting agency team sprint kickoff.
                  </p>
                )}
              </div>
            )}

            {/* In Progress */}
            {currentMilestone.status === 'in_progress' && (
              <div className="space-y-2">
                <p className="text-xs text-slate-300">
                  Milestone is currently being produced by the assigned studio engineers.
                </p>
                {currentRole === 'agency' ? (
                  <button
                    onClick={handleSubmitDeliverable}
                    className="w-full py-2.5 px-4 text-xs font-semibold text-white bg-sky-600 rounded-lg hover:bg-sky-500 transition-colors cursor-pointer"
                  >
                    Submit Deliverable for Client Review
                  </button>
                ) : (
                  <div className="p-2.5 rounded-lg bg-slate-950 text-xs text-slate-400 border border-slate-800">
                    Agency is actively building. You will be notified immediately when ready for review.
                  </div>
                )}
              </div>
            )}

            {/* In Review: The Pivotal Gate */}
            {currentMilestone.status === 'in_review' && (
              <div className="space-y-2.5">
                <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-900/40 text-xs text-amber-200">
                  <strong>Verification Required:</strong> Inspect the deliverable preview, verify the criteria, and release funds when satisfied.
                </div>

                {currentRole === 'client' ? (
                  <div className="space-y-2">
                    <button
                      onClick={handleApproveAndRelease}
                      className="w-full py-2.5 px-4 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-500 transition-colors shadow-md shadow-emerald-600/20 cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <Check className="w-4 h-4" />
                      <span>Approve & Release ${currentMilestone.amount.toLocaleString()}</span>
                    </button>

                    <button
                      onClick={() => setShowRevisionModal(true)}
                      className="w-full py-2 px-4 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700/80 rounded-lg transition-colors cursor-pointer"
                    >
                      Request Revisions (Round {currentMilestone.revisionRound + 1}/{currentMilestone.maxRevisions})
                    </button>
                  </div>
                ) : (
                  <div className="p-2.5 rounded-lg bg-slate-950 text-xs text-slate-400 border border-slate-800">
                    Deliverable is currently under review by {project.clientName}.
                  </div>
                )}
              </div>
            )}

            {/* Approved: Celebration & Invoice Access */}
            {currentMilestone.status === 'approved' && (
              <div className="space-y-2.5">
                <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-900/40 text-xs text-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5 inline mr-1 text-emerald-400" />
                  <strong>Milestone Completed:</strong> ${currentMilestone.amount.toLocaleString()} successfully transferred to agency.
                </div>
                <button
                  onClick={() => onOpenInvoice(currentMilestone, project)}
                  className="w-full py-2 px-4 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Download Tax Invoice (PDF)</span>
                </button>
              </div>
            )}

          </div>

        </div>

        {/* Right Column: Interactive Workspace & Deliverable Viewer */}
        <div className="lg:col-span-8 space-y-4">
          
          {/* Sub-Tabs: Deliverables, Criteria, Activity, Team */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab('deliverable')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  activeTab === 'deliverable'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                Visual Deliverable & Markup ({deliverable?.annotations?.length || 0})
              </button>

              <button
                onClick={() => setActiveTab('criteria')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  activeTab === 'criteria'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                Acceptance Criteria ({currentMilestone.acceptanceCriteria.length})
              </button>

              <button
                onClick={() => setActiveTab('activity')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  activeTab === 'activity'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                Audit Log & Events
              </button>

              <button
                onClick={() => setActiveTab('team')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  activeTab === 'team'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                Assigned Team ({project.assignedTeamMembers.length})
              </button>
            </div>

            {/* Interactive Pin Toggle Button when viewing deliverable */}
            {activeTab === 'deliverable' && deliverable && (
              <button
                onClick={() => {
                  setIsPlacingPin(!isPlacingPin);
                  setNewPinCoords(null);
                  setActivePin(null);
                }}
                className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  isPlacingPin
                    ? 'bg-rose-500 text-white shadow-sm shadow-rose-500/20'
                    : 'bg-indigo-600 text-white hover:bg-indigo-500'
                }`}
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{isPlacingPin ? 'Click Image to Place Pin' : 'Add Pin Feedback'}</span>
              </button>
            )}
          </div>

          {/* TAB 1: VISUAL DELIVERABLE WITH PIN-POINT MARKUP */}
          {activeTab === 'deliverable' && (
            <div className="space-y-4">
              {deliverable ? (
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm space-y-4 p-4">
                  
                  {/* Deliverable Meta Bar */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-white">{deliverable.title}</h3>
                        <span className="text-[11px] font-mono font-medium text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-900/40">
                          {deliverable.version}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{deliverable.description}</p>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-400 shrink-0">
                      <span>Submitted {deliverable.submissionDate}</span>
                      {deliverable.externalLink && (
                        <a
                          href={deliverable.externalLink}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 ml-2"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>Live Preview</span>
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Interactive Visual Canvas Container */}
                  <div className="relative rounded-lg overflow-hidden border border-slate-800 bg-slate-950">
                    {isPlacingPin && (
                      <div className="absolute top-3 left-3 z-30 bg-slate-950/90 border border-indigo-500 text-indigo-300 text-xs px-3 py-1.5 rounded-lg shadow-lg flex items-center gap-1.5 pointer-events-none">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Click anywhere on the preview to pin your comment</span>
                      </div>
                    )}

                    <div
                      onClick={handleImageClick}
                      className={`relative w-full ${isPlacingPin ? 'cursor-crosshair' : 'cursor-default'}`}
                    >
                      <img
                        src={deliverable.previewUrl}
                        alt={deliverable.title}
                        className="w-full h-auto object-cover select-none"
                      />

                      {/* Render Existing Pins */}
                      {deliverable.annotations?.map((pin, i) => (
                        <button
                          key={pin.id}
                          onClick={(e) => {
                            e.stopPropagation();
                            setActivePin(pin);
                            setNewPinCoords(null);
                          }}
                          style={{ left: `${pin.xPercent}%`, top: `${pin.yPercent}%` }}
                          className={`absolute -translate-x-1/2 -translate-y-1/2 flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold font-mono transition-transform hover:scale-110 shadow-lg cursor-pointer ${
                            pin.resolved
                              ? 'bg-slate-700 text-slate-300 border border-slate-600'
                              : 'bg-indigo-600 text-white border-2 border-white shadow-indigo-500/50'
                          }`}
                        >
                          {i + 1}
                        </button>
                      ))}

                      {/* Render Temporary New Pin Draft Indicator */}
                      {newPinCoords && (
                        <div
                          style={{ left: `${newPinCoords.x}%`, top: `${newPinCoords.y}%` }}
                          className="absolute -translate-x-1/2 -translate-y-1/2 flex items-center justify-center w-7 h-7 rounded-full bg-rose-500 text-white font-bold text-xs border-2 border-white animate-pulse"
                        >
                          +
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Draft Pin Comment Input Form */}
                  {newPinCoords && (
                    <div className="p-3.5 bg-slate-950 border border-indigo-500/60 rounded-lg space-y-2.5 animate-in fade-in duration-200">
                      <div className="flex items-center justify-between text-xs text-slate-300">
                        <span className="font-semibold text-white">Add Annotation at Pin Point ({newPinCoords.x}%, {newPinCoords.y}%)</span>
                        <button
                          onClick={() => setNewPinCoords(null)}
                          className="text-slate-400 hover:text-white"
                        >
                          Cancel
                        </button>
                      </div>
                      <textarea
                        rows={2}
                        value={newPinText}
                        onChange={(e) => setNewPinText(e.target.value)}
                        placeholder="e.g. Please refine color contrast on this header badge or adjust spacing..."
                        className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-400 resize-none"
                      />
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={handleSavePin}
                          disabled={!newPinText.trim()}
                          className="px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 disabled:opacity-40 transition-colors"
                        >
                          Save Feedback Pin
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Pin Inspector Card if pin is clicked */}
                  {activePin && (
                    <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-white">{activePin.author}</span>
                          <span className="text-[11px] text-slate-500">({activePin.authorRole})</span>
                          <span className="text-slate-600">·</span>
                          <span className="text-[11px] text-slate-400">
                            {new Date(activePin.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleToggleResolvePin(activePin.id)}
                            className={`px-2 py-0.5 text-[11px] rounded font-medium transition-colors ${
                              activePin.resolved
                                ? 'bg-slate-800 text-slate-300'
                                : 'bg-emerald-950 text-emerald-300 border border-emerald-800/40'
                            }`}
                          >
                            {activePin.resolved ? 'Mark Unresolved' : 'Resolve Pin'}
                          </button>
                          <button
                            onClick={() => setActivePin(null)}
                            className="text-slate-400 hover:text-white text-xs"
                          >
                            Close
                          </button>
                        </div>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{activePin.text}</p>
                    </div>
                  )}

                </div>
              ) : (
                <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                  <Layers className="w-8 h-8 text-slate-600 mx-auto" />
                  <h4 className="text-sm font-semibold text-white">No Deliverable Uploaded for This Phase Yet</h4>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Once the agency submits the build preview or design bundle, you will be able to review it with visual pinpoint annotations here.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: ACCEPTANCE CRITERIA */}
          {activeTab === 'criteria' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white">
                  Legally Binding Acceptance Criteria
                </h3>
                <span className="text-xs text-slate-400">
                  Phase {selectedMilestoneIndex + 1} of {project.milestones.length}
                </span>
              </div>

              <p className="text-xs text-slate-400">
                These criteria were codified in the Project Statement of Work (SOW). Both parties must verify every condition before escrow funds are released.
              </p>

              <div className="space-y-2.5">
                {currentMilestone.acceptanceCriteria.map((crit, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3 rounded-lg bg-slate-950 border border-slate-800/90 text-xs text-slate-200"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{crit}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: ACTIVITY & AUDIT LOG */}
          {activeTab === 'activity' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-white border-b border-slate-800 pb-3">
                Escrow & Delivery Audit Trail
              </h3>

              <div className="space-y-3">
                {project.activityLog.map((act) => (
                  <div
                    key={act.id}
                    className="flex items-start gap-3 p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-xs"
                  >
                    <div className="w-2 h-2 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                    <div className="space-y-0.5 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white">{act.action}</span>
                        <span className="text-[11px] text-slate-500 font-mono">{act.timestamp}</span>
                      </div>
                      <p className="text-slate-400 text-[11px]">
                        Actor: <span className="text-slate-300 font-medium">{act.actor}</span> ({act.role})
                      </p>
                      {act.details && (
                        <p className="text-slate-400 text-[11px] pt-1 border-t border-slate-800/40">
                          {act.details}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: ASSIGNED TEAM */}
          {activeTab === 'team' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-white border-b border-slate-800 pb-3">
                Assigned Studio Personnel
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {project.assignedTeamMembers.map((member) => (
                  <div
                    key={member.id}
                    className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg flex items-center gap-3 text-xs"
                  >
                    <img
                      src={member.avatarUrl}
                      alt={member.name}
                      className="w-10 h-10 rounded-full object-cover border border-slate-700 shrink-0"
                    />
                    <div className="space-y-1 overflow-hidden">
                      <h4 className="font-bold text-white truncate">{member.name}</h4>
                      <p className="text-slate-400 text-[11px] truncate">{member.role}</p>
                      <div className="flex items-center gap-2 text-[10px] text-slate-500">
                        <span>Capacity: {member.capacityPercent}%</span>
                        <span aria-hidden="true">·</span>
                        <span>{member.activeProjectsCount} Active Projects</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>

      {/* Revision Request Modal */}
      {showRevisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white">
              Request Specific Revisions (Round {currentMilestone.revisionRound + 1} of {currentMilestone.maxRevisions})
            </h3>
            <p className="text-xs text-slate-400">
              Provide concrete feedback on what deliverables or acceptance criteria require refinement.
            </p>
            <textarea
              rows={4}
              value={revisionNotes}
              onChange={(e) => setRevisionNotes(e.target.value)}
              placeholder="Detail the exact adjustments required before approval..."
              className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 resize-none"
            />
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setShowRevisionModal(false)}
                className="px-3.5 py-1.5 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmRevision}
                disabled={!revisionNotes.trim()}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 disabled:opacity-40 cursor-pointer"
              >
                Send Revision to Agency
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
