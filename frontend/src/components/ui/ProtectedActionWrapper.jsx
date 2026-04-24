import { useAuth } from "../../hooks/useAuth";

function ProtectedActionWrapper({ action, intent, children }) {
  const { isAuthenticated, openAuthModal } = useAuth();

  async function runAction() {
    if (isAuthenticated) {
      return action();
    }

    openAuthModal(action, intent);
    return undefined;
  }

  return children({
    runAction,
    isAuthenticated
  });
}

export default ProtectedActionWrapper;
