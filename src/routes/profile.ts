import { Router } from "express";
import { requireCurrentUser } from "../middleware/auth.js";
import { AppError } from "../core/exceptions.js";
import {
  getArchitectProfile,
  getInvestorProfile,
  submitArchitectProfile,
  submitInvestorProfile,
} from "../services/profileService.js";
import {
  ArchitectDocDepth,
  ArchitectProfileIn,
  ArchitectSubmissionTimeline,
  InvestorCapitalRange,
  InvestorDeploymentTimeline,
  InvestorProfileIn,
  InvestorSector,
  UserRole,
} from "../types/index.js";

export const profileRouter = Router();

// GET /api/v1/profile/investor
profileRouter.get("/investor", requireCurrentUser, (req, res, next) => {
  try {
    const user = req.user!;
    if (user.role !== UserRole.INVESTOR) {
      throw new AppError("Only investor accounts have an investor profile.");
    }
    const profile = getInvestorProfile(user.id);
    if (!profile) {
      return res.status(404).json({ error: { code: "NOT_FOUND", message: "Investor profile not found." } });
    }
    res.json({
      user: {
        id: user.id,
        email: user.email,
        full_name: user.fullName,
        role: user.role,
        status: user.status,
      },
      profile: {
        focus: profile.focus,
        location: profile.location,
        sectors: profile.sectors,
        additional_notes: profile.additionalNotes,
        looking_for: profile.lookingFor,
        capital_range: profile.capitalRange,
        deployment_timeline: profile.deploymentTimeline,
      },
    });
  } catch (err) {
    next(err);
  }
});

