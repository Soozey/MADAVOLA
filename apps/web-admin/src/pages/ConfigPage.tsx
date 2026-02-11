import { FormEvent, useEffect, useMemo, useState } from "react";
import { createConfig, deleteConfig, listConfigs, updateConfig } from "../lib/api";

type ConfigItem = {
  id: number;
  key: string;
  value: string | null;
  description: string | null;
  updated_at: string | null;
};

export default function ConfigPage() {
  const [items, setItems] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [form, setForm] = useState({ key: "", value: "", description: "" });
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadConfigs = async (key?: string) => {
    setLoading(true);
    setMessage(null);
    try {
      const data = await listConfigs(key);
      setItems(Array.isArray(data) ? data : []);
    } catch (error: any) {
      setMessage(error?.response?.data?.detail?.message ?? "Erreur de chargement des configurations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadConfigs();
  }, []);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return items;
    return items.filter(
      (c) =>
        c.key.toLowerCase().includes(term) ||
        (c.value ?? "").toLowerCase().includes(term) ||
        (c.description ?? "").toLowerCase().includes(term)
    );
  }, [items, search]);

  const resetForm = () => {
    setForm({ key: "", value: "", description: "" });
    setEditingId(null);
  };

  const startEdit = (item: ConfigItem) => {
    setEditingId(item.id);
    setForm({
      key: item.key,
      value: item.value ?? "",
      description: item.description ?? "",
    });
    setMessage(null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!form.key.trim()) {
      setMessage("La clé est obligatoire.");
      return;
    }

    setSaving(true);
    setMessage(null);
    try {
      if (editingId) {
        await updateConfig(editingId, {
          value: form.value,
          description: form.description || undefined,
        });
        setMessage("Configuration mise à jour.");
      } else {
        await createConfig({
          key: form.key.trim(),
          value: form.value,
          description: form.description || undefined,
        });
        setMessage("Configuration créée.");
      }
      resetForm();
      await loadConfigs();
    } catch (error: any) {
      setMessage(error?.response?.data?.detail?.message ?? "Erreur lors de l'enregistrement.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    setSaving(true);
    setMessage(null);
    try {
      await deleteConfig(id);
      setMessage("Configuration supprimée.");
      if (editingId === id) {
        resetForm();
      }
      await loadConfigs();
    } catch (error: any) {
      setMessage(error?.response?.data?.detail?.message ?? "Erreur lors de la suppression.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h1>Configuration système</h1>
      <p style={{ color: "#666", marginBottom: "1rem" }}>
        Gestion des clés applicatives (accès réservé aux administrateurs).
      </p>

      <form
        onSubmit={handleSubmit}
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr auto",
          gap: "0.75rem",
          alignItems: "end",
          marginBottom: "1rem",
        }}
      >
        <label style={{ display: "grid", gap: "0.25rem" }}>
          Clé
          <input
            value={form.key}
            disabled={saving || editingId !== null}
            onChange={(e) => setForm((prev) => ({ ...prev, key: e.target.value }))}
            placeholder="ex: app.name"
          />
        </label>
        <label style={{ display: "grid", gap: "0.25rem" }}>
          Valeur
          <input
            value={form.value}
            disabled={saving}
            onChange={(e) => setForm((prev) => ({ ...prev, value: e.target.value }))}
            placeholder="valeur"
          />
        </label>
        <label style={{ display: "grid", gap: "0.25rem" }}>
          Description
          <input
            value={form.description}
            disabled={saving}
            onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
            placeholder="description optionnelle"
          />
        </label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="submit" disabled={saving}>
            {saving ? "..." : editingId ? "Mettre à jour" : "Créer"}
          </button>
          {editingId ? (
            <button type="button" onClick={resetForm} disabled={saving}>
              Annuler
            </button>
          ) : null}
        </div>
      </form>

      <div style={{ marginBottom: "1rem" }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filtrer (clé, valeur, description)"
          style={{ minWidth: "360px" }}
        />
      </div>

      {message ? (
        <p style={{ marginBottom: "1rem", color: message.toLowerCase().includes("erreur") ? "#c00" : "#080" }}>
          {message}
        </p>
      ) : null}

      {loading ? (
        <div>Chargement...</div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.5rem" }}>Clé</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.5rem" }}>Valeur</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.5rem" }}>Description</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.5rem" }}>Maj</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.5rem" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id}>
                <td style={{ borderBottom: "1px solid #eee", padding: "0.5rem" }}>{item.key}</td>
                <td style={{ borderBottom: "1px solid #eee", padding: "0.5rem" }}>{item.value ?? ""}</td>
                <td style={{ borderBottom: "1px solid #eee", padding: "0.5rem" }}>{item.description ?? ""}</td>
                <td style={{ borderBottom: "1px solid #eee", padding: "0.5rem" }}>
                  {item.updated_at ? new Date(item.updated_at).toLocaleString() : "-"}
                </td>
                <td style={{ borderBottom: "1px solid #eee", padding: "0.5rem", display: "flex", gap: "0.5rem" }}>
                  <button type="button" onClick={() => startEdit(item)} disabled={saving}>
                    Éditer
                  </button>
                  <button type="button" onClick={() => void handleDelete(item.id)} disabled={saving}>
                    Supprimer
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
