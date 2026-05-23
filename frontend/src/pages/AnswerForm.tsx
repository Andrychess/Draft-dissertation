import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { answersApi, sessionsApi } from "../api/client";

type Question = { id: number; text: string; max_score: number };

export default function AnswerForm() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const sheetId = Number(localStorage.getItem("sheet_id"));
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});

  useEffect(() => {
    sessionsApi.questions(Number(sessionId)).then((r) => setQuestions(r.data));
  }, [sessionId]);

  const save = async (questionId: number) => {
    const text = answers[questionId];
    if (!text) return;
    await answersApi.save({ sheet_id: sheetId, question_id: questionId, answer_text: text });
  };

  const submit = async () => {
    for (const q of questions) {
      await save(q.id);
    }
    await answersApi.submit(sheetId);
    navigate(`/student/results/${sheetId}`);
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
            onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
            onBlur={() => save(q.id)}
          />
        </div>
      ))}
      <button onClick={submit}>Отправить на проверку</button>
    </div>
  );
}
