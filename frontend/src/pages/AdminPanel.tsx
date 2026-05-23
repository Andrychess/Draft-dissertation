import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { groupsApi, usersApi, adminApi, User } from "../api/client";

export default function AdminPanel() {
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<{ cipher: string; name: string }[]>([]);
  const userForm = useForm({ defaultValues: { email: "", password: "", full_name: "", role: "teacher" } });
  const groupForm = useForm({ defaultValues: { cipher: "", name: "" } });

  const settingsForm = useForm({
    defaultValues: { ai_timeout_sec: "60", passing_threshold: "0.6", confidence_threshold: "0.7" },
  });
  const [logs, setLogs] = useState<
    { id: number; created_at: string; action: string; message: string; ip_address?: string }[]
  >([]);

  const load = async () => {
    const [u, g, l, s] = await Promise.all([
      usersApi.list(),
      groupsApi.list(),
      adminApi.logs(),
      adminApi.settings(),
    ]);
    setUsers(u.data);
    setGroups(g.data);
    setLogs(l.data);
    settingsForm.reset(s.data);
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="container">
      <div className="nav">
        <Link to="/teacher">Панель преподавателя</Link>
        <a href="#" onClick={() => { localStorage.clear(); window.location.href = "/login"; }}>Выход</a>
      </div>
      <h1>Администрирование</h1>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2>Настройки системы</h2>
        <form
          onSubmit={settingsForm.handleSubmit(async (data) => {
            await adminApi.updateSettings(data);
            load();
          })}
        >
          <label>Таймаут ИИ (сек)</label>
          <input {...settingsForm.register("ai_timeout_sec")} />
          <label>Порог зачёта (0–1)</label>
          <input {...settingsForm.register("passing_threshold")} />
          <label>Порог уверенности (0–1)</label>
          <input {...settingsForm.register("confidence_threshold")} />
          <button type="submit">Сохранить настройки</button>
        </form>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2>Журнал событий</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Время</th>
              <th>Действие</th>
              <th>Сообщение</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{log.action}</td>
                <td>{log.message}</td>
                <td>{log.ip_address || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h2>Пользователи</h2>
        <form
          onSubmit={userForm.handleSubmit(async (data) => {
            await usersApi.create(data);
            userForm.reset();
            load();
          })}
        >
          <label>Email</label>
          <input {...userForm.register("email")} />
          <label>ФИО</label>
          <input {...userForm.register("full_name")} />
          <label>Пароль</label>
          <input type="password" {...userForm.register("password")} />
          <label>Роль</label>
          <select {...userForm.register("role")}>
            <option value="teacher">teacher</option>
            <option value="admin">admin</option>
          </select>
          <button type="submit">Создать</button>
        </form>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>ФИО</th>
              <th>Роль</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.email}</td>
                <td>{u.full_name}</td>
                <td>{u.role}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Учебные группы</h2>
        <form
          onSubmit={groupForm.handleSubmit(async (data) => {
            await groupsApi.create(data);
            groupForm.reset();
            load();
          })}
        >
          <label>Шифр</label>
          <input {...groupForm.register("cipher")} />
          <label>Название</label>
          <input {...groupForm.register("name")} />
          <button type="submit">Добавить группу</button>
        </form>
        <table>
          <thead>
            <tr>
              <th>Шифр</th>
              <th>Название</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.cipher}>
                <td>{g.cipher}</td>
                <td>{g.name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
