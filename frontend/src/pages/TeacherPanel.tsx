import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { sessionsApi, templatesApi } from "../api/client";

export default function TeacherPanel() {
  const [templates, setTemplates] = useState<{ id: number; name: string }[]>([]);
  const [sessions, setSessions] = useState<
    { id: number; name: string; connection_code: string; status: string }[]
  >([]);

  useEffect(() => {
    templatesApi.list().then((r) => setTemplates(r.data));
    sessionsApi.list().then((r) => setSessions(r.data));
  }, []);

  return (
    <div className="container">
      <div className="nav">
        {localStorage.getItem("role") === "admin" && <Link to="/admin">Админ</Link>}
        <a href="#" onClick={() => { localStorage.clear(); window.location.href = "/login"; }}>Выход</a>
      </div>
      <h1>Панель преподавателя</h1>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2>Шаблоны оценивания</h2>
        <Link className="btn" to="/templates/new">Создать шаблон</Link>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {templates.map((t) => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>{t.name}</td>
                <td>
                  <Link to={`/templates/${t.id}`}>Редактировать</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Сессии</h2>
        <Link className="btn" to="/sessions/new">Создать сессию</Link>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Код</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.name}</td>
                <td>{s.connection_code}</td>
                <td>{s.status}</td>
                <td>
                  <Link to={`/sessions/${s.id}/results`}>Результаты</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
