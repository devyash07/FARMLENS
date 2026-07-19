import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

// Initialize Sentry for frontend error tracking (optional)
try {
  const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
  const ENVIRONMENT = import.meta.env.MODE || "development";

  if (SENTRY_DSN) {
    import("@sentry/react").then((Sentry) => {
      Sentry.init({
        dsn: SENTRY_DSN,
        environment: ENVIRONMENT,
        integrations: [
          Sentry.browserTracingIntegration(),
          Sentry.replayIntegration({
            maskAllText: true,
            blockAllMedia: true,
          }),
        ],
        // Performance Monitoring
        tracesSampleRate: ENVIRONMENT === "production" ? 0.1 : 1.0,
        // Session Replay
        replaysSessionSampleRate: ENVIRONMENT === "production" ? 0.1 : 0.5,
        replaysOnErrorSampleRate: 1.0,
        // Don't send PII
        beforeSend(event) {
          if (event.user) {
            delete event.user.email;
            delete event.user.ip_address;
          }
          return event;
        },
      });
      console.log(`✅ Sentry initialized for ${ENVIRONMENT} environment`);
    });
  } else {
    console.warn("⚠️  Sentry DSN not configured - error tracking disabled");
  }
} catch (error) {
  console.warn("Failed to initialize Sentry:", error);
}

createRoot(document.getElementById("root")!).render(<App />);
