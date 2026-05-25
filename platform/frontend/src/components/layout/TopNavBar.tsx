import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "@/routes/constants";

function NavIcon() {
  const PRIMARY = "https://imgs.search.brave.com/M6EmsapjvWCxIaGgnWVVtsZoHw5_wrlpPi-8hIOVZug/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9jZG4u/cHJvZC53ZWJzaXRl/LWZpbGVzLmNvbS82/OGY1NTA5OTI1NzBj/YTAzMjI3MzdkYzIv/NjlmNGE4MmUzNjg1/NzMxYTNhYjUwODZlX2ZpZmEtd29ybGQtY3VwLTIwMjYtb2Zm/aWNpYWwtbG9nby1m/b290eWxvZ29zLXdo/aXRlLnBuZw";
  const FALLBACK = "/worldcup_icon.webp";
  const [src, setSrc] = useState(PRIMARY);

  useEffect(() => {
    const img = new window.Image();
    img.src = PRIMARY;
    img.onerror = () => setSrc(FALLBACK);
  }, []);

  return (
    <img
      src={src}
      alt=""
      width={32}
      height={32}
      style={{ width: 32, height: 32, objectFit: "contain", flexShrink: 0 }}
      onError={() => setSrc(FALLBACK)}
    />
  );
}

export function TopNavBar() {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(5, 13, 26, 0.82)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "0 20px",
          display: "flex",
          gap: 6,
          alignItems: "center",
          justifyContent: "space-between",
          height: 56,
          flexWrap: "nowrap",
        }}
      >
        <NavLink
          to="/"
          className="nav-brand"
          style={{
            display: "flex",
            flexDirection: "row",
            gap: 10,
            lineHeight: 1.1,
            textDecoration: "none",
            alignItems: "center",
          }}
        >
          <NavIcon />
          <span className="nav-brand-name">FC Analytics</span>
        </NavLink>

        <nav className="nav-links">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) => `nav-link${item.path === "/play-as-team" ? " nav-link-cta" : ""}${item.path === "/about" ? " nav-link-cta nav-link-about" : ""}${isActive ? " active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
