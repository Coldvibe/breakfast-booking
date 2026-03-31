import { useEffect, useState } from "react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "sonner";
import { fetchCashState, addCashTransaction } from "../lib/api";

interface Transaction {
  id: number;
  transaction_date: string;
  amount: number;
  transaction_type: "income" | "expense";
  label: string;
}

export function CashPage() {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  const [amount, setAmount] = useState("");
  const [label, setLabel] = useState("");

  async function loadCash() {
    try {
      const data = await fetchCashState();
      setBalance(data.balance || 0);
      setTransactions(data.transactions || []);
    } catch (e) {
      console.error(e);
      toast.error("Erreur chargement trésorerie");
    }
  }

  useEffect(() => {
    loadCash();
  }, []);

  async function handleAdd(type: "income" | "expense") {
    const value = parseFloat(amount);

    if (!value || value <= 0) {
      toast.error("Montant invalide");
      return;
    }

    try {
      await addCashTransaction({
        type,
        amount: value,
        label,
      });

      toast.success("Transaction ajoutée");

      setAmount("");
      setLabel("");

      await loadCash();
    } catch (e) {
      console.error(e);
      toast.error("Erreur ajout transaction");
    }
  }

  return (
    <div className="space-y-6 pb-20">

      {/* Balance */}
      <Card className="rounded-2xl shadow-sm">
        <CardContent className="p-6 text-center">
          <div className="text-sm text-muted-foreground">Solde actuel</div>
          <div className="text-3xl font-bold mt-2">
            {balance.toFixed(2)} €
          </div>
        </CardContent>
      </Card>

      {/* Form */}
      <Card className="rounded-2xl shadow-sm">
        <CardContent className="p-4 space-y-3">
          <Input
            placeholder="Montant (€)"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />

          <Input
            placeholder="Description"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <Button
              className="w-full"
              onClick={() => handleAdd("income")}
            >
              + Entrée
            </Button>

            <Button
              variant="outline"
              className="w-full"
              onClick={() => handleAdd("expense")}
            >
              - Dépense
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Transactions */}
      <div className="space-y-2">
        {transactions.map((t) => (
          <Card key={t.id} className="rounded-xl shadow-sm">
            <CardContent className="p-3 flex justify-between items-center">
              <div>
                <div className="font-medium">
                  {t.label || "Sans description"}
                </div>
                <div className="text-xs text-muted-foreground">
                  {t.transaction_date}
                </div>
              </div>

              <div
                className={`font-semibold ${
                  t.transaction_type === "income"
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {t.transaction_type === "income" ? "+" : "-"}
                {t.amount.toFixed(2)} €
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}