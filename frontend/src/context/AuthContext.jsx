import { createContext, useEffect, useMemo, useRef, useState } from "react";

import { supabase } from "../lib/supabase";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(undefined);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authIntent, setAuthIntent] = useState("");
  const pendingActionRef = useRef(null);

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
      authModalOpen,
      authIntent,
      openAuthModal(action, intent = "Sign in to continue this action.") {
        pendingActionRef.current = action || null;
        setAuthIntent(intent);
        setAuthModalOpen(true);
      },
      closeAuthModal() {
        pendingActionRef.current = null;
        setAuthIntent("");
        setAuthModalOpen(false);
      },
      async signIn(email, password) {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
          throw error;
        }
        setAuthModalOpen(false);
        setAuthIntent("");
        const pendingAction = pendingActionRef.current;
        pendingActionRef.current = null;
        if (pendingAction) {
          await pendingAction();
        }
        return data;
      },
      async signUp(email, password) {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) {
          throw error;
        }
        if (data.session) {
          setAuthModalOpen(false);
          setAuthIntent("");
          const pendingAction = pendingActionRef.current;
          pendingActionRef.current = null;
          if (pendingAction) {
            await pendingAction();
          }
        }
        return data;
      },
      async signOut() {
        const { error } = await supabase.auth.signOut();
        if (error) {
          throw error;
        }
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
    [authIntent, authModalOpen, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
