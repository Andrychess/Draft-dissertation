import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { sessionsApi } from "../api/client";

type Row = {
  sheet_id: number;
  student_name: string;
  group_cipher: string | null;
  total_score: number;
  max_score: number;
  verdict: string | null;
};

export default function ResultsTable() {
  const { id } = useParams();
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    sessionsApi.results(Number(id)).then((r) => setRows(r.data));
  }, [id]);

  const exportCsv = async () => {
    const { data } = await sessionsApi.exportCsv(Number(id));
    const url = URL.createObjectURL(data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `session_${id}_results.csv`;
    a.click();
  };

  return (
    <div className="container">
      <Link to="/teacher">← Назад</Link>
      <div className="card">
        <h1>Результаты сессии #{id}</h1>
        <button type="button" onClick={exportCsv}>
          Экспорт CSV
        </button>
        <table>
          <thead>
            <tr>
              <th>Студент</th>
              <th>Группа</th>
              <th>Балл</th>
              <th>Вердикт</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.sheet_id}>
                <td>{r.student_name}</td>
                <td>{r.group_cipher || "—"}</td>
                <td>
                  {r.total_score} / {r.max_score}
                </td>
                <td>{r.verdict || "ожидание"}</td>
                <td>
                  <Link to={`/results/${r.sheet_id}`}>Детали</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
