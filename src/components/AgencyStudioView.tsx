import React, { useState } from 'react';
import { ShieldCheck, Users, Star, Award, TrendingUp, Plus, Check, Clock, ExternalLink } from 'lucide-react';
import { AgencyStudio, TeamMember } from '../types';

interface AgencyStudioViewProps {
  agency: AgencyStudio;
  onUpdateAgency: (updated: AgencyStudio) => void;
  onSelectProjectWorkspace: () => void;
}

export const AgencyStudioView: React.FC<AgencyStudioViewProps> = ({
  agency,
  onUpdateAgency,
  onSelectProjectWorkspace,
}) => {
  const [showAddMember, setShowAddMember] = useState(false);
  const [newMemberName, setNewMemberName] = useState('');
  const [newMemberRole, setNewMemberRole] = useState('');
  const [newMemberSkills, setNewMemberSkills] = useState('TypeScript, React, Node.js');

  const handleUpdateCapacity = (memberId: string, delta: number) => {
    const updatedMembers = agency.teamMembers.map((m) => {
      if (m.id === memberId) {
        const nextVal = Math.min(100, Math.max(10, m.capacityPercent + delta));
        return { ...m, capacityPercent: nextVal };
      }
      return m;
    });

    onUpdateAgency({ ...agency, teamMembers: updatedMembers });
  };

  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemberName.trim() || !newMemberRole.trim()) return;

    const newMember: TeamMember = {
      id: `team-${Date.now()}`,
      name: newMemberName,
      role: newMemberRole,
      avatarUrl: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=400&q=80',
      capacityPercent: 50,
      activeProjectsCount: 1,
      skills: newMemberSkills.split(',').map((s) => s.trim()),
    };

    onUpdateAgency({
      ...agency,
      teamMembers: [...agency.teamMembers, newMember],
    });

    setNewMemberName('');
    setNewMemberRole('');
    setShowAddMember(false);
  };

  return (
    <div className="space-y-6">
      
      {/* Studio Header Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <img
              src={agency.avatarUrl}
              alt={agency.name}
              className="w-16 h-16 rounded-xl object-cover border-2 border-slate-700 shadow-md shrink-0"
            />
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-bold text-white">{agency.name}</h1>
                <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-semibold bg-indigo-950/60 border border-indigo-900/60 px-2.5 py-0.5 rounded-full">
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Top 1% Vetted Studio</span>
                </div>
              </div>
              <p className="text-xs text-indigo-300/90 font-medium">{agency.tagline}</p>
              <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">{agency.bio}</p>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-slate-950/70 border border-slate-800 p-4 rounded-xl text-xs shrink-0">
            <div>
              <span className="text-[11px] text-slate-400 block">Verified Earnings</span>
              <span className="text-base font-bold font-mono text-emerald-400 tabular-nums">
                ${agency.totalEarned.toLocaleString()}
              </span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div>
              <span className="text-[11px] text-slate-400 block">On-Time Delivery</span>
              <span className="text-base font-bold font-mono text-white tabular-nums">
                {agency.onTimeDeliveryRate}%
              </span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div>
              <span className="text-[11px] text-slate-400 block">Client NPS Rating</span>
              <div className="flex items-center gap-1 text-base font-bold font-mono text-amber-300">
                <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                <span>{agency.rating}</span>
                <span className="text-[11px] text-slate-400 font-normal">({agency.reviewsCount})</span>
              </div>
            </div>
          </div>
        </div>

        {/* Studio Specialties Tags */}
        <div className="mt-5 pt-4 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span className="font-semibold text-slate-300">Studio Core Competencies:</span>
          {agency.specialties.map((spec, i) => (
            <span key={i} className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-300 text-[11px]">
              {spec}
            </span>
          ))}
        </div>
      </div>

      {/* Multi-Seat Team & Bandwidth Capacity Management */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-400" />
              <span>Studio Engineering & Design Roster</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live capacity monitoring and project workload distribution across studio personnel
            </p>
          </div>

          <button
            onClick={() => setShowAddMember(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Team Member</span>
          </button>
        </div>

        {/* Team Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {agency.teamMembers.map((member) => (
            <div
              key={member.id}
              className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <img
                    src={member.avatarUrl}
                    alt={member.name}
                    className="w-11 h-11 rounded-full object-cover border border-slate-700 shrink-0"
                  />
                  <div>
                    <h3 className="text-xs font-bold text-white">{member.name}</h3>
                    <p className="text-xs text-slate-400">{member.role}</p>
                    <span className="text-[10px] text-indigo-400 font-mono mt-0.5 block">
                      Active on {member.activeProjectsCount} client project(s)
                    </span>
                  </div>
                </div>

                {/* Capacity Stepper */}
                <div className="text-right shrink-0">
                  <span className="text-[10px] text-slate-400 block mb-1">Bandwidth:</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleUpdateCapacity(member.id, -10)}
                      className="w-6 h-6 rounded bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white flex items-center justify-center cursor-pointer"
                      title="Decrease capacity"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-emerald-400 tabular-nums w-10 text-center">
                      {member.capacityPercent}%
                    </span>
                    <button
                      onClick={() => handleUpdateCapacity(member.id, 10)}
                      className="w-6 h-6 rounded bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white flex items-center justify-center cursor-pointer"
                      title="Increase capacity"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    member.capacityPercent > 80 ? 'bg-amber-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${member.capacityPercent}%` }}
                />
              </div>

              {/* Skills */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {member.skills.map((s, idx) => (
                  <span key={idx} className="text-[10px] px-2 py-0.5 bg-slate-900 border border-slate-800/80 rounded text-slate-300">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quality Standards & Escrow Protections */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1.5">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs">
            <Award className="w-4 h-4" />
            <span>Guaranteed SLA Sign-Off</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            All code commits and Figma prototypes are bound to predetermined acceptance criteria.
          </p>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1.5">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs">
            <ShieldCheck className="w-4 h-4" />
            <span>Instant Escrow Payouts</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Funds deposited prior to work commencement are guaranteed with automated 7-day anti-ghosting protection.
          </p>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1.5">
          <div className="flex items-center gap-2 text-sky-400 font-semibold text-xs">
            <TrendingUp className="w-4 h-4" />
            <span>Transparent Telemetry</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Clients view live milestone progress, burndown charts, and review builds on staging sandboxes.
          </p>
        </div>
      </div>

      {/* Add Member Modal */}
      {showAddMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <form
            onSubmit={handleAddMember}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 max-w-md w-full shadow-2xl space-y-4"
          >
            <h3 className="text-sm font-bold text-white">Add Studio Team Member</h3>
            <p className="text-xs text-slate-400">
              Assign team members to projects and allocate bandwidth limits.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={newMemberName}
                  onChange={(e) => setNewMemberName(e.target.value)}
                  placeholder="e.g. Liam Sterling"
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Role Title</label>
                <input
                  type="text"
                  required
                  value={newMemberRole}
                  onChange={(e) => setNewMemberRole(e.target.value)}
                  placeholder="e.g. Senior Frontend Architect"
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Key Skills (comma separated)</label>
                <input
                  type="text"
                  value={newMemberSkills}
                  onChange={(e) => setNewMemberSkills(e.target.value)}
                  placeholder="React, Next.js, Node.js"
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowAddMember(false)}
                className="px-3.5 py-1.5 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 cursor-pointer"
              >
                Save Member
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
};
