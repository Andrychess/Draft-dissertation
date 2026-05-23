import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { resultsApi } from "../api/client";

type Detail = {
  sheet_id: number;
  question_id: number;
  student_name: string;
  answer_text: string | null;
  ai_result: {
    check_id: number;
    score: number;
    confidence: number;
    verdict: string;
    explanation: string;
    weaknesses: string[];
    strengths: string[];
    model_version?: string | null;
    details?: Record<string, unknown> | null;
    corrected_score: number | null;
    approved_at?: string | null;
  } | null;
};

export default function ResultDetail() {
  const { sheetId } = useParams();
  const [items, setItems] = useState<Detail[]>([]);
  const form = useForm({ defaultValues: { corrected_score: 0, explanation: "" } });

  const load = () => resultsApi.detail(Number(sheetId)).then((r) => setItems(r.data));

  useEffect(() => {
    load();
  }, [sheetId]);

  return (
    <div className="container">
      <Link to="/teacher">← Назад</Link>
      <div className="card">
        <h1>Детали работы #{sheetId}</h1>
        {items.map((item) => (
          <div key={item.question_id} style={{ marginBottom: "2rem", borderBottom: "1px solid #eee", paddingBottom: "1rem" }}>
            <h3>Вопрос #{item.question_id}</h3>
            <p>
              <strong>Студент:</strong> {item.student_name}
            </p>
            <p>
              <strong>Ответ:</strong> {item.answer_text || "—"}
            </p>
            {item.ai_result && (
              <>
                <p>
                  <strong>Оценка ИИ:</strong> {item.ai_result.score} (уверенность {item.ai_result.confidence}) —{" "}
                  {item.ai_result.verdict}
                </p>
                <p>{item.ai_result.explanation}</p>
                {item.ai_result.weaknesses?.length > 0 && (
                  <p>
                    <strong>Слабые стороны:</strong> {item.ai_result.weaknesses.join("; ")}
                  </p>
                )}
                {item.ai_result.strengths?.length > 0 && (
                  <p>
                    <strong>Сильные стороны:</strong> {item.ai_result.strengths.join("; ")}
                  </p>
                )}
                {item.ai_result.model_version && (
                  <p>
                    <strong>Модель:</strong> {item.ai_result.model_version}
                  </p>
                )}
                {item.ai_result.details && (
                  <pre style={{ background: "#f5f5f5", padding: "0.75rem", overflow: "auto" }}>
                    {JSON.stringify(item.ai_result.details, null, 2)}
                  </pre>
                )}
                <form
                  onSubmit={form.handleSubmit(async (data) => {
                    await resultsApi.correct(item.ai_result!.check_id, data);
                    load();
                  })}
                >
                  <label>Скорректированный балл</label>
                  <input
                    type="number"
                    step="0.5"
                    defaultValue={item.ai_result.corrected_score ?? item.ai_result.score}
                    {...form.register("corrected_score", { valueAsNumber: true })}
                  />
                  <label>Комментарий</label>
                  <input {...form.register("explanation")} />
                  <button type="submit">Сохранить корректировку</button>
                  <button
                    type="button"
                    className="secondary"
                    onClick={async () => {
                      await resultsApi.approve(item.ai_result!.check_id);
                      load();
                    }}
                  >
                    Утвердить
                  </button>
                </form>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
