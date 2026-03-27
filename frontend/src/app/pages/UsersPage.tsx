import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar";
import { Switch } from "../components/ui/switch";
import { Plus, Phone, Mail, Trash2, Pencil, Check } from "lucide-react";
import { toast } from "sonner";
import { createUser, deleteUser, fetchUsersState, updateUser, updateUserActive } from "../lib/api";

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: "admin" | "gestionnaire" | "utilisateur";
  service: string;
  imageUrl: string;
  isActive: boolean;
}

const DEFAULT_ROLE: User["role"] = "utilisateur";

export function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);

  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<User["role"]>(DEFAULT_ROLE);
  const [newService, setNewService] = useState("");
  const [newImageUrl, setNewImageUrl] = useState("");

  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const isEditingUser = editingUserId !== null;

  const resetForm = () => {
    setNewName("");
    setNewEmail("");
    setNewPhone("");
    setNewPassword("");
    setNewRole(DEFAULT_ROLE);
    setNewService("");
    setNewImageUrl("");
    setEditingUserId(null);
  };

  const loadUsers = async () => {
    try {
      const data = await fetchUsersState();
      setUsers(data.users || []);
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors du chargement des utilisateurs");
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleSubmitUser = async () => {
  if (!newName.trim()) {
    toast.error("Veuillez remplir le nom");
    return;
  }

  if (!newEmail.trim()) {
    toast.error("Veuillez remplir l’email");
    return;
  }

  try {
    if (isEditingUser && editingUserId) {
      await updateUser(editingUserId, {
        name: newName.trim(),
        email: newEmail.trim(),
        phone: newPhone.trim(),
        role: newRole,
        service: newService.trim(),
        imageUrl: newImageUrl.trim(),
      });

      toast.success("Utilisateur modifié");
    } else {
      if (!newPassword.trim()) {
        toast.error("Veuillez remplir le mot de passe");
        return;
      }

      await createUser({
        name: newName.trim(),
        email: newEmail.trim(),
        phone: newPhone.trim(),
        password: newPassword,
        role: newRole,
        service: newService.trim(),
        imageUrl: newImageUrl.trim(),
      });

      toast.success("Utilisateur ajouté");
    }

    await loadUsers();
    resetForm();
  } catch (error) {
    console.error(error);

    if (error instanceof Error && error.message === "missing_name") {
      toast.error("Nom manquant");
    } else if (error instanceof Error && error.message === "missing_email") {
      toast.error("Email manquant");
    } else if (error instanceof Error && error.message === "missing_password") {
      toast.error("Mot de passe manquant");
    } else if (error instanceof Error && error.message === "duplicate_email") {
      toast.error("Cet email existe déjà");
    } else if (error instanceof Error && error.message === "invalid_role") {
      toast.error("Rôle invalide");
    } else if (error instanceof Error && error.message === "user_not_found") {
      toast.error("Utilisateur introuvable");
    } else {
      toast.error("Erreur lors de l’enregistrement de l’utilisateur");
    }
  }
};

  const toggleUserActive = async (user: User) => {
    try {
      await updateUserActive(user.id, !user.isActive);
      await loadUsers();
      toast.success("Statut utilisateur mis à jour");
    } catch (error) {
      console.error(error);

      if (error instanceof Error && error.message === "missing_is_active") {
        toast.error("Statut manquant");
      } else if (error instanceof Error && error.message === "user_not_found") {
        toast.error("Utilisateur introuvable");
      } else {
        toast.error("Erreur lors de la mise à jour du statut");
      }
    }
  };

  const handleDeleteUser = async (user: User) => {
    const confirmed = window.confirm(`Supprimer "${user.name}" ?`);
    if (!confirmed) return;

    try {
      await deleteUser(user.id);
      await loadUsers();
      toast.success("Utilisateur supprimé");

      if (editingUserId === user.id) {
        resetForm();
      }
    } catch (error) {
      console.error(error);
      toast.error("Erreur lors de la suppression de l’utilisateur");
    }
  };

  const startEditingUser = (user: User) => {
    setEditingUserId(user.id);
    setNewName(user.name);
    setNewEmail(user.email);
    setNewPhone(user.phone);
    setNewPassword("");
    setNewRole(user.role);
    setNewService(user.service);
    setNewImageUrl(user.imageUrl);
  };

  const cancelEditingUser = () => {
    resetForm();
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((part) => part[0] || "")
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const getRoleBadge = (role: User["role"]) => {
    const variants: Record<User["role"], "default" | "secondary" | "outline"> = {
      admin: "default",
      gestionnaire: "secondary",
      utilisateur: "outline",
    };
    return variants[role];
  };

  const getRoleLabel = (role: User["role"]) => {
    const labels: Record<User["role"], string> = {
      admin: "Admin",
      gestionnaire: "Gestionnaire",
      utilisateur: "Utilisateur",
    };
    return labels[role];
  };

  return (
    <div className="space-y-6 pb-20">
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {isEditingUser ? <Check className="size-5" /> : <Plus className="size-5" />}
            {isEditingUser ? "Modifier l’utilisateur" : "Ajouter un utilisateur"}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="user-name" className="text-sm text-muted-foreground">
              Nom complet
            </Label>
            <Input
              id="user-name"
              placeholder="Ex: Marie Dupont"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-email" className="text-sm text-muted-foreground">
              Email
            </Label>
            <Input
              id="user-email"
              type="email"
              placeholder="Ex: marie.dupont@example.com"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-phone" className="text-sm text-muted-foreground">
              Téléphone
            </Label>
            <Input
              id="user-phone"
              type="tel"
              placeholder="Ex: 0470 12 34 56"
              value={newPhone}
              onChange={(e) => setNewPhone(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-password" className="text-sm text-muted-foreground">
              Mot de passe
            </Label>
            <Input
              id="user-password"
              type="password"
              placeholder={isEditingUser ? "Laisser vide pour l’instant" : "Mot de passe"}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-role" className="text-sm text-muted-foreground">
              Rôle
            </Label>
            <select
              id="user-role"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as User["role"])}
              className="w-full rounded-xl border border-gray-200 bg-background px-3 py-2 text-sm"
            >
              <option value="utilisateur">Utilisateur</option>
              <option value="gestionnaire">Gestionnaire</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-service" className="text-sm text-muted-foreground">
              Service
            </Label>
            <Input
              id="user-service"
              placeholder="Ex: Circulation"
              value={newService}
              onChange={(e) => setNewService(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-image-url" className="text-sm text-muted-foreground">
              URL photo
            </Label>
            <Input
              id="user-image-url"
              placeholder="https://..."
              value={newImageUrl}
              onChange={(e) => setNewImageUrl(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <Button className="w-full rounded-full h-12" onClick={handleSubmitUser}>
            {isEditingUser ? <Check className="size-4 mr-2" /> : <Plus className="size-4 mr-2" />}
            {isEditingUser ? "Enregistrer les modifications" : "Ajouter l’utilisateur"}
          </Button>

          {isEditingUser && (
            <Button
              type="button"
              variant="outline"
              className="w-full rounded-full h-12"
              onClick={cancelEditingUser}
            >
              Annuler la modification
            </Button>
          )}
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Utilisateurs ({users.length})</h2>

        <div className="space-y-3">
          {users.map((user) => (
            <Card key={user.id} className="rounded-2xl border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <Avatar className="size-12">
                    {user.imageUrl && <AvatarImage src={user.imageUrl} alt={user.name} />}
                    <AvatarFallback className="bg-primary/10 text-primary">
                      {getInitials(user.name)}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2 gap-3">
                      <div>
                        <h4 className="font-semibold">{user.name}</h4>

                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <Badge variant={getRoleBadge(user.role)} className="rounded-full">
                            {getRoleLabel(user.role)}
                          </Badge>

                          {user.service && (
                            <Badge variant="secondary" className="rounded-full">
                              {user.service}
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <Switch
                          checked={user.isActive}
                          onCheckedChange={() => toggleUserActive(user)}
                        />

                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => startEditingUser(user)}
                          className="rounded-full"
                        >
                          <Pencil className="size-4" />
                        </Button>

                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleDeleteUser(user)}
                          className="rounded-full"
                        >
                          <Trash2 className="size-4 text-red-600" />
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Mail className="size-3.5" />
                        {user.email}
                      </div>

                      {user.phone && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Phone className="size-3.5" />
                          {user.phone}
                        </div>
                      )}
                    </div>

                    <div className="mt-2">
                      <Badge
                        variant={user.isActive ? "default" : "secondary"}
                        className="rounded-full text-xs"
                      >
                        {user.isActive ? "Actif" : "Inactif"}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}