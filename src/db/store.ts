import { User, RefreshTokenRecord, InvestorProfile, ArchitectProfile } from "../types/index.js";

// In-memory data store for AI Studio Node.js environment
class Store {
  public users = new Map<string, User>(); // userId -> User
  public usersByEmail = new Map<string, string>(); // lowercase email -> userId
  public usersByGoogleSub = new Map<string, string>(); // googleSub -> userId
  public refreshTokens = new Map<string, RefreshTokenRecord>(); // tokenHash -> RefreshTokenRecord
  public investorProfiles = new Map<string, InvestorProfile>(); // userId -> InvestorProfile
  public architectProfiles = new Map<string, ArchitectProfile>(); // userId -> ArchitectProfile

  clear() {
    this.users.clear();
    this.usersByEmail.clear();
    this.usersByGoogleSub.clear();
    this.refreshTokens.clear();
    this.investorProfiles.clear();
    this.architectProfiles.clear();
  }
}

export const store = new Store();
