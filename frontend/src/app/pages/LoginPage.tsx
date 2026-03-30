import { useState } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Coffee, Eye, EyeOff, LogIn, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { loginUser } from "../lib/api";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const { setUser } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (!email.trim()) {
      setFormError("Veuillez renseigner votre email.");
      toast.error("Email requis");
      return;
    }

    if (!password.trim()) {
      setFormError("Veuillez renseigner votre mot de passe.");
      toast.error("Mot de passe requis");
      return;
    }

    try {
      setIsSubmitting(true);

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
        setFormError("Email ou mot de passe incorrect.");
        toast.error("Identifiants incorrects");
      } else if (error instanceof Error && error.message === "missing_email") {
        setFormError("Veuillez renseigner votre email.");
        toast.error("Email manquant");
      } else if (error instanceof Error && error.message === "missing_password") {
        setFormError("Veuillez renseigner votre mot de passe.");
        toast.error("Mot de passe manquant");
      } else {
        setFormError("Une erreur est survenue lors de la connexion.");
        toast.error("Erreur de connexion");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/10 via-background to-accent flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center size-20 rounded-2xl bg-primary/10 mb-4">
            <Coffee className="size-10 text-primary" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Zack & Snack</h1>
          <p className="text-muted-foreground">Connectez-vous à votre espace</p>
        </div>

        <Card className="rounded-2xl border-0 shadow-xl">
          <CardHeader>
            <CardTitle className="text-center">Connexion</CardTitle>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              {formError && (
                <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  <AlertCircle className="size-4 mt-0.5 shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="votre.email@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="rounded-xl"
                  disabled={isSubmitting}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Mot de passe</Label>

                <div className="relative">
                  <Input
                    id="password"
                    type={isPasswordVisible ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="rounded-xl pr-12"
                    disabled={isSubmitting}
                  />

                  <button
                    type="button"
                    onClick={() => setIsPasswordVisible((prev) => !prev)}
                    className="absolute inset-y-0 right-0 flex items-center pr-4 text-muted-foreground hover:text-foreground"
                    aria-label={
                      isPasswordVisible
                        ? "Masquer le mot de passe"
                        : "Afficher le mot de passe"
                    }
                  >
                    {isPasswordVisible ? (
                      <EyeOff className="size-4" />
                    ) : (
                      <Eye className="size-4" />
                    )}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full rounded-full h-12 mt-6"
                disabled={isSubmitting}
              >
                <LogIn className="size-4 mr-2" />
                {isSubmitting ? "Connexion..." : "Se connecter"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
