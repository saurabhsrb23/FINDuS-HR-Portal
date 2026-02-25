export default function HomePage() {
  return (
    <main
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        fontFamily: "system-ui, sans-serif",
        background: "#f8fafc",
      }}
    >
      <h1 style={{ fontSize: "2.5rem", color: "#2563EB", margin: 0 }}>
        FindUs
      </h1>
      <p style={{ color: "#64748b", marginTop: "0.5rem" }}>
        AI-Powered HR Portal — Foundation Ready ✓
      </p>
      <a
        href="http://localhost:8000/docs"
        style={{
          marginTop: "1.5rem",
          padding: "0.5rem 1.25rem",
          background: "#2563EB",
          color: "#fff",
          borderRadius: "6px",
          textDecoration: "none",
          fontSize: "0.875rem",
        }}
      >
        Open API Docs →
      </a>
    </main>
  );
}
