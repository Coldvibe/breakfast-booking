import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";

export function ReservationsPage() {
  return (
    <div className="space-y-6 pb-20">
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Réservations de demain
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="rounded-full">
              À venir
            </Badge>
            <span className="text-sm text-muted-foreground">
              Cette page affichera les réservations du lendemain.
            </span>
          </div>

          <div className="rounded-2xl border border-dashed border-muted-foreground/20 p-6 text-center text-sm text-muted-foreground">
            Aucune donnée affichée pour l’instant.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}