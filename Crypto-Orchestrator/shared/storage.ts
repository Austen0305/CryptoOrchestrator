import { User, InsertUser } from "./schema";

// Mock storage implementation
const users: Map<string, User> = new Map();
const refreshTokens: Map<string, string> = new Map();

export const storage = {
  async getUserById(id: string): Promise<User | null> {
    return users.get(id) || null;
  },

  async getUserByEmail(email: string): Promise<User | null> {
    for (const user of users.values()) {
      if (user.email === email) {
        return user;
      }
    }
    return null;
  },

  async createUser(userData: InsertUser): Promise<User> {
    const user: User = {
      ...userData,
      id: Math.random().toString(36).substr(2, 9),
      createdAt: Date.now(),
      updatedAt: Date.now()
    };
    users.set(user.id, user);
    return user;
  },

  async updateUser(id: string, updates: Partial<User>): Promise<User | null> {
    const user = users.get(id);
    if (user) {
      Object.assign(user, updates);
      user.updatedAt = Date.now();
      users.set(id, user);
      return user;
    }
    return null;
  },

  async storeRefreshToken(userId: string, token: string): Promise<void> {
    refreshTokens.set(userId, token);
  },

  async getRefreshToken(userId: string): Promise<string | null> {
    return refreshTokens.get(userId) || null;
  }
};