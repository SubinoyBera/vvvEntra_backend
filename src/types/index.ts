export enum UserRole {
  INVESTOR = "investor",
  ARCHITECT = "architect",
  ADMIN = "admin",
}

export enum UserStatus {
  ONBOARDING = "onboarding",
  PENDING_REVIEW = "pending_review",
  ACTIVE = "active",
  SUSPENDED = "suspended",
}

export enum InvestorSector {
  B2B_SAAS = "b2b_saas",
  AI_AUTOMATION = "ai_automation",
  MARKETPLACES = "marketplaces",
  FINTECH = "fintech",
  CLIMATE_INDUSTRY = "climate_industry",
  D2C_CONSUMER = "d2c_consumer",
  OPERATIONS = "operations",
  HEALTHTECH = "healthtech",
}

export enum InvestorCapitalRange {
  UNDER_10K = "under_10k",
  FROM_10K_TO_50K = "10k_50k",
  FROM_50K_TO_250K = "50k_250k",
  FROM_250K_TO_1M = "250k_1m",
  OVER_1M = "over_1m",
  EXPLORING = "exploring",
}

export enum InvestorDeploymentTimeline {
  NOW = "now",
  WITHIN_3_MONTHS = "within_3_months",
  WITHIN_12_MONTHS = "within_12_months",
  EXPLORING = "exploring",
}

export interface User {
  id: string;
  email: string;
  passwordHash: string | null;
  fullName: string | null;
  role: UserRole;
  status: UserStatus;
  emailVerifiedAt: string | null;
  googleSub: string | null;
  reviewedAt: string | null;
  reviewedById: string | null;
  lastLoginAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface GoogleAuthIn {
  credential: string; // Google ID Token (from Google Identity Services)
  role?: UserRole; // Target role for new registrations (default: investor)
  remember_me?: boolean;
}

export interface UserOut {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  status: UserStatus;
}

export interface RefreshTokenRecord {
  id: string;
  userId: string;
  tokenHash: string;
  familyId: string;
  rememberMe: boolean;
  expiresAt: Date;
  usedAt: Date | null;
  revokedAt: Date | null;
  createdAt: Date;
  userAgent: string | null;
  ipAddress: string | null;
}

export interface InvestorProfile {
  userId: string;
  focus: string;
  location: string;
  sectors: InvestorSector[];
  additionalNotes: string | null;
  lookingFor: string;
  capitalRange: InvestorCapitalRange;
  deploymentTimeline: InvestorDeploymentTimeline;
  createdAt: string;
  updatedAt: string;
}

export interface InvestorProfileIn {
  full_name: string;
  focus: string;
  location: string;
  sectors: InvestorSector[];
  additional_notes?: string | null;
  looking_for: string;
  capital_range: InvestorCapitalRange;
  deployment_timeline: InvestorDeploymentTimeline;
}

export enum ArchitectDocDepth {
  DEPTH_90_120 = "90_120_pages",
  DEPTH_120_150 = "120_150_pages",
  DEPTH_150_PLUS = "150_plus_pages",
  STILL_PLANNING = "still_planning",
}

export enum ArchitectSubmissionTimeline {
  WITHIN_30_DAYS = "within_30_days",
  WITHIN_3_MONTHS = "within_3_months",
  LATER_THIS_YEAR = "later_this_year",
  EXPLORING = "exploring",
}

export interface ArchitectProfile {
  userId: string;
  headline: string;
  location: string;
  sectors: InvestorSector[];
  additionalNotes: string | null;
  opportunityDescription: string;
  docDepth: ArchitectDocDepth;
  submissionTimeline: ArchitectSubmissionTimeline;
  createdAt: string;
  updatedAt: string;
}

export interface ArchitectProfileIn {
  full_name: string;
  headline: string;
  location: string;
  sectors: InvestorSector[];
  additional_notes?: string | null;
  opportunity_description: string;
  doc_depth: ArchitectDocDepth;
  submission_timeline: ArchitectSubmissionTimeline;
}

