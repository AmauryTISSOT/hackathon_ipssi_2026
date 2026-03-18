import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthCard from "../components/AuthCard";
import { register } from "../services/authApi";

function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    role: "user",
    password: "",
    confirmPassword: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => {
      const updated = {
        fullName: current.fullName,
        email: current.email,
        role: current.role,
        password: current.password,
        confirmPassword: current.confirmPassword
      };
      updated[name] = value;
      return updated;
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    const { fullName, email, role, password, confirmPassword } = form;

    if (password !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);
    try {
      await register({ fullName, email, password, role });
      setSuccess("Inscription reussie. Vous pouvez vous connecter.");
      setForm({
        fullName: "",
        email: "",
        role: "user",
        password: "",
        confirmPassword: ""
      });
      setTimeout(() => navigate("/connexion"), 500);
    } catch {
      setError("Impossible de finaliser l'inscription.");
    }

    setLoading(false);
  };

  return (
    <AuthCard
      title="Inscription"
      subtitle="Cree un compte pour gerer vos documents."
      onSubmit={handleSubmit}
      fields={[
        {
          name: "fullName",
          label: "Nom complet",
          type: "text",
          value: form.fullName,
          placeholder: "Prenom Nom",
          required: true,
          minLength: 2,
          onChange: handleChange
        },
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
          name: "role",
          label: "Type de compte",
          type: "select",
          value: form.role,
          required: true,
          onChange: handleChange,
          options: [
            { value: "user", label: "Utilisateur" },
            { value: "comptable", label: "Comptable" }
          ]
        },
        {
          name: "password",
          label: "Mot de passe",
          type: "password",
          value: form.password,
          placeholder: "Minimum 6 caracteres",
          required: true,
          minLength: 6,
          onChange: handleChange
        },
        {
          name: "confirmPassword",
          label: "Confirmer le mot de passe",
          type: "password",
          value: form.confirmPassword,
          placeholder: "Confirmer le mot de passe",
          required: true,
          minLength: 6,
          onChange: handleChange
        }
      ]}
      submitLabel="S'inscrire"
      loading={loading}
      error={error}
      success={success}
      footerText="Vous avez deja un compte ?"
      footerLinkTo="/connexion"
      footerLinkLabel="Se connecter"
    />
  );
}

export default RegisterPage;
