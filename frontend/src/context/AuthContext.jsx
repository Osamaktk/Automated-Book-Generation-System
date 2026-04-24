import { createContext, useEffect, useMemo, useState } from "react";

import { supabase } from "../lib/supabase";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(undefined);

  useEffect(() => {
    let mounted = true;

    supabase.auth.getSession().then(({ data }) => {
      if (mounted) {
        setSession(data.session);
      }
    });

    const {
      data: { subscription }
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      accessToken: session?.access_token ?? null,
      isAuthenticated: Boolean(session?.user),
      isLoading: session === undefined,
      async signIn(email, password) {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
          throw error;
        }
        return data;
      },
      async signUp(email, password) {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) {
          throw error;
        }
        return data;
      },
      async signOut() {
        const { error } = await supabase.auth.signOut();
        if (error) {
          throw error;
        }
      },
      async sendMagicLink(email) {
        const { data, error } = await supabase.auth.signInWithOtp({
          email,
          options: {
            emailRedirectTo: window.location.origin
          }
        });
        if (error) {
          throw error;
        }
        return data;
      },
      async resetPassword(email) {
        const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: window.location.origin
        });
        if (error) {
          throw error;
        }
        return data;
      }
    }),
    [session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
