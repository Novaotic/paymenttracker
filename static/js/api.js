/**
 * Thin fetch() wrappers for the Payment Tracker REST API.
 * All functions return parsed JSON (or throw on non-2xx).
 */

const API = (() => {
  async function request(method, path, body = null) {
    const opts = {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
    };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(path, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) {
      const msg = data?.detail ?? `HTTP ${res.status}`;
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    return data;
  }

  // ---- Transactions ----

  function getTransactions(params = {}) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== null && v !== undefined && v !== "")
    ).toString();
    return request("GET", `/api/transactions${qs ? "?" + qs : ""}`);
  }

  function getTransaction(id) {
    return request("GET", `/api/transactions/${id}`);
  }

  function createTransaction(data) {
    return request("POST", "/api/transactions", data);
  }

  function updateTransaction(id, data) {
    return request("PUT", `/api/transactions/${id}`, data);
  }

  function deleteTransaction(id) {
    return request("DELETE", `/api/transactions/${id}`);
  }

  function createTransactionsBatch(transactions) {
    return request("POST", "/api/transactions/batch", { transactions });
  }

  function getTemplates() {
    return request("GET", "/api/transactions/templates");
  }

  // ---- Balances ----

  function getCurrentBalance(asOf = null) {
    const qs = asOf ? `?as_of=${asOf}` : "";
    return request("GET", `/api/balances/current${qs}`);
  }

  function getWeeklyBalances(year, month) {
    return request("GET", `/api/balances/weekly?year=${year}&month=${month}`);
  }

  // ---- Import ----

  async function importCSV(formData) {
    const res = await fetch("/api/import/csv", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.detail ?? `HTTP ${res.status}`);
    return data;
  }

  return {
    getTransactions,
    getTransaction,
    createTransaction,
    updateTransaction,
    deleteTransaction,
    createTransactionsBatch,
    getTemplates,
    getCurrentBalance,
    getWeeklyBalances,
    importCSV,
  };
})();
