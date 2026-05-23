import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { studentApi } from "../api/client";

type Row = {
  question_id: number;
  question_text: string;
  max_score: number;
  answer_text: string | null;
  score: number | null;
  verdict: string | null;
  explanation: string | null;
  weaknesses: string[];
  strengths: string[];
  details: Record<string, unknown> | null;
};

export default function StudentResults() {
  const { sheetId } = useParams();
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const id = Number(sheetId);
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const { data: status } = await studentApi.status(id);
        if (status.ready) {
          const { data } = await studentApi.results(id);
          setRows(data);
          setReady(true);
          setLoading(false);
          return;
        }
      } catch {
        setLoading(false);
      }
      timer = setTimeout(poll, 2000);
    };
    poll();
    return () => clearTimeout(timer);
  }, [sheetId]);

  const total = rows.reduce((s, r) => s + (r.score ?? 0), 0);
  const max = rows.reduce((s, r) => s + r.max_score, 0);

  return (
    <div className="container card">
      <h1>Результаты проверки</h1>
      {loading && !ready && <p>Идёт проверка ответов ИИ…</p>}
      {ready && (
        <p>
          <strong>Итого:</strong> {total.toFixed(1)} / {max}
        </p>
      )}
      {rows.map((r) => (
        <div
          key={r.question_id}
          style={{ marginBottom: "1.5rem", borderBottom: "1px solid #eee", paddingBottom: "1rem" }}
        >
          <h3>{r.question_text}</h3>
          <p>
            <strong>Ваш ответ:</strong> {r.answer_text}
          </p>
          {r.score != null && (
            <>
              <p>
                <strong>Оценка:</strong> {r.score} / {r.max_score} — {r.verdict}
              </p>
              <p>{r.explanation}</p>
              {r.weaknesses?.length > 0 && (
                <p>
                  <strong>Замечания:</strong> {r.weaknesses.join("; ")}
                </p>
              )}
              {r.strengths?.length > 0 && (
                <p>
                  <strong>Сильные стороны:</strong> {r.strengths.join("; ")}
                </p>
              )}
            </>
          )}
        </div>
      ))}
      <Link to="/join">Новая сессия</Link>
    </div>
  );
}
