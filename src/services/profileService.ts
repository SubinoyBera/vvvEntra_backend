import { ProfileLocked, WrongRole } from "../core/exceptions.js";
import { store } from "../db/store.js";
import {
  ArchitectProfile,
  ArchitectProfileIn,
  InvestorProfile,
  InvestorProfileIn,
  User,
  UserRole,
  UserStatus,
} from "../types/index.js";

export async function submitInvestorProfile(
  user: User,
  data: InvestorProfileIn
): Promise<InvestorProfile> {
  if (user.role !== UserRole.INVESTOR) {
    throw new WrongRole();
  }

  // Editable while onboarding or waiting for review; once approved/suspended it's locked
  if (user.status !== UserStatus.ONBOARDING && user.status !== UserStatus.PENDING_REVIEW) {
    throw new ProfileLocked();
  }

  const now = new Date().toISOString();
  let profile = store.investorProfiles.get(user.id);

  if (!profile) {
    profile = {
      userId: user.id,
      focus: data.focus,
      location: data.location,
      sectors: [...new Set(data.sectors)],
      additionalNotes: data.additional_notes || null,
      lookingFor: data.looking_for,
      capitalRange: data.capital_range,
      deploymentTimeline: data.deployment_timeline,
      createdAt: now,
      updatedAt: now,
    };
    store.investorProfiles.set(user.id, profile);
  } else {
    profile.focus = data.focus;
    profile.location = data.location;
    profile.sectors = [...new Set(data.sectors)];
    profile.additionalNotes = data.additional_notes || null;
    profile.lookingFor = data.looking_for;
    profile.capitalRange = data.capital_range;
    profile.deploymentTimeline = data.deployment_timeline;
    profile.updatedAt = now;
  }

  user.fullName = data.full_name;
  user.status = UserStatus.PENDING_REVIEW;
  user.updatedAt = now;

  return profile;
}

export async function submitArchitectProfile(
  user: User,
  data: ArchitectProfileIn
): Promise<ArchitectProfile> {
  if (user.role !== UserRole.ARCHITECT) {
    throw new WrongRole("This action is only available for architect accounts.");
  }

  // Editable while onboarding or waiting for review; once approved/suspended it's locked
  if (user.status !== UserStatus.ONBOARDING && user.status !== UserStatus.PENDING_REVIEW) {
    throw new ProfileLocked();
  }

  const now = new Date().toISOString();
  let profile = store.architectProfiles.get(user.id);

  if (!profile) {
    profile = {
      userId: user.id,
      headline: data.headline,
      location: data.location,
      sectors: [...new Set(data.sectors)],
      additionalNotes: data.additional_notes || null,
      opportunityDescription: data.opportunity_description,
      docDepth: data.doc_depth,
      submissionTimeline: data.submission_timeline,
      createdAt: now,
      updatedAt: now,
    };
    store.architectProfiles.set(user.id, profile);
  } else {
    profile.headline = data.headline;
    profile.location = data.location;
    profile.sectors = [...new Set(data.sectors)];
    profile.additionalNotes = data.additional_notes || null;
    profile.opportunityDescription = data.opportunity_description;
    profile.docDepth = data.doc_depth;
    profile.submissionTimeline = data.submission_timeline;
    profile.updatedAt = now;
  }

  user.fullName = data.full_name;
  user.status = UserStatus.PENDING_REVIEW;
  user.updatedAt = now;

  return profile;
}

export function getInvestorProfile(userId: string): InvestorProfile | null {
  return store.investorProfiles.get(userId) || null;
}

export function getArchitectProfile(userId: string): ArchitectProfile | null {
  return store.architectProfiles.get(userId) || null;
}

