import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { authApi } from "../api/client";

type FormData = { email: string; password: string };

export default function LoginPage() {
  const { register, handleSubmit } = useForm<FormData>();
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const onSubmit = async (data: FormData) => {
    setError("");
    try {
      const { data: tokens } = await authApi.login(data.email, data.password);
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      const payload = JSON.parse(atob(tokens.access_token.split(".")[1]));
      const role = payload.role || "teacher";
      localStorage.setItem("role", role);
      navigate(role === "admin" ? "/admin" : "/teacher");
    } catch {
      setError("Неверный email или пароль");
    }
  };

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 420, margin: "4rem auto" }}>
        <h1>AutoAssess</h1>
        <p>Вход для преподавателя или администратора</p>
        <form onSubmit={handleSubmit(onSubmit)}>
          <label>Email</label>
          <input type="email" {...register("email", { required: true })} />
          <label>Пароль</label>
          <input type="password" {...register("password", { required: true })} />
          {error && <p className="error">{error}</p>}
          <button type="submit">Войти</button>
        </form>
        <p style={{ marginTop: "1.5rem" }}>
          Студент? <Link to="/join">Подключиться к сессии</Link>
        </p>
      </div>
    </div>
  );
}
