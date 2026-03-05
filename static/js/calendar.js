/**
 * Calendar view — renders a month grid with deposit/withdrawal dot indicators.
 * Clicking a day opens the day drawer with that day's transactions.
 */

const Calendar = (() => {
  const MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
  ];
  const DAYS_OF_WEEK = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

  let currentYear  = new Date().getFullYear();
  let currentMonth = new Date().getMonth() + 1; // 1-based
  let allTransactions = []; // transactions for the visible month
  let selectedDate = null;

  // ---- DOM refs ----
  const grid       = document.getElementById("calendar-grid");
  const monthLabel = document.getElementById("cal-month-label");
  const drawer     = document.getElementById("day-drawer");
  const drawerDate = document.getElementById("day-drawer-date");
  const drawerList = document.getElementById("day-drawer-list");
  const drawerAdd  = document.getElementById("day-drawer-add");
  const drawerClose= document.getElementById("day-drawer-close");

  // ---- Public: load and render ----
  async function load(year, month) {
    currentYear  = year;
    currentMonth = month;

    try {
      allTransactions = await API.getTransactions({ year, month });
    } catch {
      allTransactions = [];
    }

    render();
  }

  function render() {
    monthLabel.textContent = `${MONTHS[currentMonth - 1]} ${currentYear}`;

    // Remove old day cells (keep the 7 dow headers)
    const dayCells = grid.querySelectorAll(".cal-day");
    dayCells.forEach(c => c.remove());

    const firstDay = new Date(currentYear, currentMonth - 1, 1).getDay(); // 0=Sun
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    const today = new Date();

    // Group transactions by date string YYYY-MM-DD
    const byDate = {};
    for (const tx of allTransactions) {
      byDate[tx.date] = byDate[tx.date] || { deposit: 0, withdrawal: 0 };
      byDate[tx.date][tx.type]++;
    }

    // Blank cells before first day
    for (let i = 0; i < firstDay; i++) {
      const blank = document.createElement("div");
      blank.className = "cal-day empty";
      grid.appendChild(blank);
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const cell = document.createElement("div");
      cell.className = "cal-day";

      const isToday =
        d === today.getDate() &&
        currentMonth === today.getMonth() + 1 &&
        currentYear  === today.getFullYear();
      if (isToday) cell.classList.add("today");

      const dateStr = `${currentYear}-${String(currentMonth).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
      if (selectedDate === dateStr) cell.classList.add("selected");

      const num = document.createElement("span");
      num.textContent = d;
      cell.appendChild(num);

      // Dots
      const info = byDate[dateStr];
      if (info) {
        const dots = document.createElement("div");
        dots.className = "cal-dots";
        if (info.deposit > 0) {
          const dot = document.createElement("span");
          dot.className = "cal-dot deposit";
          dots.appendChild(dot);
        }
        if (info.withdrawal > 0) {
          const dot = document.createElement("span");
          dot.className = "cal-dot withdrawal";
          dots.appendChild(dot);
        }
        cell.appendChild(dots);
      }

      cell.addEventListener("click", () => openDrawer(dateStr));
      grid.appendChild(cell);
    }
  }

  // ---- Day drawer ----
  function openDrawer(dateStr) {
    selectedDate = dateStr;
    render(); // re-render to highlight selected

    const [y, m, d] = dateStr.split("-").map(Number);
    drawerDate.textContent = new Date(y, m - 1, d).toLocaleDateString(undefined, {
      weekday: "long", year: "numeric", month: "long", day: "numeric"
    });

    const dayTxs = allTransactions.filter(t => t.date === dateStr);
    drawerList.innerHTML = "";
    if (dayTxs.length === 0) {
      drawerList.innerHTML = '<li class="tx-empty">No transactions</li>';
    } else {
      dayTxs.forEach(tx => {
        drawerList.appendChild(Transactions.buildTxItem(tx, () => {
          load(currentYear, currentMonth);
          openDrawer(dateStr);
        }));
      });
    }

    drawer.hidden = false;
    drawer.scrollIntoView({ behavior: "smooth", block: "nearest" });

    // Pass date to add button
    drawerAdd.dataset.date = dateStr;
  }

  function closeDrawer() {
    drawer.hidden = true;
    selectedDate = null;
    render();
  }

  // ---- Navigation ----
  function prevMonth() {
    if (currentMonth === 1) { currentYear--; currentMonth = 12; }
    else currentMonth--;
    closeDrawer();
    load(currentYear, currentMonth);
  }

  function nextMonth() {
    if (currentMonth === 12) { currentYear++; currentMonth = 1; }
    else currentMonth++;
    closeDrawer();
    load(currentYear, currentMonth);
  }

  // ---- Wiring ----
  document.getElementById("cal-prev").addEventListener("click", prevMonth);
  document.getElementById("cal-next").addEventListener("click", nextMonth);
  drawerClose.addEventListener("click", closeDrawer);

  drawerAdd.addEventListener("click", () => {
    Transactions.openAddModal(drawerAdd.dataset.date, () => {
      load(currentYear, currentMonth);
      openDrawer(drawerAdd.dataset.date);
    });
  });

  // ---- Public API ----
  return {
    load,
    get year()  { return currentYear; },
    get month() { return currentMonth; },
    refresh() { load(currentYear, currentMonth); },
  };
})();
