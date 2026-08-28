export interface UserProfile {
  id: number;
  username: string;
  role: string;
  department: string;
  is_active: boolean;
  created_at: string;
}

export const setAuthSession = (token: string, user: any) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('csm_hod_token', token);
    localStorage.setItem('csm_hod_user', JSON.stringify(user));
  }
};

export const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('csm_hod_token');
  }
  return null;
};

export const getAuthUser = (): UserProfile | null => {
  if (typeof window !== 'undefined') {
    const raw = localStorage.getItem('csm_hod_user');
    if (raw) {
      try {
        return JSON.parse(raw);
      } catch {
        return null;
      }
    }
  }
  return null;
};

export const clearAuthSession = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('csm_hod_token');
    localStorage.removeItem('csm_hod_user');
    window.location.href = '/login';
  }
};
