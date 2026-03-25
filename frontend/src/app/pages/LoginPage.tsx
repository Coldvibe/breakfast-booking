import { useState } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Coffee, LogIn } from "lucide-react";
import { toast } from "sonner";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      toast.error("Veuillez remplir tous les champs");
      return;
    }

    const success = login(email, password);
    if (success) {
      toast.success("Connexion réussie");
      navigate("/");
    } else {
      toast.error("Email ou mot de passe incorrect");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/10 via-background to-accent flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center size-20 rounded-2xl bg-primary/10 mb-4">
            <Coffee className="size-10 text-primary" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Petit Déjeuner</h1>
          <p className="text-muted-foreground">Connectez-vous à votre espace</p>
        </div>

        <Card className="rounded-2xl border-0 shadow-xl">
          <CardHeader>
            <CardTitle className="text-center">Connexion</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="votre.email@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="rounded-xl"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Mot de passe</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="rounded-xl"
                />
              </div>

              <Button type="submit" className="w-full rounded-full h-12 mt-6">
                <LogIn className="size-4 mr-2" />
                Se connecter
              </Button>
            </form>

            <div className="mt-6 p-4 bg-muted/50 rounded-xl">
              <p className="text-xs text-muted-foreground text-center mb-3">
                Comptes de démonstration :
              </p>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Admin :</span>
                  <span className="text-muted-foreground">
                    admin@example.com / admin
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-medium">Employé :</span>
                  <span className="text-muted-foreground">
                    jean@example.com / 1234
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
