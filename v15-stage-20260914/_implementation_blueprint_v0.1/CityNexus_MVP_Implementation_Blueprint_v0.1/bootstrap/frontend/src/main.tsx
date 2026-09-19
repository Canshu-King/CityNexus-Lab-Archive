import React from "react";
import ReactDOM from "react-dom/client";

function App() {
  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 960, margin: "0 auto", padding: 24 }}>
      <h1>CityNexus</h1>
      <p>MVP bootstrap. Implement WP08 after the backend vertical slice is stable.</p>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
