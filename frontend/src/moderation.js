export function moderationEntry(role) {
  return role === "moderator" || role === "admin" ? "shown" : "hidden";
}
