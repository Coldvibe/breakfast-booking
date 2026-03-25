import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { Plus, Mail, Phone, UserCheck, UserX } from "lucide-react";
import { toast } from "sonner";

interface Agent {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: "admin" | "gestionnaire" | "utilisateur";
  isActive: boolean;
}

const INITIAL_AGENTS: Agent[] = [
  {
    id: "1",
    name: "Marie Dupont",
    email: "marie.dupont@example.com",
    phone: "06 12 34 56 78",
    role: "admin",
    isActive: true,
  },
  {
    id: "2",
    name: "Jean Martin",
    email: "jean.martin@example.com",
    phone: "06 98 76 54 32",
    role: "gestionnaire",
    isActive: true,
  },
  {
    id: "3",
    name: "Sophie Bernard",
    email: "sophie.bernard@example.com",
    phone: "06 45 67 89 01",
    role: "utilisateur",
    isActive: false,
  },
];

export function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);
  const [newName, setNewName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPhone, setNewPhone] = useState("");

  const handleAddAgent = () => {
    if (!newName.trim() || !newEmail.trim()) {
      toast.error("Veuillez remplir le nom et l'email");
      return;
    }

    const newAgent: Agent = {
      id: Date.now().toString(),
      name: newName,
      email: newEmail,
      phone: newPhone,
      role: "utilisateur",
      isActive: true,
    };

    setAgents([...agents, newAgent]);
    toast.success("Agent ajouté");

    setNewName("");
    setNewEmail("");
    setNewPhone("");
  };

  const toggleAgentStatus = (id: string) => {
    setAgents(
      agents.map((agent) =>
        agent.id === id ? { ...agent, isActive: !agent.isActive } : agent
      )
    );
    toast.success("Statut modifié");
  };

  const getRoleBadge = (role: string) => {
    const variants: Record<string, "default" | "secondary" | "outline"> = {
      admin: "default",
      gestionnaire: "secondary",
      utilisateur: "outline",
    };
    return variants[role] || "outline";
  };

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      admin: "Admin",
      gestionnaire: "Gestionnaire",
      utilisateur: "Utilisateur",
    };
    return labels[role] || role;
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="space-y-6 pb-20">
      {/* Formulaire d'ajout */}
      <Card className="rounded-2xl border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="size-5" />
            Ajouter un agent
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="agent-name" className="text-sm text-muted-foreground">
              Nom complet
            </Label>
            <Input
              id="agent-name"
              placeholder="Ex: Marie Dupont"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="agent-email" className="text-sm text-muted-foreground">
              Email
            </Label>
            <Input
              id="agent-email"
              type="email"
              placeholder="Ex: marie.dupont@example.com"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="agent-phone" className="text-sm text-muted-foreground">
              Téléphone (optionnel)
            </Label>
            <Input
              id="agent-phone"
              type="tel"
              placeholder="Ex: 06 12 34 56 78"
              value={newPhone}
              onChange={(e) => setNewPhone(e.target.value)}
              className="rounded-xl border-gray-200"
            />
          </div>

          <Button className="w-full rounded-full h-12" onClick={handleAddAgent}>
            <Plus className="size-4 mr-2" />
            Ajouter l'agent
          </Button>
        </CardContent>
      </Card>

      {/* Liste des agents */}
      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Agents ({agents.length})</h2>
        <div className="space-y-3">
          {agents.map((agent) => (
            <Card key={agent.id} className="rounded-2xl border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <Avatar className="size-12">
                    <AvatarFallback className="bg-primary/10 text-primary">
                      {getInitials(agent.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold">{agent.name}</h4>
                        <Badge
                          variant={getRoleBadge(agent.role)}
                          className="rounded-full mt-1"
                        >
                          {getRoleLabel(agent.role)}
                        </Badge>
                      </div>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => toggleAgentStatus(agent.id)}
                        className="rounded-full"
                      >
                        {agent.isActive ? (
                          <UserCheck className="size-4 text-green-600" />
                        ) : (
                          <UserX className="size-4 text-gray-400" />
                        )}
                      </Button>
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Mail className="size-3.5" />
                        {agent.email}
                      </div>
                      {agent.phone && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Phone className="size-3.5" />
                          {agent.phone}
                        </div>
                      )}
                    </div>
                    <div className="mt-2">
                      <Badge
                        variant={agent.isActive ? "default" : "secondary"}
                        className="rounded-full text-xs"
                      >
                        {agent.isActive ? "Actif" : "Inactif"}
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
