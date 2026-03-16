import { createContext, useContext, useMemo, useState } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(null);

  const value = useMemo(
    () => ({
      token,
      user,
      setUser,
      login: (newToken) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
      },
      logout: () => {
        localStorage.removeItem('token');
        setToken('');
        setUser(null);
      },
    }),
    [token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('认证上下文未初始化');
  }
  return ctx;
}
