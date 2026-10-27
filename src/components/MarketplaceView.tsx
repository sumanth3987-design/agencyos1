import React, { useState } from 'react';
import { Search, Star, ShieldCheck, MapPin, DollarSign, Filter, ArrowUpRight, Sparkles, Building2 } from 'lucide-react';
import { AgencyStudio } from '../types';

interface MarketplaceViewProps {
  agencies: AgencyStudio[];
  onSelectAgencyForScoping: (agency: AgencyStudio) => void;
}

export const MarketplaceView: React.FC<MarketplaceViewProps> = ({
  agencies,
  onSelectAgencyForScoping,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSpecialty, setSelectedSpecialty] = useState<string>('All');

  const specialties = ['All', 'Fintech Core Systems', 'B2B SaaS Architecture', 'Design Systems', 'Three.js & WebGL', 'AI & Data Labs'];

  const filteredAgencies = agencies.filter((agency) => {
    const matchesSearch =
      agency.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agency.specialties.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase())) ||
      agency.tagline.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSpecialty =
      selectedSpecialty === 'All' ||
      agency.specialties.some((s) => s.toLowerCase().includes(selectedSpecialty.toLowerCase()));

    return matchesSearch && matchesSpecialty;
  });

  return (
    <div className="space-y-6">
      
      {/* Search & Hero Kicker */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Vetted Enterprise Agency Directory</h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl leading-relaxed">
              Every agency studio is audited for verified milestone completion history, code quality standards, and SLA compliance.
            </p>
          </div>

          <div className="relative w-full md:max-w-sm">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by studio, skill, or tech stack..."
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
        </div>

        {/* Filter Bar with Accessible Functional Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800/80">
          <span className="text-[11px] font-semibold text-slate-400 mr-2 flex items-center gap-1">
            <Filter className="w-3 h-3" />
            <span>Category:</span>
          </span>
          {specialties.map((spec) => (
            <button
              key={spec}
              onClick={() => setSelectedSpecialty(spec)}
              className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors cursor-pointer ${
                selectedSpecialty === spec
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              {spec}
            </button>
          ))}
        </div>
      </div>

      {/* Agency Studios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgencies.map((agency) => (
          <div
            key={agency.id}
            className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700/80 transition-all flex flex-col justify-between shadow-sm group"
          >
            <div>
              {/* Cover Showcase Image */}
              <div className="h-40 w-full overflow-hidden bg-slate-950 relative">
                <img
                  src={agency.coverMockupUrl}
                  alt={`${agency.name} Portfolio`}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-90"
                />
                <div className="absolute top-3 right-3 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded text-[11px] font-mono text-emerald-400 font-bold border border-emerald-900/60">
                  ${agency.hourlyRate}/hr
                </div>
              </div>

              {/* Agency Info */}
              <div className="p-5 space-y-3">
                <div className="flex items-start gap-3">
                  <img
                    src={agency.avatarUrl}
                    alt={agency.name}
                    className="w-12 h-12 rounded-xl object-cover border border-slate-700 shrink-0 -mt-8 relative z-10 bg-slate-900 shadow-md"
                  />
                  <div className="space-y-0.5 overflow-hidden">
                    <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors truncate">
                      {agency.name}
                    </h3>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                      <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="truncate">{agency.location}</span>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {agency.tagline}
                </p>

                {/* Performance Stats */}
                <div className="grid grid-cols-3 gap-2 py-2 border-y border-slate-800/80 text-center font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500 block font-sans">NPS Rating</span>
                    <div className="flex items-center justify-center gap-1 text-xs font-bold text-amber-400">
                      <Star className="w-3 h-3 fill-amber-400" />
                      <span>{agency.rating}</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block font-sans">On-Time</span>
                    <span className="text-xs font-bold text-white">{agency.onTimeDeliveryRate}%</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block font-sans">Delivered</span>
                    <span className="text-xs font-bold text-slate-300">{agency.completedProjectsCount} projects</span>
                  </div>
                </div>

                {/* Specialties */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {agency.specialties.slice(0, 3).map((spec, sIdx) => (
                    <span
                      key={sIdx}
                      className="text-[10px] px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400"
                    >
                      {spec}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div className="p-4 bg-slate-950/60 border-t border-slate-800/80 flex items-center justify-between gap-3">
              <span className="text-[11px] font-medium text-slate-400">
                Studio Status: <strong className="text-emerald-400">{agency.capacityLevel}</strong>
              </span>

              <button
                onClick={() => onSelectAgencyForScoping(agency)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-colors shadow-sm cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Scope With AI</span>
              </button>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
