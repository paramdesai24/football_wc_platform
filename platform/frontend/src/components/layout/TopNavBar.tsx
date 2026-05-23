import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "@/routes/constants";

export function TopNavBar() {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(13, 17, 23, 0.94)",
        backdropFilter: "blur(10px)",
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "10px 20px",
          display: "flex",
          gap: 16,
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
        }}
      >
        {/* Logo */}
        <NavLink
          to="/"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            lineHeight: 1.1,
            fontWeight: 800,
            fontSize: "0.875rem",
            color: "var(--color-text)",
            textDecoration: "none",
          }}
        >
          <span>WC26 INTEL</span>
          <span style={{ fontSize: "0.7rem", color: "var(--color-text-secondary)", fontWeight: 500 }}>
            Football intelligence platform
          </span>
        </NavLink>

        <nav style={{ display: "flex", alignItems: "center", gap: 2 }}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) => (isActive ? "nav-active" : "nav-link")}
              style={({ isActive }) => ({
                padding: "7px 12px",
                borderRadius: 999,
                fontSize: "0.8125rem",
                fontWeight: 500,
                textDecoration: "none",
                color: isActive ? "var(--color-text)" : "var(--color-text-secondary)",
                background: isActive ? "var(--color-surface-hover)" : "transparent",
                border: isActive ? "1px solid var(--color-border)" : "1px solid transparent",
                transition: "all 0.15s",
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
