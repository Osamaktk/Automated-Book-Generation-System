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

    // Get initial session
    supabase.auth.getSession().then(({ data }) => {
      if (mounted) {
        setSession(data.session);
      }
    });

    // Listen for auth changes
    const {
      data: { subscription }
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      console.log("AUTH STATE CHANGE:", nextSession);
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

      // 🔥 FIXED LOGIN WITH DEBUG
      async signIn(email, password) {
        console.log("Attempting login with:", email, password);

        const { data, error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password: password.trim()
        });

        console.log("LOGIN RESPONSE:", data);
        console.log("LOGIN ERROR:", error);

        if (error) {
          alert("Login failed: " + error.message);
          throw error;
        }

        // Close modal after login
        setAuthModalOpen(false);
        setAuthIntent("");

        // Run pending action if exists
        const pendingAction = pendingActionRef.current;
        pendingActionRef.current = null;

        if (pendingAction) {
          await pendingAction();
        }

        return data;
      },

      // SIGN UP
      async signUp(email, password) {
        console.log("Attempting signup with:", email);

        const { data, error } = await supabase.auth.signUp({
          email: email.trim(),
          password: password.trim()
        });

        console.log("SIGNUP RESPONSE:", data);
        console.log("SIGNUP ERROR:", error);

        if (error) {
          alert("Signup failed: " + error.message);
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

      // LOGOUT
      async signOut() {
        const { error } = await supabase.auth.signOut();
        if (error) {
          alert("Logout failed: " + error.message);
          throw error;
        }
      },

      // RESET PASSWORD
      async resetPassword(email) {
        const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: window.location.origin
        });

        if (error) {
          alert("Reset failed: " + error.message);
          throw error;
        }

        return data;
      }
    }),
    [authIntent, authModalOpen, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}