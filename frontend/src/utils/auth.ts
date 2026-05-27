export function logout(): void {
  localStorage.clear();
  window.location.href = "/login";
}
