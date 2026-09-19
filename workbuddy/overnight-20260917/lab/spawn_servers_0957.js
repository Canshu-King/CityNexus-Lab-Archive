// Detached spawner for delta verification: backend 8011 + vite 5181 from snapshot_0957
const { spawn } = require("child_process");
const SNAP = "D:\\moodle\\CityNexus-WorkBuddy\\overnight-20260917\\baseline\\app_snapshot_0957";
const PY = "D:\\moodle\\CityNexus\\.venv\\Scripts\\python.exe";
const NODE = "C:\\Users\\仓鼠王\\.workbuddy\\binaries\\node\\versions\\22.22.2-3\\node.exe";

const be = spawn(PY, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8011"], {
  cwd: SNAP + "\\backend",
  env: { ...process.env, CITYNEXUS_DATABASE_URL: "sqlite:///./citynexus.db" },
  detached: true,
  stdio: ["ignore", "ignore", "ignore"],
});
be.unref();
console.log("backend spawned pid", be.pid);

const fe = spawn(NODE, [SNAP + "\\frontend\\node_modules\\vite\\bin\\vite.js", "--port", "5181", "--strictPort"], {
  cwd: SNAP + "\\frontend",
  detached: true,
  stdio: ["ignore", "ignore", "ignore"],
});
fe.unref();
console.log("frontend spawned pid", fe.pid);
setTimeout(() => process.exit(0), 2000);
