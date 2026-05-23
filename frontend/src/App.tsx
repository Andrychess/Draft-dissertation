import { Navigate, Route, Routes } from "react-router-dom";
import StudentResults from "./pages/StudentResults";
import LoginPage from "./pages/LoginPage";
import AdminPanel from "./pages/AdminPanel";
import TeacherPanel from "./pages/TeacherPanel";
import TemplateEditor from "./pages/TemplateEditor";
import SessionForm from "./pages/SessionForm";
import SessionJoin from "./pages/SessionJoin";
import AnswerForm from "./pages/AnswerForm";
import ResultsTable from "./pages/ResultsTable";
import ResultDetail from "./pages/ResultDetail";

function PrivateRoute({ children, roles }: { children: JSX.Element; roles?: string[] }) {
  const token = localStorage.getItem("access_token");
  const role = localStorage.getItem("role");
  if (!token) return <Navigate to="/login" replace />;
  if (roles && role && !roles.includes(role)) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/join" element={<SessionJoin />} />
      <Route path="/answer/:sessionId" element={<AnswerForm />} />
      <Route path="/student/results/:sheetId" element={<StudentResults />} />
      <Route
        path="/admin"
        element={
          <PrivateRoute roles={["admin"]}>
            <AdminPanel />
          </PrivateRoute>
        }
      />
      <Route
        path="/teacher"
        element={
          <PrivateRoute roles={["teacher", "admin"]}>
            <TeacherPanel />
          </PrivateRoute>
        }
      />
      <Route
        path="/templates/new"
        element={
          <PrivateRoute roles={["teacher", "admin"]}>
            <TemplateEditor />
          </PrivateRoute>
        }
      />
      <Route
        path="/templates/:id"
        element={
          <PrivateRoute roles={["teacher", "admin"]}>
            <TemplateEditor />
          </PrivateRoute>
        }
      />
      <Route
        path="/sessions/new"
        element={
          <PrivateRoute roles={["teacher", "admin"]}>
            <SessionForm />
          </PrivateRoute>
        }
      />
      <Route
        path="/sessions/:id/results"
        element={
          <PrivateRoute roles={["teacher", "admin"]}>
            <ResultsTable />
          </PrivateRoute>
        }
      />
      <Route
        path="/results/:sheetId"
        element={
          <PrivateRoute roles={["teacher", "admin"]}>
            <ResultDetail />
          </PrivateRoute>
        }
      />
      <Route path="/" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
