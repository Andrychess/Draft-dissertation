/** Ссылка для студента: /join?code=... */
export function buildStudentJoinUrl(connectionCode: string): string {
  const code = connectionCode.trim();
  const url = new URL("/join", window.location.origin);
  url.searchParams.set("code", code);
  return url.toString();
}

/** Открыть страницу подключения студента в новой вкладке (как «Открыть по ссылке»). */
export function openStudentJoinLink(connectionCode: string): void {
  window.open(buildStudentJoinUrl(connectionCode), "_blank", "noopener,noreferrer");
}

/** Перейти на страницу подключения в текущей вкладке. */
export function goToStudentJoinLink(connectionCode: string): void {
  window.location.assign(buildStudentJoinUrl(connectionCode));
}
