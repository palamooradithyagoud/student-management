export interface UserProfile {
  id: number;
  username: string;
  role: string;
  department: string;
  is_active: boolean;
  created_at: string;
}

export const DEFAULT_HOD_USER: UserProfile = {
  id: 1,
  username: 'hod.csm',
  role: 'HOD',
  department: 'CSM',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

export const setAuthSession = (_token?: string, _user?: any) => {
  // Authentication disabled; session is active by default
};

export const getAuthToken = (): string | null => {
  return 'open_access_token';
};

export const getAuthUser = (): UserProfile => {
  return DEFAULT_HOD_USER;
};

export const clearAuthSession = () => {
  // Authentication disabled
};

