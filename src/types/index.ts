export type UserRole = 'client' | 'agency' | 'admin';

export type MilestoneStatus = 
  | 'pending_funding' // Waiting for client to deposit to escrow
  | 'funded'          // Money held in escrow, ready for agency to work
  | 'in_progress'     // Agency actively working
  | 'in_review'       // Deliverable submitted, waiting for client approval
  | 'approved'        // Client approved, funds released to agency
  | 'disputed';       // In arbitration

export interface AnnotationPin {
  id: string;
  xPercent: number; // percentage coordinate on deliverable image
  yPercent: number;
  author: string;
  authorRole: UserRole;
  text: string;
  timestamp: string;
  resolved: boolean;
}

export interface Deliverable {
  id: string;
  title: string;
  version: string;
  previewUrl: string;
  description: string;
  submissionDate: string;
  fileSize?: string;
  externalLink?: string;
  annotations: AnnotationPin[];
}

export interface Milestone {
  id: string;
  title: string;
  description: string;
  amount: number;
  dueDate: string;
  status: MilestoneStatus;
  acceptanceCriteria: string[];
  deliverable?: Deliverable;
  revisionRound: number;
  maxRevisions: number;
  releasedAt?: string;
  escrowDepositedAt?: string;
  autoReleaseDaysRemaining?: number;
}

export interface TeamMember {
  id: string;
  name: string;
  role: string;
  avatarUrl: string;
  capacityPercent: number;
  activeProjectsCount: number;
  skills: string[];
}

export interface Invoice {
  id: string;
  invoiceNumber: string;
  date: string;
  dueDate: string;
  clientName: string;
  clientCompany: string;
  clientAddress: string;
  agencyName: string;
  agencyAddress: string;
  projectName: string;
  milestoneTitle: string;
  amount: number;
  taxRatePercent: number;
  totalAmount: number;
  status: 'paid' | 'pending';
  transactionHash: string;
}

export interface ProjectContract {
  id: string;
  title: string;
  sowSummary: string;
  effectiveDate: string;
  ipTransferClause: string;
  confidentialityTerms: string;
  signedByClient: boolean;
  clientSignature?: string;
  clientSignedAt?: string;
  signedByAgency: boolean;
  agencySignature?: string;
  agencySignedAt?: string;
}

export interface Project {
  id: string;
  title: string;
  clientName: string;
  clientCompany: string;
  clientAvatar: string;
  agencyName: string;
  agencyAvatar: string;
  status: 'scoping' | 'active' | 'in_review' | 'completed' | 'disputed';
  category: string;
  totalBudget: number;
  escrowSecuredAmount: number;
  releasedAmount: number;
  startDate: string;
  targetEndDate: string;
  milestones: Milestone[];
  assignedTeamMembers: TeamMember[];
  contract: ProjectContract;
  activityLog: {
    id: string;
    action: string;
    actor: string;
    role: UserRole;
    timestamp: string;
    details?: string;
  }[];
}

export interface AgencyStudio {
  id: string;
  name: string;
  tagline: string;
  bio: string;
  location: string;
  avatarUrl: string;
  coverMockupUrl: string;
  hourlyRate: number;
  verifiedBadges: string[];
  onTimeDeliveryRate: number;
  completedProjectsCount: number;
  totalEarned: number;
  rating: number;
  reviewsCount: number;
  specialties: string[];
  capacityLevel: 'Available' | 'High Demand' | 'Booked';
  teamMembers: TeamMember[];
}

export type LeadStatus = 
  | 'queued' 
  | 'calling' 
  | 'qualified' 
  | 'meeting_booked' 
  | 'converted_to_project' 
  | 'unreachable' 
  | 'not_interested';

export interface Lead {
  id: string;
  name: string;
  title: string;
  company: string;
  email: string;
  phone: string;
  industry: string;
  source: string;
  estimatedBudget: number;
  detectedNeed: string;
  status: LeadStatus;
  fitScore: number; // 0 - 100
  lastCallDate?: string;
  callDurationSeconds?: number;
  keyInsights?: string[];
  campaignId: string;
}

export interface CallMessage {
  id: string;
  speaker: 'agent' | 'prospect';
  text: string;
  timestamp: string;
  sentiment?: 'positive' | 'neutral' | 'objection' | 'agreement';
  extractedEntity?: string;
}

export interface AgentPersona {
  id: string;
  name: string;
  title: string;
  tone: string;
  voiceGender: 'female' | 'male';
  scriptStrategy: string;
  objectionHandlingStrategy: string;
}

export interface CallingCampaign {
  id: string;
  name: string;
  targetIndustry: string;
  leadCount: number;
  dialsCompleted: number;
  meetingsBooked: number;
  pipelineValue: number;
  status: 'active' | 'paused' | 'completed';
  agentPersona: AgentPersona;
}
