import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { toast } from "sonner";
import {
  fetchReservationsState,
  toggleReservationPaid,
  fetchStockCheck,
} from "../lib/api";

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

interface StockCheckItem {
  foodId: number;
  name: string;
  unit: string;
  stock: number;
  required: number;
  missing: number;
  shortage: boolean;
}

interface StockCheckState {
  eventDate: string;
  hasShortage: boolean;
  items: StockCheckItem[];
}

export function ReservationsPage() {
  const [data, setData] = useState<ReservationsState | null>(null);
  const [stockCheck, setStockCheck] = useState<StockCheckState | null>(null);
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

  const loadStockCheck = async () => {
    try {
      const result = await fetchStockCheck();
      setStockCheck(result);
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors du chargement du stock");
    }
  };

  const loadPageData = async () => {
    await Promise.all([loadReservations(), loadStockCheck()]);
  };

  useEffect(() => {
    loadPageData();
  }, []);

  const handleTogglePaid = async (reservationId: string, isPaid: boolean) => {
    try {
      setLoadingPaymentId(reservationId);
      await toggleReservationPaid(reservationId, isPaid);
      await loadPageData();

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

  const shortageItems =
    stockCheck?.items.filter((item) => item.shortage || item.missing > 0) || [];

  const okItems =
    stockCheck?.items.filter((item) => !item.shortage && item.required > 0) || [];

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

      {stockCheck && (
        <Card
          className={`rounded-2xl border-0 shadow-sm ${
            stockCheck.hasShortage ? "ring-1 ring-red-200" : "ring-1 ring-green-200"
          }`}
        >
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-3 flex-wrap">
              <span>État du stock pour le service</span>

              <Badge
                variant={stockCheck.hasShortage ? "destructive" : "default"}
                className="rounded-full"
              >
                {stockCheck.hasShortage ? "Stock insuffisant" : "Stock suffisant"}
              </Badge>
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            {stockCheck.hasShortage ? (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Certains produits sont insuffisants pour assurer le service de demain.
                </p>

                {shortageItems.length === 0 ? (
                  <div className="text-sm text-muted-foreground">
                    Aucune ligne de manque détectée.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {shortageItems.map((item) => (
                      <div
                        key={item.foodId}
                        className="rounded-xl border border-red-200 bg-red-50 px-4 py-3"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="font-medium">{item.name}</div>
                            <div className="text-sm text-muted-foreground">
                              En stock : {item.stock} {item.unit} • Nécessaire : {item.required} {item.unit}
                            </div>
                          </div>

                          <Badge variant="destructive" className="rounded-full">
                            Manque {item.missing} {item.unit}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Le stock actuel permet de couvrir les réservations enregistrées.
                </p>

                {okItems.length > 0 && (
                  <div className="space-y-2">
                    {okItems.map((item) => (
                      <div
                        key={item.foodId}
                        className="rounded-xl border border-green-200 bg-green-50 px-4 py-3"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="font-medium">{item.name}</div>
                            <div className="text-sm text-muted-foreground">
                              En stock : {item.stock} {item.unit} • Nécessaire : {item.required} {item.unit}
                            </div>
                          </div>

                          <Badge className="rounded-full">
                            OK
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
                        <div className="flex items-center gap-2 flex-wrap">
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