// PUT /api/v1/profile/investor
profileRouter.put("/investor", requireCurrentUser, async (req, res, next) => {
  try {
    const user = req.user!;
    const body = req.body || {};

    const {
      full_name,
      focus,
      location,
      sectors,
      additional_notes,
      looking_for,
      capital_range,
      deployment_timeline,
    } = body;

    if (!full_name || typeof full_name !== "string" || full_name.trim().length < 2 || full_name.trim().length > 200) {
      throw new AppError("full_name must be between 2 and 200 characters.");
    }
    if (!focus || typeof focus !== "string" || focus.trim().length < 1 || focus.trim().length > 120) {
      throw new AppError("focus must be between 1 and 120 characters.");
    }
    if (!location || typeof location !== "string" || location.trim().length < 1 || location.trim().length > 120) {
      throw new AppError("location must be between 1 and 120 characters.");
    }
    if (!Array.isArray(sectors) || sectors.length === 0) {
      throw new AppError("sectors must be a non-empty array.");
    }

    const validSectors = Object.values(InvestorSector) as string[];
    for (const s of sectors) {
      if (!validSectors.includes(s)) {
        throw new AppError(`Invalid sector: ${s}`);
      }
    }

    if (!looking_for || typeof looking_for !== "string" || looking_for.trim().length < 1 || looking_for.trim().length > 2000) {
      throw new AppError("looking_for must be between 1 and 2000 characters.");
    }

    const validCapitalRanges = Object.values(InvestorCapitalRange) as string[];
    if (!validCapitalRanges.includes(capital_range)) {
      throw new AppError(`Invalid capital_range: ${capital_range}`);
    }

    const validTimelines = Object.values(InvestorDeploymentTimeline) as string[];
    if (!validTimelines.includes(deployment_timeline)) {
      throw new AppError(`Invalid deployment_timeline: ${deployment_timeline}`);
    }

    const profileData: InvestorProfileIn = {
      full_name: full_name.trim(),
      focus: focus.trim(),
      location: location.trim(),
      sectors: sectors as InvestorSector[],
      additional_notes: additional_notes ? String(additional_notes).trim().slice(0, 1000) : null,
      looking_for: looking_for.trim(),
      capital_range: capital_range as InvestorCapitalRange,
      deployment_timeline: deployment_timeline as InvestorDeploymentTimeline,
    };

    const profile = await submitInvestorProfile(user, profileData);

    res.json({
      user: {
        id: user.id,
        email: user.email,
        full_name: user.fullName,
        role: user.role,
        status: user.status,
      },
      profile: {
        focus: profile.focus,
        location: profile.location,
        sectors: profile.sectors,
        additional_notes: profile.additionalNotes,
        looking_for: profile.lookingFor,
        capital_range: profile.capitalRange,
        deployment_timeline: profile.deploymentTimeline,
      },
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/profile/architect
profileRouter.get("/architect", requireCurrentUser, (req, res, next) => {
  try {
    const user = req.user!;
    if (user.role !== UserRole.ARCHITECT) {
      throw new AppError("Only architect accounts have an architect profile.");
    }
    const profile = getArchitectProfile(user.id);
    if (!profile) {
      return res.status(404).json({ error: { code: "NOT_FOUND", message: "Architect profile not found." } });
    }
    res.json({
      user: {
        id: user.id,
        email: user.email,
        full_name: user.fullName,
        role: user.role,
        status: user.status,
      },
      profile: {
        headline: profile.headline,
        location: profile.location,
        sectors: profile.sectors,
        additional_notes: profile.additionalNotes,
        opportunity_description: profile.opportunityDescription,
        doc_depth: profile.docDepth,
        submission_timeline: profile.submissionTimeline,
      },
    });
  } catch (err) {
    next(err);
  }
});

// PUT /api/v1/profile/architect (Finish Architect Profile Wizard)
profileRouter.put("/architect", requireCurrentUser, async (req, res, next) => {
  try {
    const user = req.user!;
    const body = req.body || {};

    const {
      full_name,
      headline,
      location,
      sectors,
      additional_notes,
      opportunity_description,
      doc_depth,
      submission_timeline,
    } = body;

    // Step 1 validation: About you
    if (!full_name || typeof full_name !== "string" || full_name.trim().length < 2 || full_name.trim().length > 200) {
      throw new AppError("full_name must be between 2 and 200 characters.");
    }
    if (!headline || typeof headline !== "string" || headline.trim().length < 1 || headline.trim().length > 120) {
      throw new AppError("headline must be between 1 and 120 characters.");
    }
    if (!location || typeof location !== "string" || location.trim().length < 1 || location.trim().length > 120) {
      throw new AppError("location must be between 1 and 120 characters.");
    }

    // Step 2 validation: Your strengths
    if (!Array.isArray(sectors) || sectors.length === 0) {
      throw new AppError("sectors must be a non-empty array.");
    }
    const validSectors = Object.values(InvestorSector) as string[];
    for (const s of sectors) {
      if (!validSectors.includes(s)) {
        throw new AppError(`Invalid sector: ${s}`);
      }
    }

    // Step 3 validation: Your opportunity
    if (!opportunity_description || typeof opportunity_description !== "string" || opportunity_description.trim().length < 1 || opportunity_description.trim().length > 2000) {
      throw new AppError("opportunity_description must be between 1 and 2000 characters.");
    }

    const validDocDepths = Object.values(ArchitectDocDepth) as string[];
    if (!validDocDepths.includes(doc_depth)) {
      throw new AppError(`Invalid doc_depth: ${doc_depth}. Valid values: ${validDocDepths.join(", ")}`);
    }

    const validSubmissionTimelines = Object.values(ArchitectSubmissionTimeline) as string[];
    if (!validSubmissionTimelines.includes(submission_timeline)) {
      throw new AppError(`Invalid submission_timeline: ${submission_timeline}. Valid values: ${validSubmissionTimelines.join(", ")}`);
    }

    const profileData: ArchitectProfileIn = {
      full_name: full_name.trim(),
      headline: headline.trim(),
      location: location.trim(),
      sectors: sectors as InvestorSector[],
      additional_notes: additional_notes ? String(additional_notes).trim().slice(0, 1000) : null,
      opportunity_description: opportunity_description.trim(),
      doc_depth: doc_depth as ArchitectDocDepth,
      submission_timeline: submission_timeline as ArchitectSubmissionTimeline,
    };

    const profile = await submitArchitectProfile(user, profileData);

    res.json({
      user: {
        id: user.id,
        email: user.email,
        full_name: user.fullName,
        role: user.role,
        status: user.status,
      },
      profile: {
        headline: profile.headline,
        location: profile.location,
        sectors: profile.sectors,
        additional_notes: profile.additionalNotes,
        opportunity_description: profile.opportunityDescription,
        doc_depth: profile.docDepth,
        submission_timeline: profile.submissionTimeline,
      },
    });
  } catch (err) {
    next(err);
  }
});

