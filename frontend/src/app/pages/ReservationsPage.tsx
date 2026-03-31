import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { toast } from "sonner";
import { fetchReservationsState, toggleReservationPaid } from "../lib/api";

interface ReservationLine {
  label: string;
  qty: number;
  type: string;
}

interface Reservation {
  id: string;
  name: string;
  lines: ReservationLine[];
  isPaid: boolean;
}

interface OfferItem {
  id: number;
  offer_date: string;
  offer_type: string;
  recipe_id: number | null;
  food_id: number | null;
  max_per_person: number;
  is_active: number;
  label: string;
  unit: string | null;
}

interface ReservationsState {
  date: string;
  isPlanned: boolean;
  isOpen: boolean;
  reservations: Reservation[];
  totals: {
    mains: Record<string, number>;
    sides: Record<string, number>;
  };
  offers: {
    mains: OfferItem[];
    sides: OfferItem[];
  };
}

export function ReservationsPage() {
  const [data, setData] = useState<ReservationsState | null>(null);
  const [loadingPaymentId, setLoadingPaymentId] = useState<string | null>(null);

  const loadReservations = async () => {
    try {
      const result = await fetchReservationsState();
      setData(result);
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors du chargement des réservations");
    }
  };

  useEffect(() => {
    loadReservations();
  }, []);

  const handleTogglePaid = async (reservationId: string, isPaid: boolean) => {
    try {
      setLoadingPaymentId(reservationId);
      await toggleReservationPaid(reservationId, isPaid);
      await loadReservations();

      toast.success(
        isPaid ? "Réservation marquée comme payée" : "Paiement retiré"
      );
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors de la mise à jour du paiement");
    } finally {
      setLoadingPaymentId(null);
    }
  };

  if (!data) {
    return (
      <div className="space-y-6 pb-20">
        <Card className="rounded-2xl border-0 shadow-sm">
          <CardContent className="py-8 text-center text-muted-foreground">
            Chargement des réservations...
          </CardContent>
        </Card>
      </div>
    );
  }

  const mainTotals = Object.entries(data.totals.mains);
  const sideTotals = Object.entries(data.totals.sides);

  const unpaidReservations = data.reservations.filter((reservation) => !reservation.isPaid);
  const paidReservations = data.reservations.filter((reservation) => reservation.isPaid);

  return (
    <div className="space-y-6 pb-20">
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Réservations de demain
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="rounded-full">
              {data.date}
            </Badge>

            <Badge
              variant={data.isPlanned ? "default" : "secondary"}
              className="rounded-full"
            >
              {data.isPlanned ? "Déjeuner prévu" : "Déjeuner non prévu"}
            </Badge>

            <Badge
              variant={data.isOpen ? "default" : "secondary"}
              className="rounded-full"
            >
              {data.isOpen ? "Réservations ouvertes" : "Réservations fermées"}
            </Badge>

            <Badge variant="outline" className="rounded-full">
              {data.reservations.length} réservation(s)
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle>Offre active</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">
              Plats principaux
            </h3>

            {data.offers.mains.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                Aucun plat principal actif
              </div>
            ) : (
              <div className="space-y-2">
                {data.offers.mains.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3"
                  >
                    <span className="font-medium">{item.label}</span>
                    <Badge variant="outline" className="rounded-full">
                      Max {item.max_per_person}/pers
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">
              Accompagnements
            </h3>

            {data.offers.sides.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                Aucun accompagnement actif
              </div>
            ) : (
              <div className="space-y-2">
                {data.offers.sides.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3"
                  >
                    <span className="font-medium">{item.label}</span>
                    <Badge variant="outline" className="rounded-full">
                      Max {item.max_per_person}/pers
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle>Totaux réservés</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">
              Plats principaux
            </h3>

            {mainTotals.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                Aucun total pour l’instant
              </div>
            ) : (
              <div className="space-y-2">
                {mainTotals.map(([label, qty]) => (
                  <div
                    key={label}
                    className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3"
                  >
                    <span>{label}</span>
                    <Badge className="rounded-full">{qty}</Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">
              Accompagnements
            </h3>

            {sideTotals.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                Aucun total pour l’instant
              </div>
            ) : (
              <div className="space-y-2">
                {sideTotals.map(([label, qty]) => (
                  <div
                    key={label}
                    className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3"
                  >
                    <span>{label}</span>
                    <Badge className="rounded-full">{qty}</Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-xl font-semibold">
          Réservations ({data.reservations.length})
        </h2>

        {data.reservations.length === 0 ? (
          <Card className="rounded-2xl border-0 shadow-sm">
            <CardContent className="py-8 text-center text-muted-foreground">
              Aucune réservation pour le moment.
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Non payé</h3>
                <Badge variant="secondary" className="rounded-full">
                  {unpaidReservations.length}
                </Badge>
              </div>

              {unpaidReservations.length === 0 ? (
                <Card className="rounded-2xl border-0 shadow-sm">
                  <CardContent className="py-6 text-center text-muted-foreground">
                    Aucune réservation non payée.
                  </CardContent>
                </Card>
              ) : (
                unpaidReservations.map((reservation) => (
                  <Card key={reservation.id} className="rounded-2xl border-0 shadow-sm">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="font-semibold text-base">{reservation.name}</div>

                        <Button
                          size="sm"
                          className="rounded-full"
                          disabled={loadingPaymentId === reservation.id}
                          onClick={() => handleTogglePaid(reservation.id, true)}
                        >
                          {loadingPaymentId === reservation.id ? "..." : "Marquer payé"}
                        </Button>
                      </div>

                      {reservation.lines.length === 0 ? (
                        <div className="text-sm text-muted-foreground">
                          Aucun choix enregistré
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {reservation.lines.map((line, index) => (
                            <div
                              key={`${reservation.id}-${index}`}
                              className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3"
                            >
                              <div className="flex items-center gap-2">
                                <span>{line.label}</span>
                                <Badge
                                  variant={line.type === "MAIN" ? "default" : "secondary"}
                                  className="rounded-full"
                                >
                                  {line.type === "MAIN" ? "Plat" : "Accompagnement"}
                                </Badge>
                              </div>

                              <Badge variant="outline" className="rounded-full">
                                x{line.qty}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Payé</h3>
                <Badge variant="default" className="rounded-full">
                  {paidReservations.length}
                </Badge>
              </div>

              {paidReservations.length === 0 ? (
                <Card className="rounded-2xl border-0 shadow-sm">
                  <CardContent className="py-6 text-center text-muted-foreground">
                    Aucune réservation payée.
                  </CardContent>
                </Card>
              ) : (
                paidReservations.map((reservation) => (
                  <Card
                    key={reservation.id}
                    className="rounded-2xl border-0 shadow-sm ring-1 ring-green-200"
                  >
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <div className="font-semibold text-base">{reservation.name}</div>
                          <Badge className="rounded-full">Payé</Badge>
                        </div>

                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-full"
                          disabled={loadingPaymentId === reservation.id}
                          onClick={() => handleTogglePaid(reservation.id, false)}
                        >
                          {loadingPaymentId === reservation.id ? "..." : "Annuler paiement"}
                        </Button>
                      </div>

                      {reservation.lines.length === 0 ? (
                        <div className="text-sm text-muted-foreground">
                          Aucun choix enregistré
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {reservation.lines.map((line, index) => (
                            <div
                              key={`${reservation.id}-${index}`}
                              className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3"
                            >
                              <div className="flex items-center gap-2">
                                <span>{line.label}</span>
                                <Badge
                                  variant={line.type === "MAIN" ? "default" : "secondary"}
                                  className="rounded-full"
                                >
                                  {line.type === "MAIN" ? "Plat" : "Accompagnement"}
                                </Badge>
                              </div>

                              <Badge variant="outline" className="rounded-full">
                                x{line.qty}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}