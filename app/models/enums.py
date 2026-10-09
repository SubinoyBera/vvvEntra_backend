from enum import StrEnum

# Rule: the DB stores the stable machine value ("under_10k"), never the display label
# ("Under $10,000"). Labels live in the frontend, so copy can change without a migration.


class UserRole(StrEnum):
    INVESTOR = "investor"      # "Investor / Buyer" tab on the login page
    ARCHITECT = "architect"    # "Architect / Creator" tab
    ADMIN = "admin"            # internal staff who approve members


class UserStatus(StrEnum):
    ONBOARDING = "onboarding"          # account exists, profile wizard not finished
    PENDING_REVIEW = "pending_review"  # profile submitted, waiting for admin approval
    ACTIVE = "active"                  # approved, can use the platform
    SUSPENDED = "suspended"            # blocked by an admin


# ---- Investor profile wizard (investor-only values; architects get their own enums) ----


class InvestorSector(StrEnum):
    B2B_SAAS = "b2b_saas"
    AI_AUTOMATION = "ai_automation"
    MARKETPLACES = "marketplaces"
    FINTECH = "fintech"
    CLIMATE_INDUSTRY = "climate_industry"
    D2C_CONSUMER = "d2c_consumer"
    OPERATIONS = "operations"
    HEALTHTECH = "healthtech"


class InvestorCapitalRange(StrEnum):
    UNDER_10K = "under_10k"      # Under $10,000
    FROM_10K_TO_50K = "10k_50k"  # $10,000 - $50,000
    FROM_50K_TO_250K = "50k_250k"  # $50,000 - $250,000
    FROM_250K_TO_1M = "250k_1m"  # $250,000 - $1M
    OVER_1M = "over_1m"          # Above $1M
    EXPLORING = "exploring"      # I'm exploring


class InvestorDeploymentTimeline(StrEnum):
    NOW = "now"
    WITHIN_3_MONTHS = "within_3_months"
    WITHIN_12_MONTHS = "within_12_months"
    EXPLORING = "exploring"      # I'm exploring


# ---- Architect profile wizard ----


class ArchitectDocDepth(StrEnum):
    DEPTH_90_120 = "90_120_pages"        # 90-120 pages
    DEPTH_120_150 = "120_150_pages"      # 120-150 pages
    DEPTH_150_PLUS = "150_plus_pages"    # 150+ pages
    STILL_PLANNING = "still_planning"    # I'm still planning it.


class ArchitectSubmissionTimeline(StrEnum):
    WITHIN_30_DAYS = "within_30_days"    # Within 30 days
    WITHIN_3_MONTHS = "within_3_months"  # Within 3 months
    LATER_THIS_YEAR = "later_this_year"  # Later this year
    EXPLORING = "exploring"              # I am exploring
