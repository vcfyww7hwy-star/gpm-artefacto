import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles/tokens.css";
import "./index.css";
import App from "./App";
import { initTheme } from "./lib/theme";

// Aplica la preferencia de tema guardada antes del primer render.
initTheme();

const container = document.getElementById("root");
if (!container) throw new Error("No existe #root");

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
