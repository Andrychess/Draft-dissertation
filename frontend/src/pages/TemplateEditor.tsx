import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { templatesApi } from "../api/client";

type Question = { id: number; text: string; correct_answer: string; max_score: number };

export default function TemplateEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = !id || id === "new";
  const form = useForm({
    defaultValues: {
      name: "",
      weight_relevance: 0.25,
      weight_correctness: 0.35,
      weight_normativity: 0.2,
      weight_logic: 0.2,
    },
  });
  const qForm = useForm({ defaultValues: { text: "", correct_answer: "", max_score: 10 } });
  const [questions, setQuestions] = useState<Question[]>([]);

  useEffect(() => {
    if (!isNew) {
      templatesApi.get(Number(id)).then((r) => {
        form.reset({
          name: r.data.name,
          weight_relevance: r.data.weight_relevance ?? 0.25,
          weight_correctness: r.data.weight_correctness ?? 0.35,
          weight_normativity: r.data.weight_normativity ?? 0.2,
          weight_logic: r.data.weight_logic ?? 0.2,
        });
        setQuestions(r.data.questions || []);
      });
    }
  }, [id, isNew, form]);

  const saveTemplate = async (data: {
    name: string;
    weight_relevance: number;
    weight_correctness: number;
    weight_normativity: number;
    weight_logic: number;
  }) => {
    if (isNew) {
      const { data: tpl } = await templatesApi.create(data);
      navigate(`/templates/${tpl.id}`);
    } else {
      await templatesApi.update(Number(id), data);
    }
  };

  return (
    <div className="container">
      <Link to="/teacher">← Назад</Link>
      <div className="card">
        <h1>{isNew ? "Новый шаблон" : "Редактирование шаблона"}</h1>
        <form onSubmit={form.handleSubmit(saveTemplate)}>
          <label>Название</label>
          <input {...form.register("name", { required: true })} />
          <h3>Веса критериев ИИ</h3>
          <label>Релевантность</label>
          <input type="number" step="0.05" {...form.register("weight_relevance", { valueAsNumber: true })} />
          <label>Корректность</label>
          <input type="number" step="0.05" {...form.register("weight_correctness", { valueAsNumber: true })} />
          <label>Нормативность</label>
          <input type="number" step="0.05" {...form.register("weight_normativity", { valueAsNumber: true })} />
          <label>Логика</label>
          <input type="number" step="0.05" {...form.register("weight_logic", { valueAsNumber: true })} />
          <button type="submit">Сохранить</button>
        </form>

        {!isNew && (
          <>
            <h2>Вопросы</h2>
            <form
              onSubmit={qForm.handleSubmit(async (data) => {
                await templatesApi.addQuestion(Number(id), data);
                const { data: tpl } = await templatesApi.get(Number(id));
                setQuestions(tpl.questions);
                qForm.reset({ text: "", correct_answer: "", max_score: 10 });
              })}
            >
              <label>Текст вопроса</label>
              <textarea {...qForm.register("text")} rows={3} />
              <label>Эталонный ответ</label>
              <textarea {...qForm.register("correct_answer")} rows={3} />
              <label>Макс. балл</label>
              <input type="number" step="0.5" {...qForm.register("max_score", { valueAsNumber: true })} />
              <button type="submit">Добавить вопрос</button>
            </form>
            <ul>
              {questions.map((q) => (
                <li key={q.id}>
                  <strong>{q.text}</strong> (макс. {q.max_score})
                  <button
                    type="button"
                    className="secondary"
                    style={{ marginLeft: "1rem" }}
                    onClick={async () => {
                      await templatesApi.deleteQuestion(q.id);
                      const { data: tpl } = await templatesApi.get(Number(id));
                      setQuestions(tpl.questions);
                    }}
                  >
                    Удалить
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
