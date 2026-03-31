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

  const unpaidReservations = data.reservations.filter(
    (reservation) => !reservation.isPaid
  );
  const paidReservations = data.reservations.filter(
    (reservation) => reservation.isPaid
  );

  const renderReservationLines = (reservation: Reservation) => {
    if (reservation.lines.length === 0) {
      return (
        <div className="text-sm text-muted-foreground">
          Aucun choix enregistré
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {reservation.lines.map((line, index) => (
          <div
            key={`${reservation.id}-${index}`}
            className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3 gap-3"
          >
            <div className="flex items-center gap-2 flex-wrap min-w-0">
              <span className="break-words">{line.label}</span>
              <Badge
                variant={line.type === "MAIN" ? "default" : "secondary"}
                className="rounded-full"
              >
                {line.type === "MAIN" ? "Plat" : "Accompagnement"}
              </Badge>
            </div>

            <Badge variant="outline" className="rounded-full shrink-0">
              x{line.qty}
            </Badge>
          </div>
        ))}
      </div>
    );
  };

  const renderReservationCard = (reservation: Reservation, paid: boolean) => {
    return (
      <Card
        key={reservation.id}
        className={`rounded-2xl border-0 shadow-sm ${
          paid ? "ring-1 ring-green-200" : ""
        }`}
      >
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <div className="font-semibold text-base break-words">
                  {reservation.name}
                </div>

                {paid && <Badge className="rounded-full">Payé</Badge>}
              </div>
            </div>

            <div className="w-full sm:w-auto">
              <Button
                size="sm"
                variant={paid ? "outline" : "default"}
                className="w-full sm:w-auto rounded-full"
                disabled={loadingPaymentId === reservation.id}
                onClick={() => handleTogglePaid(reservation.id, !paid)}
              >
                {loadingPaymentId === reservation.id
                  ? "..."
                  : paid
                  ? "Annuler paiement"
                  : "Marquer payé"}
              </Button>
            </div>
          </div>

          {renderReservationLines(reservation)}
        </CardContent>
      </Card>
    );
  };

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
                    className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3 gap-3"
                  >
                    <span className="font-medium break-words">{item.label}</span>
                    <Badge variant="outline" className="rounded-full shrink-0">
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
                    className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3 gap-3"
                  >
                    <span className="font-medium break-words">{item.label}</span>
                    <Badge variant="outline" className="rounded-full shrink-0">
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
                    className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3 gap-3"
                  >
                    <span className="break-words">{label}</span>
                    <Badge className="rounded-full shrink-0">{qty}</Badge>
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
                    className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3 gap-3"
                  >
                    <span className="break-words">{label}</span>
                    <Badge className="rounded-full shrink-0">{qty}</Badge>
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
                unpaidReservations.map((reservation) =>
                  renderReservationCard(reservation, false)
                )
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
                paidReservations.map((reservation) =>
                  renderReservationCard(reservation, true)
                )
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}