import { useEffect, useMemo, useState } from "react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import { fetchCashState, addCashTransaction } from "../lib/api";

interface Transaction {
  id: number;
  transaction_date: string;
  amount: number;
  transaction_type: "income" | "expense";
  label: string;
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr);

  const formatted = date.toLocaleDateString("fr-BE", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

function formatAmount(value: number) {
  return `${value.toFixed(2)} €`;
}

export function CashPage() {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  const [amount, setAmount] = useState("");
  const [label, setLabel] = useState("");
  const [isSubmitting, setIsSubmitting] = useState<"income" | "expense" | null>(null);

  async function loadCash() {
    try {
      const data = await fetchCashState();
      setBalance(data.balance || 0);
      setTransactions(data.transactions || []);
    } catch (error) {
      console.error(error);
      toast.error("Erreur chargement trésorerie");
    }
  }

  useEffect(() => {
    loadCash();
  }, []);

  const sortedTransactions = useMemo(() => {
    return [...transactions].sort((a, b) => {
      if (a.transaction_date === b.transaction_date) {
        return b.id - a.id;
      }
      return b.transaction_date.localeCompare(a.transaction_date);
    });
  }, [transactions]);

  async function handleAdd(type: "income" | "expense") {
    const value = parseFloat(amount);

    if (!value || value <= 0) {
      toast.error("Montant invalide");
      return;
    }

    try {
      setIsSubmitting(type);

      await addCashTransaction({
        type,
        amount: value,
        label: label.trim(),
      });

      toast.success(
        type === "income" ? "Entrée ajoutée" : "Dépense ajoutée"
      );

      setAmount("");
      setLabel("");

      await loadCash();
    } catch (error) {
      console.error(error);
      toast.error("Erreur ajout transaction");
    } finally {
      setIsSubmitting(null);
    }
  }

  return (
    <div className="space-y-6 pb-20">
      <Card className="rounded-2xl shadow-sm border-0">
        <CardContent className="p-6 text-center">
          <div className="text-sm text-muted-foreground">Solde actuel</div>
          <div className="text-3xl font-bold mt-2">
            {formatAmount(balance)}
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl shadow-sm border-0">
        <CardContent className="p-4 space-y-3">
          <Input
            type="number"
            min="0"
            step="0.01"
            placeholder="Montant (€)"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />

          <Input
            placeholder="Description"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Button
              className="w-full rounded-full"
              onClick={() => handleAdd("income")}
              disabled={isSubmitting !== null}
            >
              {isSubmitting === "income" ? "Ajout..." : "+ Entrée"}
            </Button>

            <Button
              variant="outline"
              className="w-full rounded-full"
              onClick={() => handleAdd("expense")}
              disabled={isSubmitting !== null}
            >
              {isSubmitting === "expense" ? "Ajout..." : "- Dépense"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {sortedTransactions.length === 0 ? (
          <Card className="rounded-2xl shadow-sm border-0">
            <CardContent className="py-8 text-center text-muted-foreground">
              Aucune transaction pour le moment.
            </CardContent>
          </Card>
        ) : (
          sortedTransactions.map((transaction) => (
            <Card key={transaction.id} className="rounded-2xl shadow-sm border-0">
              <CardContent className="p-4 flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="font-medium break-words">
                    {transaction.label?.trim() || "Sans description"}
                  </div>

                  <div className="text-xs text-muted-foreground mt-1">
                    {formatDate(transaction.transaction_date)}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2 shrink-0">
                  <Badge
                    variant={
                      transaction.transaction_type === "income"
                        ? "default"
                        : "secondary"
                    }
                    className="rounded-full"
                  >
                    {transaction.transaction_type === "income" ? "Entrée" : "Dépense"}
                  </Badge>

                  <div
                    className={`font-semibold ${
                      transaction.transaction_type === "income"
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {transaction.transaction_type === "income" ? "+" : "-"}
                    {formatAmount(transaction.amount)}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}