import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { groupsApi, sessionsApi, templatesApi } from "../api/client";
import StudentJoinActions from "../components/StudentJoinActions";

type CreatedSession = {
  id: number;
  name: string;
  connection_code: string;
};

export default function SessionForm() {
  const navigate = useNavigate();
  const { register, handleSubmit } = useForm({
    defaultValues: { name: "", template_id: "", group_ciphers: "" },
  });
  const [templates, setTemplates] = useState<{ id: number; name: string }[]>([]);
  const [created, setCreated] = useState<CreatedSession | null>(null);

  useEffect(() => {
    templatesApi.list().then((r) => setTemplates(r.data));
  }, []);

  const onSubmit = async (data: { name: string; template_id: string; group_ciphers: string }) => {
    const groups = await groupsApi.list();
    const ciphers = data.group_ciphers
      ? data.group_ciphers.split(",").map((s) => s.trim())
      : groups.data.map((g: { cipher: string }) => g.cipher);
    const { data: session } = await sessionsApi.create({
      name: data.name,
      template_id: Number(data.template_id),
      group_ciphers: ciphers,
    });
    setCreated({
      id: session.id,
      name: session.name,
      connection_code: session.connection_code,
    });
  };

  if (created) {
    return (
      <div className="container">
        <Link to="/teacher">← Назад</Link>
        <div className="card">
          <h1>Сессия создана</h1>
          <p>
            <strong>{created.name}</strong>
          </p>
          <p>
            Код подключения: <strong>{created.connection_code}</strong>
          </p>
          <StudentJoinActions connectionCode={created.connection_code} showUrl />
          <button
            type="button"
            className="secondary"
            style={{ marginTop: "1rem" }}
            onClick={() => navigate("/teacher")}
          >
            К списку сессий
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <Link to="/teacher">← Назад</Link>
      <div className="card">
        <h1>Новая сессия</h1>
        <form onSubmit={handleSubmit(onSubmit)}>
          <label>Название</label>
          <input {...register("name", { required: true })} />
          <label>Шаблон</label>
          <select {...register("template_id", { required: true })}>
            <option value="">— выберите —</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <label>Группы (шифры через запятую, пусто = все)</label>
          <input {...register("group_ciphers")} />
          <button type="submit">Создать</button>
        </form>
      </div>
    </div>
  );
}
