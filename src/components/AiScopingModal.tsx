import React, { useState } from 'react';
import { Sparkles, X, CheckCircle2, ArrowRight, Layers, DollarSign, Calendar, Shield, AlertCircle, Plus, Trash2 } from 'lucide-react';
import { Milestone, Project } from '../types';

interface AiScopingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectCreated: (project: Project) => void;
}

const PRESET_TEMPLATES = [
  {
    title: 'Fintech Mobile App MVP',
    prompt: 'Build a production-ready iOS and Android mobile investment application with biometric login, real-time asset tracking, bank linking, and compliance-ready data security.',
    budget: 38000,
    durationWeeks: 8,
  },
  {
    title: 'B2B SaaS Analytics Overhaul',
    prompt: 'Redesign our enterprise SaaS analytics console with custom design tokens, sub-100ms dashboard queries, automated report generation, and role-based permissions.',
    budget: 45000,
    durationWeeks: 10,
  },
  {
    title: 'High-Performance E-Commerce & CMS',
    prompt: 'Migrate legacy storefront to headless Next.js architecture with instant faceted search, multi-currency checkout, and Shopify backend integration.',
    budget: 28000,
    durationWeeks: 6,
  },
];

export const AiScopingModal: React.FC<AiScopingModalProps> = ({
  isOpen,
  onClose,
  onProjectCreated,
}) => {
  const [projectTitle, setProjectTitle] = useState('Fintech Mobile App MVP');
  const [briefDescription, setBriefDescription] = useState(PRESET_TEMPLATES[0].prompt);
  const [targetBudget, setTargetBudget] = useState(38000);
  const [timelineWeeks, setTimelineWeeks] = useState(8);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedMilestones, setGeneratedMilestones] = useState<Milestone[] | null>(null);
  const [recommendedStack, setRecommendedStack] = useState<string[]>([]);
  const [mitigations, setMitigations] = useState<string[]>([]);

  if (!isOpen) return null;

  const handleApplyTemplate = (tpl: typeof PRESET_TEMPLATES[0]) => {
    setProjectTitle(tpl.title);
    setBriefDescription(tpl.prompt);
    setTargetBudget(tpl.budget);
    setTimelineWeeks(tpl.durationWeeks);
    setGeneratedMilestones(null);
  };

  const handleGenerateScope = () => {
    setIsGenerating(true);

    // Simulate intelligent scoping synthesis
    setTimeout(() => {
      const p1Amount = Math.round(targetBudget * 0.35);
      const p2Amount = Math.round(targetBudget * 0.40);
      const p3Amount = targetBudget - p1Amount - p2Amount;

      const milestones: Milestone[] = [
        {
          id: `m-gen-1-${Date.now()}`,
          title: 'Phase 1: Architecture, Wireframes & Core Schemas',
          description: `Detailed system design, Figma design tokens, and technical blueprint for ${projectTitle}.`,
          amount: p1Amount,
          dueDate: '2026-11-10',
          status: 'pending_funding',
          acceptanceCriteria: [
            'All primary screen wireframes approved in Figma with design tokens',
            'Relational database schema with indexes and migration scripts',
            'API contracts defined with OpenAPI / TypeScript types',
          ],
          revisionRound: 0,
          maxRevisions: 2,
        },
        {
          id: `m-gen-2-${Date.now()}`,
          title: 'Phase 2: Core Engine Development & User Workflows',
          description: `Full-stack implementation of primary user flows, state management, and external service integrations.`,
          amount: p2Amount,
          dueDate: '2026-12-05',
          status: 'pending_funding',
          acceptanceCriteria: [
            'Primary user dashboard and core transactional flows functional',
            'Authentication, authorization, and rate limiting in place',
            'Automated integration tests passing at >=80% code coverage',
          ],
          revisionRound: 0,
          maxRevisions: 2,
        },
        {
          id: `m-gen-3-${Date.now()}`,
          title: 'Phase 3: Security Hardening, E2E Testing & Production Deployment',
          description: `Comprehensive penetration testing, load testing, final polish, and turnkey deployment to cloud infrastructure.`,
          amount: p3Amount,
          dueDate: '2026-12-28',
          status: 'pending_funding',
          acceptanceCriteria: [
            'Passing security audit with zero critical vulnerabilities',
            'Automated CI/CD pipeline verified with rollback safety',
            'Full IP assignment, code repository transfer, and documentation handoff',
          ],
          revisionRound: 0,
          maxRevisions: 2,
        },
      ];

      setGeneratedMilestones(milestones);
      setRecommendedStack(['TypeScript', 'Next.js App Router', 'Tailwind CSS v4', 'PostgreSQL', 'Redis', 'Docker']);
      setMitigations([
        'Strict boundary on third-party API rate limits defined in Phase 1',
        'Maximum 2 revision cycles per milestone to eliminate scope creep',
        'Dual-lock escrow guarantees developer payment once criteria are validated',
      ]);
      setIsGenerating(false);
    }, 900);
  };

  const handleUpdateMilestoneAmount = (index: number, newAmount: number) => {
    if (!generatedMilestones) return;
    const updated = [...generatedMilestones];
    updated[index].amount = newAmount;
    setGeneratedMilestones(updated);
  };

  const handleAddMilestone = () => {
    if (!generatedMilestones) return;
    const newM: Milestone = {
      id: `m-gen-custom-${Date.now()}`,
      title: 'Additional Custom Deliverable Phase',
      description: 'Specific domain requirements agreed upon between client and agency.',
      amount: 5000,
      dueDate: '2027-01-15',
      status: 'pending_funding',
      acceptanceCriteria: ['Documented verification signed off by stakeholders'],
      revisionRound: 0,
      maxRevisions: 2,
    };
    setGeneratedMilestones([...generatedMilestones, newM]);
  };

  const handleRemoveMilestone = (index: number) => {
    if (!generatedMilestones || generatedMilestones.length <= 1) return;
    setGeneratedMilestones(generatedMilestones.filter((_, i) => i !== index));
  };

  const handleCommitProject = () => {
    if (!generatedMilestones) return;

    const totalCalculated = generatedMilestones.reduce((acc, m) => acc + m.amount, 0);

    const newProject: Project = {
      id: `proj-${Date.now()}`,
      title: projectTitle,
      clientName: 'Alexander Hayes',
      clientCompany: 'Velo Financial Technologies Inc.',
      clientAvatar: '/src/assets/images/client_founder_avatar_1792401016296.jpg',
      agencyName: 'Aether Digital & Engineering Studio',
      agencyAvatar: '/src/assets/images/agency_lead_avatar_1792401015439.jpg',
      status: 'active',
      category: 'Custom Engineering & Product Design',
      totalBudget: totalCalculated,
      escrowSecuredAmount: 0,
      releasedAmount: 0,
      startDate: new Date().toISOString().split('T')[0],
      targetEndDate: generatedMilestones[generatedMilestones.length - 1]?.dueDate || '2026-12-31',
      assignedTeamMembers: [],
      contract: {
        id: `contract-${Date.now()}`,
        title: `Standard SOW Agreement for ${projectTitle}`,
        sowSummary: briefDescription,
        effectiveDate: new Date().toISOString().split('T')[0],
        ipTransferClause: 'Full IP assignment transferred immediately upon escrow release of the final milestone.',
        confidentialityTerms: 'Mutual NDA and proprietary data non-disclosure in force.',
        signedByClient: true,
        clientSignature: 'A. Hayes (Digital Auth)',
        clientSignedAt: new Date().toISOString(),
        signedByAgency: true,
        agencySignature: 'S. Chen (Principal)',
        agencySignedAt: new Date().toISOString(),
      },
      activityLog: [
        {
          id: `act-${Date.now()}-1`,
          action: 'Project Scoped via AI Brief Engine',
          actor: 'Alexander Hayes',
          role: 'client',
          timestamp: new Date().toISOString().split('T')[0],
          details: `Generated ${generatedMilestones.length} milestones totaling $${totalCalculated.toLocaleString()}`,
        },
      ],
      milestones: generatedMilestones,
    };

    onProjectCreated(newProject);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden my-6">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/60 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">AI Project Scoping & Milestone Architect</h2>
              <p className="text-xs text-slate-400">
                Transform rough requirements into verified milestones, escrow schedules, and acceptance criteria
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content Scroll Area */}
        <div className="p-6 overflow-y-auto space-y-6">
          
          {/* Quick Preset Templates */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
              Start with an Industry SOW Template
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {PRESET_TEMPLATES.map((tpl, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleApplyTemplate(tpl)}
                  className={`text-left p-3 rounded-lg border transition-all text-xs ${
                    projectTitle === tpl.title
                      ? 'border-indigo-500/80 bg-indigo-950/30 text-white'
                      : 'border-slate-800 bg-slate-950/40 text-slate-300 hover:border-slate-700 hover:bg-slate-800/40'
                  }`}
                >
                  <p className="font-semibold text-white mb-1">{tpl.title}</p>
                  <p className="text-slate-400 line-clamp-2 text-[11px] mb-2">{tpl.prompt}</p>
                  <div className="flex items-center justify-between font-mono text-[11px] text-slate-400 border-t border-slate-800/60 pt-1.5">
                    <span>${tpl.budget.toLocaleString()}</span>
                    <span>{tpl.durationWeeks} weeks</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Input Form */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            <div className="md:col-span-6 space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Project Title</label>
              <input
                type="text"
                value={projectTitle}
                onChange={(e) => setProjectTitle(e.target.value)}
                placeholder="e.g. Enterprise Fintech Core App"
                className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            <div className="md:col-span-3 space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Target Budget (USD)</label>
              <div className="relative">
                <span className="absolute left-3 top-2 text-xs text-slate-500 font-mono">$</span>
                <input
                  type="number"
                  value={targetBudget}
                  onChange={(e) => setTargetBudget(Number(e.target.value))}
                  className="w-full pl-7 pr-3 py-2 text-xs font-mono tabular-nums bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            </div>

            <div className="md:col-span-3 space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Target Timeline (Weeks)</label>
              <input
                type="number"
                value={timelineWeeks}
                onChange={(e) => setTimelineWeeks(Number(e.target.value))}
                className="w-full px-3.5 py-2 text-xs font-mono tabular-nums bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            <div className="md:col-span-12 space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Project Requirements & Deliverable Scope</label>
              <textarea
                rows={3}
                value={briefDescription}
                onChange={(e) => setBriefDescription(e.target.value)}
                placeholder="Describe your user journeys, technical constraints, integrations, and compliance requirements..."
                className="w-full px-3.5 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 transition-colors leading-relaxed resize-none"
              />
            </div>
          </div>

          {/* Generate Button */}
          <div className="flex justify-end">
            <button
              onClick={handleGenerateScope}
              disabled={isGenerating || !briefDescription.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-colors disabled:opacity-50 cursor-pointer shadow-md shadow-indigo-600/20"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isGenerating ? 'Synthesizing Architecture & SOW...' : 'Synthesize Scope & Milestones'}</span>
            </button>
          </div>

          {/* Generated Result Breakdown */}
          {generatedMilestones && (
            <div className="space-y-5 border-t border-slate-800 pt-5">
              
              {/* Architecture & Tech Stack Pill Bar */}
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="font-semibold text-slate-200">Recommended Tech Architecture:</span>
                <div className="flex flex-wrap items-center gap-2 text-slate-300">
                  {recommendedStack.map((tech, i) => (
                    <React.Fragment key={i}>
                      <span>{tech}</span>
                      {i < recommendedStack.length - 1 && <span className="text-slate-600" aria-hidden="true">·</span>}
                    </React.Fragment>
                  ))}
                </div>
              </div>

              {/* Milestones list with edit capabilities */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Phased Milestone & Escrow Allocation ({generatedMilestones.length} Phases)
                  </h3>
                  <button
                    onClick={handleAddMilestone}
                    className="inline-flex items-center gap-1 text-[11px] font-medium text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer"
                  >
                    <Plus className="w-3 h-3" />
                    <span>Add Custom Phase</span>
                  </button>
                </div>

                <div className="space-y-2.5">
                  {generatedMilestones.map((m, idx) => (
                    <div
                      key={m.id}
                      className="p-3.5 bg-slate-950 border border-slate-800/90 rounded-lg hover:border-slate-700/80 transition-all space-y-2"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-300 text-[11px] font-mono font-bold">
                            {idx + 1}
                          </span>
                          <span className="text-xs font-bold text-white">{m.title}</span>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs text-slate-400">Escrow:</span>
                            <div className="relative">
                              <span className="absolute left-2 top-1 text-[11px] text-slate-500 font-mono">$</span>
                              <input
                                type="number"
                                value={m.amount}
                                onChange={(e) => handleUpdateMilestoneAmount(idx, Number(e.target.value))}
                                className="w-24 pl-5 pr-2 py-0.5 text-xs font-mono tabular-nums bg-slate-900 border border-slate-700 rounded text-emerald-400 font-medium"
                              />
                            </div>
                          </div>

                          <button
                            onClick={() => handleRemoveMilestone(idx)}
                            disabled={generatedMilestones.length <= 1}
                            className="text-slate-500 hover:text-rose-400 transition-colors disabled:opacity-20 cursor-pointer"
                            title="Remove Phase"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      <p className="text-xs text-slate-400">{m.description}</p>

                      {/* Criteria list */}
                      <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/60 space-y-1">
                        <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                          Enforceable Acceptance Criteria:
                        </span>
                        {m.acceptanceCriteria.map((crit, cIdx) => (
                          <div key={cIdx} className="flex items-start gap-1.5 text-xs text-slate-300">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                            <span>{crit}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Scope-Creep & Risk Mitigation */}
              <div className="p-3.5 rounded-lg bg-amber-950/20 border border-amber-900/40 text-xs text-amber-200/90 space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-amber-300">
                  <Shield className="w-3.5 h-3.5" />
                  <span>Scope-Creep Protection Guarantees</span>
                </div>
                {mitigations.map((mit, i) => (
                  <p key={i} className="text-amber-200/80 text-[11px]">
                    · {mit}
                  </p>
                ))}
              </div>

              {/* Summary and Confirmation */}
              <div className="flex items-center justify-between border-t border-slate-800 pt-4">
                <div>
                  <span className="text-xs text-slate-400 block">Total Scoped Budget:</span>
                  <span className="text-lg font-bold font-mono text-emerald-400 tabular-nums">
                    ${generatedMilestones.reduce((acc, m) => acc + m.amount, 0).toLocaleString()} USD
                  </span>
                </div>

                <button
                  onClick={handleCommitProject}
                  className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-500 transition-colors shadow-md shadow-emerald-600/20 cursor-pointer"
                >
                  <span>Commit SOW & Open Project Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

            </div>
          )}

        </div>

      </div>
    </div>
  );
};
