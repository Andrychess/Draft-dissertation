import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { answersApi, sessionsApi } from "../api/client";
import { useDebouncedCallback } from "../hooks/useDebouncedCallback";

type Question = { id: number; text: string; max_score: number };

export default function AnswerForm() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const sheetId = Number(localStorage.getItem("sheet_id"));
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    sessionsApi.questions(Number(sessionId)).then((r) => setQuestions(r.data));
  }, [sessionId]);

  const saveOne = useCallback(
    async (questionId: number, text: string) => {
      if (!text.trim()) return;
      await answersApi.save({ sheet_id: sheetId, question_id: questionId, answer_text: text });
    },
    [sheetId]
  );

  const debouncedSave = useDebouncedCallback((questionId: number, text: string) => {
    void saveOne(questionId, text);
  }, 600);

  const submit = async () => {
    setSaving(true);
    try {
      await Promise.all(
        questions.map((q) => {
          const text = answers[q.id];
          return text?.trim() ? saveOne(q.id, text) : Promise.resolve();
        })
      );
      await answersApi.submit(sheetId);
      navigate(`/student/results/${sheetId}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container card">
      <h1>Ответы на вопросы</h1>
      {questions.map((q) => (
        <div key={q.id} style={{ marginBottom: "1.5rem" }}>
          <h3>
            {q.text} <small>(макс. {q.max_score})</small>
          </h3>
          <textarea
            rows={4}
            value={answers[q.id] || ""}
            onChange={(e) => {
              const text = e.target.value;
              setAnswers((prev) => ({ ...prev, [q.id]: text }));
              debouncedSave(q.id, text);
            }}
          />
        </div>
      ))}
      <button onClick={submit} disabled={saving}>
        {saving ? "Отправка…" : "Отправить на проверку"}
      </button>
    </div>
  );
}
