import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { sessionsApi } from "../api/client";
import { getDeviceFingerprint } from "../utils/fingerprint";

type FormData = {
  connection_code: string;
  last_name: string;
  first_name: string;
  patronymic: string;
  group_cipher: string;
};

export default function SessionJoin() {
  const { register, handleSubmit } = useForm<FormData>();
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const onSubmit = async (data: FormData) => {
    setError("");
    try {
      await sessionsApi.checkCode(data.connection_code);
      const { data: join } = await sessionsApi.join({
        connection_code: data.connection_code,
        student_name: "",
        last_name: data.last_name,
        first_name: data.first_name,
        patronymic: data.patronymic || null,
        group_cipher: data.group_cipher || null,
        device_fingerprint: getDeviceFingerprint(),
      });
      localStorage.setItem("sheet_id", String(join.sheet_id));
      navigate(`/answer/${join.session_id}`);
    } catch {
      setError("Неверный код или сессия недоступна");
    }
  };

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 480, margin: "3rem auto" }}>
        <h1>Подключение к сессии</h1>
        <form onSubmit={handleSubmit(onSubmit)}>
          <label>Код подключения</label>
          <input {...register("connection_code", { required: true })} />
          <label>Фамилия</label>
          <input {...register("last_name", { required: true })} />
          <label>Имя</label>
          <input {...register("first_name", { required: true })} />
          <label>Отчество</label>
          <input {...register("patronymic")} />
          <label>Группа (шифр)</label>
          <input {...register("group_cipher")} />
          {error && <p className="error">{error}</p>}
          <button type="submit">Войти</button>
        </form>
        <p>
          <Link to="/login">Вход для преподавателя</Link>
        </p>
      </div>
    </div>
  );
}
