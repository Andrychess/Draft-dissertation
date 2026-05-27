import { buildStudentJoinUrl, goToStudentJoinLink, openStudentJoinLink } from "../utils/joinLink";

type Props = {
  connectionCode: string;
  showUrl?: boolean;
};

export default function StudentJoinActions({ connectionCode, showUrl = false }: Props) {
  const joinUrl = buildStudentJoinUrl(connectionCode);

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(joinUrl);
    } catch {
      window.prompt("Скопируйте ссылку:", joinUrl);
    }
  };

  return (
    <div>
      {showUrl && (
        <p style={{ wordBreak: "break-all", fontSize: "0.9rem", marginBottom: "0.75rem" }}>{joinUrl}</p>
      )}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <button type="button" onClick={() => openStudentJoinLink(connectionCode)}>
          Открыть по ссылке
        </button>
        <button type="button" onClick={() => goToStudentJoinLink(connectionCode)}>
          Перейти
        </button>
        <button type="button" className="secondary" onClick={copyLink}>
          Копировать ссылку
        </button>
      </div>
    </div>
  );
}
