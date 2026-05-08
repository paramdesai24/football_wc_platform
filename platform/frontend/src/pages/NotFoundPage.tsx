import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "@/routes/constants";

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="container-main page-section min-h-screen flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center max-w-md"
      >
        <div className="mb-6">
          <div className="text-7xl mb-4">⚽</div>
          <h1 className="font-display text-heading-lg text-text-primary mb-2">
            404 - Page Not Found
          </h1>
          <p className="text-body-md text-text-secondary mb-6">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <div className="space-y-3">
          <button
            onClick={() => navigate(ROUTES.HOME)}
            className="w-full px-6 py-3 rounded-md bg-fifa-navy text-white font-display font-semibold text-body-md hover:bg-fifa-blue transition-colors"
          >
            Go to Home Dashboard
          </button>
          <button
            onClick={() => navigate(-1)}
            className="w-full px-6 py-3 rounded-md bg-surface-secondary text-text-primary border border-surface-border font-display font-semibold text-body-md hover:bg-surface-hover transition-colors"
          >
            Go Back
          </button>
        </div>

        <div className="mt-8 pt-6 border-t border-surface-border text-caption text-text-tertiary">
          <p>Need help? Check out the navigation menu or try another route.</p>
        </div>
      </motion.div>
    </div>
  );
}
