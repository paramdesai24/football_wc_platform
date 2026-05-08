import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "@/routes/constants";

export function Navbar() {
  const { pathname } = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50">
      {/* Primary FIFA bar */}
      <div className="nav-gradient">
        <div className="container-main flex items-center justify-between h-14">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-8 h-8 rounded-sm bg-white/10 flex items-center justify-center text-white font-display font-bold text-sm group-hover:bg-white/20 transition-colors">
              ⚽
            </div>
            <div className="flex flex-col">
              <span className="text-white font-display font-bold text-sm tracking-wide leading-none">
                FIFA WORLD CUP 2026™
              </span>
              <span className="text-white/50 text-[10px] font-medium tracking-widest uppercase leading-none mt-0.5">
                Intelligence Platform
              </span>
            </div>
          </Link>

          <div className="hidden lg:flex items-center gap-1">
            <span className="text-white/40 text-xs font-medium px-3 py-1.5 rounded-md bg-white/5">v0.1.0</span>
          </div>

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden text-white p-2 hover:bg-white/10 rounded-md transition-colors"
            aria-label="Toggle menu"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              {mobileOpen ? (
                <path d="M5 5L15 15M5 15L15 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              ) : (
                <>
                  <path d="M3 5H17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M3 10H17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M3 15H17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Secondary nav */}
      <nav className="bg-white border-b border-surface-border shadow-[0_1px_0_rgba(26,42,68,0.08)]">
        <div className="container-main">
          <div className="hidden lg:flex items-center gap-0 h-12 overflow-x-auto">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "relative px-4 h-full flex items-center text-body-sm font-medium transition-colors whitespace-nowrap",
                    isActive ? "text-fifa-navy" : "text-text-secondary hover:text-fifa-navy",
                  )}
                >
                  {item.label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-fifa-blue"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="lg:hidden bg-white border-b border-surface-border overflow-hidden"
          >
            <div className="container-main py-2">
              {NAV_ITEMS.map((item) => {
                const isActive = pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      "flex items-center px-4 py-3 rounded-md text-body-md font-medium transition-colors",
                      isActive ? "bg-fifa-light/50 text-fifa-navy" : "text-text-secondary hover:bg-surface-hover hover:text-fifa-navy",
                    )}
                  >
                    {isActive && <span className="w-1 h-4 bg-fifa-blue rounded-full mr-3" />}
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
