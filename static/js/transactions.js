/**
 * Transactions view — list, add/edit modal, bulk entry, CSV import.
 */

const Transactions = (() => {

  // ---- Helpers ----

  function fmt(amount, type) {
    const sign  = type === "deposit" ? "+" : "-";
    return `${sign}$${Number(amount).toFixed(2)}`;
  }

  function fmtDate(dateStr) {
    const [y, m, d] = dateStr.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString(undefined, {
      month: "short", day: "numeric", year: "numeric"
    });
  }

  // Build a single transaction list item (shared by calendar drawer + tx list)
  function buildTxItem(tx, onRefresh) {
    const li = document.createElement("li");
    li.className = "tx-item";

    const dot = document.createElement("span");
    dot.className = `tx-dot ${tx.type}`;

    const info = document.createElement("div");
    info.className = "tx-info";

    const desc = document.createElement("div");
    desc.className = "tx-desc";
    const recurIcon = tx.recurring_template_id || tx.is_template ? " 📅" : "";
    desc.textContent = (tx.description || "(no description)") + recurIcon;

    const meta = document.createElement("div");
    meta.className = "tx-meta";
    const parts = [fmtDate(tx.date)];
    if (tx.category) parts.push(tx.category);
    if (tx.payee)    parts.push(tx.payee);
    meta.textContent = parts.join(" · ");

    info.appendChild(desc);
    info.appendChild(meta);

    const amt = document.createElement("span");
    amt.className = `tx-amount ${tx.type}`;
    amt.textContent = fmt(tx.amount, tx.type);

    const actions = document.createElement("div");
    actions.className = "tx-actions";

    const editBtn = document.createElement("button");
    editBtn.className = "btn-edit";
    editBtn.textContent = "Edit";
    editBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openEditModal(tx, onRefresh);
    });

    const delBtn = document.createElement("button");
    delBtn.className = "btn-danger";
    delBtn.textContent = "Del";
    delBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Delete this transaction?")) return;
      try {
        await API.deleteTransaction(tx.id);
        onRefresh();
      } catch (err) {
        alert("Error: " + err.message);
      }
    });

    actions.appendChild(editBtn);
    actions.appendChild(delBtn);

    li.appendChild(dot);
    li.appendChild(info);
    li.appendChild(amt);
    li.appendChild(actions);
    return li;
  }

  // ---- Transactions list ----

  const txList = document.getElementById("tx-list");
  let currentFilter = {};

  async function loadList() {
    txList.innerHTML = '<li class="tx-empty">Loading…</li>';
    try {
      const params = buildFilterParams();
      const txs = await API.getTransactions(params);
      renderList(txs);
    } catch (err) {
      txList.innerHTML = `<li class="tx-empty" style="color:var(--red)">${err.message}</li>`;
    }
  }

  function buildFilterParams() {
    const search = document.getElementById("tx-search").value.trim();
    const type   = document.getElementById("tx-type-filter").value;
    const min    = document.getElementById("tx-min").value;
    const max    = document.getElementById("tx-max").value;
    const month  = document.getElementById("tx-month-filter").value; // "YYYY-MM" or ""

    const params = {};
    if (search) params.search = search;
    if (type)   params.type   = type;
    if (min)    params.min_amount = min;
    if (max)    params.max_amount = max;
    if (month) {
      const [y, m] = month.split("-");
      params.year  = y;
      params.month = m;
    }
    return params;
  }

  function renderList(txs) {
    txList.innerHTML = "";
    if (!txs.length) {
      txList.innerHTML = '<li class="tx-empty">No transactions found</li>';
      return;
    }
    txs.forEach(tx => txList.appendChild(buildTxItem(tx, loadList)));
  }

  // Filter bar wiring
  ["tx-search","tx-type-filter","tx-min","tx-max","tx-month-filter"].forEach(id => {
    const el = document.getElementById(id);
    el.addEventListener("input", debounce(loadList, 250));
    el.addEventListener("change", loadList);
  });

  document.getElementById("tx-filter-clear").addEventListener("click", () => {
    document.getElementById("tx-search").value = "";
    document.getElementById("tx-type-filter").value = "";
    document.getElementById("tx-min").value = "";
    document.getElementById("tx-max").value = "";
    document.getElementById("tx-month-filter").value = "";
    loadList();
  });

  document.getElementById("tx-add-btn").addEventListener("click", () => {
    openAddModal(null, loadList);
  });

  // ---- Add / Edit modal ----

  const backdrop   = document.getElementById("tx-modal-backdrop");
  const form       = document.getElementById("tx-form");
  const titleEl    = document.getElementById("tx-modal-title");
  const errorEl    = document.getElementById("tx-form-error");
  let _onSave      = null;

  function openAddModal(dateStr, onSave) {
    titleEl.textContent = "Add Transaction";
    form.reset();
    document.getElementById("tx-id").value = "";
    document.getElementById("tx-date").value = dateStr || todayStr();
    document.getElementById("tx-type").value = "withdrawal";
    errorEl.hidden = true;
    _onSave = onSave;
    backdrop.hidden = false;
  }

  function openEditModal(tx, onSave) {
    titleEl.textContent = "Edit Transaction";
    document.getElementById("tx-id").value          = tx.id;
    document.getElementById("tx-date").value         = tx.date;
    document.getElementById("tx-amount").value       = tx.amount;
    document.getElementById("tx-type").value         = tx.type;
    document.getElementById("tx-description").value  = tx.description || "";
    document.getElementById("tx-category").value     = tx.category || "";
    document.getElementById("tx-payee").value        = tx.payee || "";
    document.getElementById("tx-recurrence").value   = tx.recurrence_pattern || "";
    errorEl.hidden = true;
    _onSave = onSave;
    backdrop.hidden = false;
  }

  function closeModal() {
    backdrop.hidden = true;
  }

  document.getElementById("tx-modal-close").addEventListener("click", closeModal);
  document.getElementById("tx-modal-cancel").addEventListener("click", closeModal);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) closeModal(); });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.hidden = true;

    const id         = document.getElementById("tx-id").value;
    const dateVal    = document.getElementById("tx-date").value;
    const amountVal  = parseFloat(document.getElementById("tx-amount").value);
    const typeVal    = document.getElementById("tx-type").value;
    const desc       = document.getElementById("tx-description").value.trim();
    const cat        = document.getElementById("tx-category").value.trim();
    const payee      = document.getElementById("tx-payee").value.trim();
    const recurrence = document.getElementById("tx-recurrence").value;

    if (!dateVal || isNaN(amountVal) || amountVal <= 0) {
      showError(errorEl, "Date and a positive amount are required.");
      return;
    }

    const payload = {
      date: dateVal, amount: amountVal, type: typeVal,
      description: desc, category: cat, payee,
      recurrence_pattern: recurrence || null,
      is_template: !!recurrence,
    };

    try {
      if (id) {
        await API.updateTransaction(id, payload);
      } else {
        await API.createTransaction(payload);
      }
      closeModal();
      _onSave && _onSave();
    } catch (err) {
      showError(errorEl, err.message);
    }
  });

  // ---- Bulk entry modal ----

  const bulkBackdrop = document.getElementById("bulk-modal-backdrop");
  const bulkTbody    = document.getElementById("bulk-tbody");
  const bulkError    = document.getElementById("bulk-form-error");

  function openBulkModal() {
    bulkTbody.innerHTML = "";
    addBulkRow();
    bulkError.hidden = true;
    bulkBackdrop.hidden = false;
  }

  function closeBulkModal() { bulkBackdrop.hidden = true; }

  function addBulkRow() {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="date" value="${todayStr()}" /></td>
      <td><input type="number" step="0.01" min="0.01" placeholder="0.00" /></td>
      <td>
        <select>
          <option value="withdrawal">Withdrawal</option>
          <option value="deposit">Deposit</option>
        </select>
      </td>
      <td><input type="text" placeholder="Description" /></td>
      <td><input type="text" placeholder="Category" /></td>
      <td><input type="text" placeholder="Payee" /></td>
      <td><button class="btn-danger" type="button">✕</button></td>
    `;
    tr.querySelector(".btn-danger").addEventListener("click", () => tr.remove());
    bulkTbody.appendChild(tr);
  }

  document.getElementById("bulk-modal-close").addEventListener("click", closeBulkModal);
  document.getElementById("bulk-modal-cancel").addEventListener("click", closeBulkModal);
  document.getElementById("bulk-add-row").addEventListener("click", addBulkRow);
  bulkBackdrop.addEventListener("click", (e) => { if (e.target === bulkBackdrop) closeBulkModal(); });

  document.getElementById("bulk-modal-save").addEventListener("click", async () => {
    bulkError.hidden = true;
    const rows = bulkTbody.querySelectorAll("tr");
    const items = [];

    for (const row of rows) {
      const inputs  = row.querySelectorAll("input");
      const selects = row.querySelectorAll("select");
      const dateVal = inputs[0].value;
      const amt     = parseFloat(inputs[1].value);
      const type    = selects[0].value;
      const desc    = inputs[2].value.trim();
      const cat     = inputs[3].value.trim();
      const payee   = inputs[4].value.trim();

      if (!dateVal || isNaN(amt) || amt <= 0) continue;
      items.push({ date: dateVal, amount: amt, type, description: desc, category: cat, payee });
    }

    if (!items.length) { showError(bulkError, "No valid rows to import."); return; }

    try {
      await API.createTransactionsBatch(items);
      closeBulkModal();
      loadList();
    } catch (err) {
      showError(bulkError, err.message);
    }
  });

  document.getElementById("tx-bulk-btn").addEventListener("click", openBulkModal);

  // ---- CSV import modal ----

  const csvBackdrop  = document.getElementById("csv-modal-backdrop");
  const csvFileInput = document.getElementById("csv-file");
  const csvMapGrid   = document.getElementById("csv-map-grid");
  const csvPreview   = document.getElementById("csv-preview");
  const csvResult    = document.getElementById("csv-result");
  const csvError     = document.getElementById("csv-error");
  const csvImportBtn = document.getElementById("csv-modal-import");
  let csvHeaders = [];

  function openCSVModal() {
    csvFileInput.value = "";
    csvMapGrid.innerHTML = "";
    document.getElementById("csv-column-map").hidden = true;
    csvPreview.hidden = true;
    csvResult.hidden  = true;
    csvError.hidden   = true;
    csvImportBtn.disabled = true;
    csvBackdrop.hidden = false;
  }

  function closeCSVModal() { csvBackdrop.hidden = true; }

  document.getElementById("csv-modal-close").addEventListener("click", closeCSVModal);
  document.getElementById("csv-modal-cancel").addEventListener("click", closeCSVModal);
  csvBackdrop.addEventListener("click", (e) => { if (e.target === csvBackdrop) closeCSVModal(); });

  document.getElementById("tx-csv-btn").addEventListener("click", openCSVModal);

  csvFileInput.addEventListener("change", () => {
    const file = csvFileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const lines = e.target.result.split("\n").filter(l => l.trim());
      if (!lines.length) return;

      // Parse header line (simple split, handle quoted values minimally)
      csvHeaders = lines[0].split(",").map(h => h.replace(/^"|"$/g, "").trim());

      // Build column mapper
      const mapSection = document.getElementById("csv-column-map");
      csvMapGrid.innerHTML = "";
      const fields = [
        { id: "date_col",        label: "Date *",        defaultMatch: ["date","Date","DATE"] },
        { id: "amount_col",      label: "Amount *",      defaultMatch: ["amount","Amount","AMOUNT"] },
        { id: "type_col",        label: "Type *",        defaultMatch: ["type","Type","TYPE"] },
        { id: "description_col", label: "Description",   defaultMatch: ["description","Description","memo","Memo"] },
        { id: "category_col",    label: "Category",      defaultMatch: ["category","Category"] },
        { id: "payee_col",       label: "Payee",         defaultMatch: ["payee","Payee","vendor","Vendor"] },
      ];

      for (const f of fields) {
        const lbl = document.createElement("label");
        lbl.textContent = f.label;
        const sel = document.createElement("select");
        sel.id = f.id;
        sel.className = "field-input";
        sel.innerHTML = '<option value="">(skip)</option>';
        csvHeaders.forEach(h => {
          const opt = document.createElement("option");
          opt.value = h;
          opt.textContent = h;
          if (f.defaultMatch.includes(h)) opt.selected = true;
          sel.appendChild(opt);
        });
        csvMapGrid.appendChild(lbl);
        csvMapGrid.appendChild(sel);
      }
      mapSection.hidden = false;
      csvImportBtn.disabled = false;

      // Preview
      const previewTable = document.getElementById("csv-preview-table");
      previewTable.innerHTML = "";
      const thead = document.createElement("thead");
      thead.innerHTML = `<tr>${csvHeaders.map(h => `<th>${h}</th>`).join("")}</tr>`;
      previewTable.appendChild(thead);
      const tbody = document.createElement("tbody");
      lines.slice(1, 6).forEach(line => {
        const tr = document.createElement("tr");
        tr.innerHTML = line.split(",").map(c => `<td>${c.replace(/^"|"$/g,"").trim()}</td>`).join("");
        tbody.appendChild(tr);
      });
      previewTable.appendChild(tbody);
      csvPreview.hidden = false;
    };
    reader.readAsText(file);
  });

  csvImportBtn.addEventListener("click", async () => {
    csvError.hidden  = true;
    csvResult.hidden = true;
    const file = csvFileInput.files[0];
    if (!file) return;

    const fd = new FormData();
    fd.append("file", file);
    const colIds = ["date_col","amount_col","type_col","description_col","category_col","payee_col"];
    for (const id of colIds) {
      fd.append(id.replace("_col","_col"), document.getElementById(id).value);
    }

    try {
      const result = await API.importCSV(fd);
      csvResult.textContent = `Imported ${result.imported} transaction(s).` +
        (result.skipped ? ` Skipped ${result.skipped}.` : "");
      csvResult.hidden = false;
      loadList();
    } catch (err) {
      showError(csvError, err.message);
    }
  });

  // ---- Utilities ----

  function todayStr() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  }

  function showError(el, msg) {
    el.textContent = msg;
    el.hidden = false;
  }

  function debounce(fn, ms) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
  }

  // ---- Public ----
  return { loadList, buildTxItem, openAddModal };
})();
