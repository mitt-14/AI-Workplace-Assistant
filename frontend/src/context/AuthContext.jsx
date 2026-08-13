import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { api, authStorage } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(
    Boolean(authStorage.getToken()),
  );

  useEffect(() => {
    const token = authStorage.getToken();

    if (!token) {
      setLoading(false);
      return;
    }

    api
      .get("/auth/me")
      .then(setUser)
      .catch(() => {
        authStorage.clearToken();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    const result = await api.post("/auth/login", {
      email,
      password,
    });

    authStorage.setToken(result.access_token);
    setUser(result.user);
    return result.user;
  }

  async function register(name, email, password) {
    const result = await api.post("/auth/register", {
      name,
      email,
      password,
    });

    authStorage.setToken(result.access_token);
    setUser(result.user);
    return result.user;
  }

  function logout() {
    authStorage.clearToken();
    setUser(null);
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      authenticated: Boolean(user),
      login,
      register,
      logout,
    }),
    [user, loading],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}
