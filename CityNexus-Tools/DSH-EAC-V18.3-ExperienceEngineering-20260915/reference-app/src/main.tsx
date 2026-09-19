import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { LocaleProvider } from "./i18n";
import { ExperienceAdapterProvider } from "./adapters/ExperienceAdapterContext";
import { registerExperienceServiceWorker } from "./pwa/serviceWorker";
import "./styles/tokens.css";
import "./styles/global.css";
import "./styles/experience.css";

const root = document.getElementById("root");
if (!root) throw new Error("CityNexus V18.3 reference root element is missing");

createRoot(root).render(
  <StrictMode>
    <LocaleProvider>
      <ExperienceAdapterProvider>
        <App />
      </ExperienceAdapterProvider>
    </LocaleProvider>
  </StrictMode>,
);

registerExperienceServiceWorker();
