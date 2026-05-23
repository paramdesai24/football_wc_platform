import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="page-container" style={{ textAlign: "center", padding: "60px 20px" }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: 8 }}>404 — Page Not Found</h1>
      <p style={{ color: "var(--color-text-secondary)", marginBottom: 16, fontSize: "0.875rem" }}>
        The page you're looking for doesn't exist.
      </p>
      <Link to="/" className="btn btn-primary" style={{ textDecoration: "none" }}>
        Back to Dashboard
      </Link>
    </div>
  );
}
