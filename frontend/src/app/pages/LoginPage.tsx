import { useState } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Coffee, LogIn } from "lucide-react";
import { toast } from "sonner";
import { loginUser } from "../lib/api";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { setUser } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim()) {
      toast.error("Email requis");
      return;
    }

    if (!password.trim()) {
      toast.error("Mot de passe requis");
      return;
    }

    try {
      const data = await loginUser(email.trim(), password);

      setUser(data.user);

      toast.success("Connexion réussie");

      if (data.user.role === "admin" || data.user.role === "gestionnaire") {
        navigate("/");
      } else {
        navigate("/employee");
      }
    } catch (error) {
      console.error(error);

      if (error instanceof Error && error.message === "invalid_credentials") {
        toast.error("Identifiants incorrects");
      } else if (error instanceof Error && error.message === "missing_email") {
        toast.error("Email manquant");
      } else if (error instanceof Error && error.message === "missing_password") {
        toast.error("Mot de passe manquant");
      } else {
        toast.error("Erreur de connexion");
      }
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
}