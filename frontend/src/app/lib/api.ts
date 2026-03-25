export async function fetchDailyOfferState() {
  const response = await fetch("/api/admin/daily-offer-state", {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Erreur API");
  }

  return response.json();
}