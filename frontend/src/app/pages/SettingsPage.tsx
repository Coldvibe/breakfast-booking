import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Button } from "../components/ui/button";
import { Settings, Bell, Moon, Smartphone, Trash2, Download } from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";

export function SettingsPage() {
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [autoBackup, setAutoBackup] = useState(true);

  const handleClearData = () => {
    if (confirm("Êtes-vous sûr de vouloir effacer toutes les données ?")) {
      toast.success("Données effacées");
    }
  };

  const handleExportData = () => {
    toast.success("Données exportées");
  };

  return (
    <div className="space-y-6 pb-24">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Settings className="size-6 text-primary" />
          <h2 className="text-2xl font-semibold">Paramètres</h2>
        </div>
        <p className="text-muted-foreground">Configurez votre application</p>
      </div>

      {/* Notifications */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="size-5" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-base">Activer les notifications</Label>
              <p className="text-sm text-muted-foreground">
                Recevoir des rappels pour créer les offres
              </p>
            </div>
            <Switch checked={notifications} onCheckedChange={setNotifications} />
          </div>
        </CardContent>
      </Card>

      {/* Apparence */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Moon className="size-5" />
            Apparence
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-base">Mode sombre</Label>
              <p className="text-sm text-muted-foreground">Activer le thème sombre</p>
            </div>
            <Switch checked={darkMode} onCheckedChange={setDarkMode} />
          </div>
        </CardContent>
      </Card>

      {/* Sauvegarde */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="size-5" />
            Données
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-base">Sauvegarde automatique</Label>
              <p className="text-sm text-muted-foreground">
                Sauvegarder les données régulièrement
              </p>
            </div>
            <Switch checked={autoBackup} onCheckedChange={setAutoBackup} />
          </div>

          <div className="pt-4 space-y-3 border-t">
            <Button
              variant="outline"
              className="w-full rounded-full"
              onClick={handleExportData}
            >
              <Download className="size-4 mr-2" />
              Exporter les données
            </Button>
            <Button
              variant="destructive"
              className="w-full rounded-full"
              onClick={handleClearData}
            >
              <Trash2 className="size-4 mr-2" />
              Effacer toutes les données
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Installation PWA */}
      <Card className="rounded-2xl border-0 shadow-sm bg-gradient-to-br from-primary/5 to-accent">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="flex items-center justify-center size-12 rounded-xl bg-primary/10">
              <Smartphone className="size-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold mb-1">Installer l'application</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Installez l'application sur votre téléphone pour un accès rapide et
                hors-ligne
              </p>
              <Button className="rounded-full" size="sm">
                Installer
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Informations */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardContent className="p-6 text-center space-y-2">
          <p className="text-sm text-muted-foreground">Version 1.0.0</p>
          <p className="text-xs text-muted-foreground">© 2026 Backoffice Petit Déjeuner</p>
        </CardContent>
      </Card>
    </div>
  );
}
