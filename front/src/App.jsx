import { Navigate, Route, Routes } from "react-router-dom";
import { getCurrentUser, isAuthenticated } from "./services/authApi";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ClientUploadPage from "./pages/ClientUploadPage";
import ClientRecapPage from "./pages/ClientRecapPage";
import ComptableUploadPage from "./pages/ComptableUploadPage";
import ComptableRecapPage from "./pages/ComptableRecapPage";

function getHomeRoute(role) {
  if (role === "comptable") return "/comptable/depot";
  return "/user/depot";
}

function RequireAuth({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/connexion" replace />;
  }
  return children;
}

function RequireRole({ allowedRoles, children }) {
  const currentUser = getCurrentUser();
  if (!currentUser) {
    return <Navigate to="/connexion" replace />;
  }

  if (!allowedRoles.includes(currentUser.role)) {
    return <Navigate to={getHomeRoute(currentUser.role)} replace />;
  }
  return children;
}

function App() {
  const currentUser = getCurrentUser();
  const connected = isAuthenticated();
  const currentRole = currentUser ? currentUser.role : "";
  const defaultConnectedRoute = getHomeRoute(currentRole);
  const authRedirect = connected ? defaultConnectedRoute : "/connexion";

  return (
    <Routes>
      <Route path="/" element={<Navigate to={authRedirect} replace />} />
      <Route path="/connexion" element={<LoginPage />} />
      <Route path="/inscription" element={<RegisterPage />} />
      <Route path="/accueil" element={<Navigate to={authRedirect} replace />} />
      <Route
        path="/user/depot"
        element={
          <RequireAuth>
            <RequireRole allowedRoles={["user"]}>
              <ClientUploadPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route
        path="/user/recap"
        element={
          <RequireAuth>
            <RequireRole allowedRoles={["user"]}>
              <ClientRecapPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route
        path="/comptable/depot"
        element={
          <RequireAuth>
            <RequireRole allowedRoles={["comptable"]}>
              <ComptableUploadPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route
        path="/comptable/gestion"
        element={
          <RequireAuth>
            <RequireRole allowedRoles={["comptable"]}>
              <ComptableRecapPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
