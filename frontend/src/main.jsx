import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles.css";
import "./pinterest.css";
import "./theme-overrides.css";

createRoot(document.getElementById("root")).render(<App />);
