/**
 * E2E smoke test: login → template → session → student answer → AI check
 * Run: node scripts/e2e_test.mjs
 * Requires: backend :8000, ai-service :8001, postgres with migrations
 */
const API = process.env.API_URL || "http://localhost:8000";
const AI = process.env.AI_URL || "http://localhost:8001";

async function req(method, path, body, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) throw new Error(`${method} ${path} → ${res.status}: ${JSON.stringify(data)}`);
  return data;
}

async function waitForResults(token, sessionId, sheetId, attempts = 30) {
  for (let i = 0; i < attempts; i++) {
    const results = await req("GET", `/api/sessions/${sessionId}/results`, null, token);
    const row = results.find((r) => r.sheet_id === sheetId);
    if (row?.verdict) return row;
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error("AI results not ready in time");
}

async function main() {
  console.log("1. Health checks...");
  const aiHealth = await fetch(`${AI}/health`).then((r) => r.json());
  console.log("   ai-service:", aiHealth);

  const apiHealth = await fetch(`${API}/health`).then((r) => r.json());
  console.log("   backend:", apiHealth);

  console.log("2. Login...");
  const { access_token } = await req("POST", "/api/auth/login", {
    email: "admin@example.com",
    password: "admin123",
  });
  console.log("   OK");

  console.log("3. Create template + question...");
  const tpl = await req("POST", "/api/templates", { name: `E2E ${Date.now()}` }, access_token);
  await req(
    "POST",
    `/api/templates/${tpl.id}/questions`,
    {
      text: "Что такое ООП?",
      correct_answer: "Объектно-ориентированное программирование — парадигма с объектами и классами.",
      max_score: 10,
    },
    access_token
  );
  const tplFull = await req("GET", `/api/templates/${tpl.id}`, null, access_token);
  const questionId = tplFull.questions[0].id;
  console.log("   template", tpl.id, "question", questionId);

  console.log("4. Create session...");
  const session = await req(
    "POST",
    "/api/sessions",
    { name: "E2E Session", template_id: tpl.id, group_ciphers: [] },
    access_token
  );
  console.log("   code:", session.connection_code);

  console.log("5. Student join...");
  const join = await req("POST", "/api/sessions/join", {
    connection_code: session.connection_code,
    last_name: "Тестов",
    first_name: "Студент",
    patronymic: "Иванович",
    group_cipher: null,
    device_fingerprint: "e2e-test-device",
  });
  const { sheet_id, session_id } = join;
  console.log("   sheet_id:", sheet_id);

  console.log("6. Save & submit answer...");
  await req("POST", "/api/answers/save", {
    sheet_id,
    question_id: questionId,
    answer_text: "ООП — это программирование с объектами, инкапсуляцией и наследованием.",
  });
  await req("POST", "/api/answers/submit", { sheet_id });
  console.log("   submitted");

  console.log("7. Wait for AI results...");
  const row = await waitForResults(access_token, session_id, sheet_id);
  console.log("   result:", row);

  const details = await req("GET", `/api/results/${sheet_id}`, null, access_token);
  console.log("8. Details:", JSON.stringify(details, null, 2));

  console.log("\n✅ E2E PASSED");
}

main().catch((e) => {
  console.error("\n❌ E2E FAILED:", e.message);
  process.exit(1);
});
