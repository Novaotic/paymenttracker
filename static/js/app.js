/**
 * App bootstrap — view routing, balance updates, navigation wiring.
 */

(async () => {

  // ---- View routing ----

  const views   = document.querySelectorAll(".view");
  const navBtns = document.querySelectorAll(".nav-btn");

  function showView(name) {
    views.forEach(v => v.classList.toggle("active", v.id === `view-${name}`));
    navBtns.forEach(b => b.classList.toggle("active", b.dataset.view === name));
    if (name === "calendar")     Calendar.refresh();
    if (name === "transactions") Transactions.loadList();
    if (name === "balances")     Balances.load();
  }

  navBtns.forEach(btn => {
    btn.addEventListener("click", () => showView(btn.dataset.view));
  });

  // ---- Balance widget (top bar) ----

  async function refreshTopBalance() {
    try {
      const res = await API.getCurrentBalance();
      const el  = document.getElementById("top-balance");
      el.textContent = formatMoney(res.balance);
      el.style.color = res.balance >= 0 ? "var(--green)" : "var(--red)";
    } catch { /* silently ignore */ }
  }

  // ---- Balances view ----

  const Balances = (() => {
    let year  = new Date().getFullYear();
    let month = new Date().getMonth() + 1;

    const monthLabel = document.getElementById("bal-month-label");
    const heroAmount = document.getElementById("balance-hero-amount");
    const tbody      = document.getElementById("weekly-tbody");

    const MONTHS = [
      "January","February","March","April","May","June",
      "July","August","September","October","November","December"
    ];

    async function load() {
      monthLabel.textContent = `${MONTHS[month - 1]} ${year}`;

      // Hero balance — end of the month
      try {
        const lastDay = new Date(year, month, 0).getDate();
        const asOf = `${year}-${String(month).padStart(2,"0")}-${String(lastDay).padStart(2,"0")}`;
        const balRes = await API.getCurrentBalance(asOf);
        heroAmount.textContent = formatMoney(balRes.balance);
        heroAmount.style.color = balRes.balance >= 0 ? "var(--green)" : "var(--red)";
      } catch {
        heroAmount.textContent = "—";
      }

      // Weekly table
      try {
        const weeks = await API.getWeeklyBalances(year, month);
        tbody.innerHTML = "";
        weeks.forEach(w => {
          const tr = document.createElement("tr");
          const startLabel = fmtDateRange(w.week_start, w.week_end);
          const netClass = w.net_change >= 0 ? "pos" : "neg";
          tr.innerHTML = `
            <td>${startLabel}</td>
            <td class="num-col">${formatMoney(w.starting_balance)}</td>
            <td class="num-col">${formatMoney(w.ending_balance)}</td>
            <td class="num-col ${netClass}">${formatSignedMoney(w.net_change)}</td>
          `;
          tbody.appendChild(tr);
        });
      } catch {
        tbody.innerHTML = '<tr><td colspan="4" class="tx-empty">Could not load</td></tr>';
      }
    }

    function fmtDateRange(startStr, endStr) {
      const fmt = (s) => {
        const [y, m, d] = s.split("-").map(Number);
        return new Date(y, m - 1, d).toLocaleDateString(undefined, { month: "short", day: "numeric" });
      };
      return `${fmt(startStr)} – ${fmt(endStr)}`;
    }

    document.getElementById("bal-prev").addEventListener("click", () => {
      if (month === 1) { year--; month = 12; } else month--;
      load();
    });
    document.getElementById("bal-next").addEventListener("click", () => {
      if (month === 12) { year++; month = 1; } else month++;
      load();
    });

    return { load };
  })();

  // ---- Formatting helpers ----

  function formatMoney(value) {
    const abs = Math.abs(value);
    const sign = value < 0 ? "-" : "";
    return `${sign}$${abs.toFixed(2)}`;
  }

  function formatSignedMoney(value) {
    const sign = value >= 0 ? "+" : "-";
    return `${sign}$${Math.abs(value).toFixed(2)}`;
  }

  // Make formatMoney globally available for transaction items
  window.formatMoney = formatMoney;

  // ---- Init ----

  await Calendar.load(new Date().getFullYear(), new Date().getMonth() + 1);
  refreshTopBalance();
  showView("calendar");

  // Refresh top balance whenever a transaction changes (after modal saves, etc.)
  // We do this by polling lightly — re-fetch on view switch
  navBtns.forEach(btn => {
    btn.addEventListener("click", refreshTopBalance);
  });

})();
