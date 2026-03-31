import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Coffee, Eye, EyeOff, UserPlus, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { registerUser } from "../lib/api";

export function RegisterPage() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [service, setService] = useState("");
  const [password, setPassword] = useState("");
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    setSuccessMessage("");

    if (!name.trim()) {
      setFormError("Veuillez renseigner votre nom.");
      return;
    }

    if (!email.trim()) {
      setFormError("Veuillez renseigner votre email.");
      return;
    }

    if (!password.trim()) {
      setFormError("Veuillez renseigner votre mot de passe.");
      return;
    }

    try {
      setIsSubmitting(true);

      await registerUser({
        name: name.trim(),
        email: email.trim(),
        password,
        service: service.trim(),
      });

      setSuccessMessage(
        "Compte créé avec succès. En attente de validation par un administrateur."
      );

      toast.success("Inscription réussie 🎉");

      // reset form
      setName("");
      setEmail("");
      setPassword("");
      setService("");

      // optionnel : redirection après 2 sec
      setTimeout(() => {
        navigate("/login");
      }, 2000);

    } catch (error) {
      console.error(error);

      if (error instanceof Error) {
        switch (error.message) {
          case "duplicate_email":
            setFormError("Cet email est déjà utilisé.");
            toast.error("Email déjà utilisé");
            break;
          case "missing_name":
            setFormError("Nom requis.");
            break;
          case "missing_email":
            setFormError("Email requis.");
            break;
          case "missing_password":
            setFormError("Mot de passe requis.");
            break;
          default:
            setFormError("Une erreur est survenue.");
            toast.error("Erreur d’inscription");
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/10 via-background to-accent flex items-center justify-center p-4">
      <div className="w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center size-20 rounded-2xl bg-primary/10 mb-4">
            <Coffee className="size-10 text-primary" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Zack & Snack</h1>
          <p className="text-muted-foreground">Créer un compte</p>
        </div>

        <Card className="rounded-2xl border-0 shadow-xl">
          <CardHeader>
            <CardTitle className="text-center">Inscription</CardTitle>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleRegister} className="space-y-4">

              {/* Error */}
              {formError && (
                <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  <AlertCircle className="size-4 mt-0.5 shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              {/* Success */}
              {successMessage && (
                <div className="rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
                  {successMessage}
                </div>
              )}

              {/* Name */}
              <div className="space-y-2">
                <Label>Nom</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Votre nom"
                  disabled={isSubmitting}
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="votre.email@example.com"
                  disabled={isSubmitting}
                />
              </div>

              {/* Service */}
              <div className="space-y-2">
                <Label>Service (optionnel)</Label>
                <Input
                  value={service}
                  onChange={(e) => setService(e.target.value)}
                  placeholder="IT, RH, Logistique..."
                  disabled={isSubmitting}
                />
              </div>

              {/* Password */}
              <div className="space-y-2">
                <Label>Mot de passe</Label>

                <div className="relative">
                  <Input
                    type={isPasswordVisible ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    disabled={isSubmitting}
                    className="pr-12"
                  />

                  <button
                    type="button"
                    onClick={() => setIsPasswordVisible((prev) => !prev)}
                    className="absolute inset-y-0 right-0 flex items-center pr-4 text-muted-foreground"
                  >
                    {isPasswordVisible ? (
                      <EyeOff className="size-4" />
                    ) : (
                      <Eye className="size-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <Button
                type="submit"
                className="w-full rounded-full h-12 mt-4"
                disabled={isSubmitting}
              >
                <UserPlus className="size-4 mr-2" />
                {isSubmitting ? "Création..." : "Créer un compte"}
              </Button>

              {/* Back to login */}
              <div className="text-center text-sm text-muted-foreground mt-4">
                Déjà un compte ?{" "}
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="text-primary font-medium hover:underline"
                >
                  Se connecter
                </button>
              </div>

            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}