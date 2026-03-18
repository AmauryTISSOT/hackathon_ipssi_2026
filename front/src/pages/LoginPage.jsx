import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthCard from "../components/AuthCard";
import { login } from "../services/authApi";

function getRoleRedirect(role) {
  if (role === "comptable") return "/comptable/depot";
  return "/user/depot";
}

function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: "",
    password: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => {
      const updated = {
        email: current.email,
        password: current.password
      };
      updated[name] = value;
      return updated;
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const response = await login(form);
      const userRole = response.user.role;
      setSuccess("Connexion reussie.");
      navigate(getRoleRedirect(userRole));
    } catch {
      setError("Impossible de se connecter.");
    }

    setLoading(false);
  };

  return (
    <AuthCard
      title="Connexion"
      subtitle="Accede a la plateforme avec vos identifiants."
      onSubmit={handleSubmit}
      fields={[
        {
          name: "email",
          label: "Email",
          type: "email",
          value: form.email,
          placeholder: "exemple@domaine.com",
          required: true,
          onChange: handleChange
        },
        {
          name: "password",
          label: "Mot de passe",
          type: "password",
          value: form.password,
          placeholder: "Votre mot de passe",
          required: true,
          minLength: 6,
          onChange: handleChange
        }
      ]}
      submitLabel="Se connecter"
      loading={loading}
      error={error}
      success={success}
      footerText="Pas encore de compte ?"
      footerLinkTo="/inscription"
      footerLinkLabel="Creer un compte"
    />
  );
}

export default LoginPage;
