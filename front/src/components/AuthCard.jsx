import { Link } from "react-router-dom";

function AuthCard({
  title,
  subtitle,
  onSubmit,
  fields,
  submitLabel,
  loading,
  error,
  success,
  footerText,
  footerLinkTo,
  footerLinkLabel
}) {
  return (
    <main className="auth-layout">
      <section className="auth-card">
        <h1>{title}</h1>
        <p className="auth-subtitle">{subtitle}</p>

        <form onSubmit={onSubmit} className="auth-form">
          {fields.map((field) => (
            <label key={field.name} className="auth-field">
              <span>{field.label}</span>
              {field.type === "select" ? (
                <select
                  name={field.name}
                  value={field.value}
                  onChange={field.onChange}
                  required={field.required}
                >
                  {field.options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  name={field.name}
                  type={field.type}
                  value={field.value}
                  onChange={field.onChange}
                  placeholder={field.placeholder}
                  required={field.required}
                  minLength={field.minLength}
                />
              )}
            </label>
          ))}

          {error ? <p className="message error">{error}</p> : null}
          {success ? <p className="message success">{success}</p> : null}

          <button type="submit" disabled={loading} className="submit-button">
            {loading ? "Chargement..." : submitLabel}
          </button>
        </form>

        <p className="auth-footer">
          {footerText} <Link to={footerLinkTo}>{footerLinkLabel}</Link>
        </p>
      </section>
    </main>
  );
}

export default AuthCard;
