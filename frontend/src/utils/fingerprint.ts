export function getDeviceFingerprint(): string {
  const key = "autoassess_fp";
  let fp = localStorage.getItem(key);
  if (!fp) {
    const seed = [
      navigator.userAgent,
      navigator.language,
      screen.width,
      screen.height,
      Intl.DateTimeFormat().resolvedOptions().timeZone,
    ].join("|");
    fp = btoa(unescape(encodeURIComponent(seed))).slice(0, 64);
    localStorage.setItem(key, fp);
  }
  return fp;
}
