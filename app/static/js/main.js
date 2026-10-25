/**
 * FinTrack: Expense & Transaction Management System
 * Frontend Controller (Fetch API async updates for summary cards, alert banner, category bars, and ledger table)
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Element References
    const metricTotalSpent = document.getElementById("metric-total-spent");
    const metricMonthlyBudget = document.getElementById("metric-monthly-budget");
    const metricRemainingBudget = document.getElementById("metric-remaining-budget");
    const metricIncomeNote = document.getElementById("metric-income-note");
    const metricUtilization = document.getElementById("metric-utilization");
    const utilizationProgressBar = document.getElementById("utilization-progress-bar");

    const alertBanner = document.getElementById("budget-alert-banner");
    const alertTitle = document.getElementById("alert-title");
    const alertMessage = document.getElementById("alert-message");
    const alertEditBudgetBtn = document.getElementById("alert-edit-budget-btn");

    const openBudgetModalBtn = document.getElementById("open-budget-modal-btn");
    const inlineEditBudgetBtn = document.getElementById("inline-edit-budget-btn");
    const inlineBudgetEditor = document.getElementById("inline-budget-editor");
    const budgetInput = document.getElementById("budget-input");
    const saveBudgetBtn = document.getElementById("save-budget-btn");
    const cancelBudgetBtn = document.getElementById("cancel-budget-btn");

    const txForm = document.getElementById("transaction-form");
    const txIdInput = document.getElementById("tx-id");
    const txAmountInput = document.getElementById("tx-amount");
    const txTypeSelect = document.getElementById("tx-type");
    const txCategorySelect = document.getElementById("tx-category");
    const txDateInput = document.getElementById("tx-date");
    const txDescriptionInput = document.getElementById("tx-description");
    const formPanelTitle = document.getElementById("form-panel-title");
    const submitTxBtn = document.getElementById("submit-tx-btn");
    const cancelEditBtn = document.getElementById("cancel-edit-btn");
    const formFeedback = document.getElementById("form-feedback");

    const categoryBreakdownList = document.getElementById("category-breakdown-list");
    const transactionsTbody = document.getElementById("transactions-tbody");
    const ledgerCountLabel = document.getElementById("ledger-count-label");
    const activePeriodLabel = document.getElementById("active-period-label");

    const filterCategorySelect = document.getElementById("filter-category");
    const filterMonthInput = document.getElementById("filter-month");
    const resetFiltersBtn = document.getElementById("reset-filters-btn");
    const exportCsvBtn = document.getElementById("export-csv-btn");

    let currentTransactions = [];

    /**
     * Formats a number as USD currency string ($1,234.56)
     */
    function formatCurrency(value) {
        const num = Number(value) || 0;
        const sign = num < 0 ? "-" : "";
        return `${sign}$${Math.abs(num).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    }

    /**
     * Escapes HTML characters to prevent XSS in dynamic templates
     */
    function escapeHtml(unsafe) {
        return String(unsafe || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    /**
     * Displays transient feedback message in the transaction form panel
     */
    function showFormFeedback(message, type = "error") {
        formFeedback.textContent = message;
        formFeedback.className = `form-feedback ${type}`;
        formFeedback.classList.remove("hidden");
        if (type === "success") {
            setTimeout(() => {
                formFeedback.classList.add("hidden");
            }, 3500);
        }
    }

    /**
     * Fetches aggregated summary metrics from GET /api/summary and updates KPI cards + category bars
     */
    async function loadSummary() {
        const monthVal = filterMonthInput.value.trim();
        const query = monthVal ? `?month=${encodeURIComponent(monthVal)}` : "";

        try {
            const response = await fetch(`/api/summary${query}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to load summary metrics.");
            }

            // Update KPI Cards
            metricTotalSpent.textContent = formatCurrency(data.total_spent);
            metricMonthlyBudget.textContent = formatCurrency(data.monthly_budget);
            metricRemainingBudget.textContent = formatCurrency(data.remaining_budget);
            budgetInput.value = data.monthly_budget;

            if (data.total_income > 0) {
                metricIncomeNote.textContent = `Includes ${formatCurrency(data.total_income)} logged income this period`;
            } else {
                metricIncomeNote.textContent =
                    data.remaining_budget >= 0
                        ? "Available before reaching monthly cap"
                        : "Monthly budget exceeded";
            }

            const utilization = Number(data.budget_utilization_percent) || 0;
            metricUtilization.textContent = `${utilization.toFixed(1)}%`;

            const clampedWidth = Math.min(Math.max(utilization, 0), 100);
            utilizationProgressBar.style.width = `${clampedWidth}%`;
            utilizationProgressBar.className = "progress-fill";
            if (utilization >= 100) {
                utilizationProgressBar.classList.add("critical");
            } else if (utilization >= 80) {
                utilizationProgressBar.classList.add("warning");
            }

            // Update Dynamic Alert Banner (>= 80% warning, >= 100% critical)
            if (data.budget_alert) {
                alertBanner.classList.remove("hidden");
                if (utilization >= 100) {
                    alertBanner.classList.add("alert-critical");
                    alertTitle.textContent = "Critical Budget Alert: Monthly Limit Exceeded";
                    alertMessage.textContent = `Total spending (${formatCurrency(
                        data.total_spent
                    )}) is at ${utilization.toFixed(1)}% of your ${formatCurrency(
                        data.monthly_budget
                    )} monthly budget.`;
                } else {
                    alertBanner.classList.remove("alert-critical");
                    alertTitle.textContent = "Budget Utilization Warning (80%+ Threshold)";
                    alertMessage.textContent = `You have utilized ${utilization.toFixed(
                        1
                    )}% (${formatCurrency(data.total_spent)}) of your ${formatCurrency(
                        data.monthly_budget
                    )} monthly budget.`;
                }
            } else {
                alertBanner.classList.add("hidden");
            }

            // Render Category Breakdown Progress Bars
            renderCategoryBreakdown(data.category_breakdown || [], data.total_spent);
        } catch (err) {
            console.error("Error fetching summary:", err);
        }
    }

    /**
     * Renders visual progress bars for category spending breakdown
     */
    function renderCategoryBreakdown(breakdown, totalSpent) {
        if (!breakdown.length) {
            categoryBreakdownList.innerHTML =
                '<p class="empty-text">No expense transactions recorded for the selected period.</p>';
            return;
        }

        categoryBreakdownList.innerHTML = breakdown
            .map((item) => {
                const sharePercent =
                    totalSpent > 0 ? ((item.total / totalSpent) * 100).toFixed(1) : "0.0";
                return `
                    <div class="breakdown-item">
                        <div class="breakdown-item-header">
                            <span class="breakdown-category-name">${escapeHtml(item.category)}</span>
                            <span class="breakdown-category-metrics tabular-nums">
                                ${formatCurrency(item.total)} &middot; ${sharePercent}%
                            </span>
                        </div>
                        <div class="breakdown-bar-track">
                            <div class="breakdown-bar-fill" style="width: ${Math.min(
                                Number(sharePercent),
                                100
                            )}%;"></div>
                        </div>
                    </div>
                `;
            })
            .join("");
    }

    /**
     * Fetches filtered transactions from GET /api/transactions and populates the ledger table
     */
    async function loadTransactions() {
        const categoryVal = filterCategorySelect.value;
        const monthVal = filterMonthInput.value.trim();

        const params = new URLSearchParams();
        if (categoryVal && categoryVal !== "all") {
            params.set("category", categoryVal);
        }
        if (monthVal) {
            params.set("month", monthVal);
            activePeriodLabel.textContent = `Active Period: ${monthVal}`;
        } else {
            activePeriodLabel.textContent = "Active Period: All Months";
        }

        const queryString = params.toString() ? `?${params.toString()}` : "";

        try {
            const response = await fetch(`/api/transactions${queryString}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to load transactions.");
            }

            currentTransactions = data;
            ledgerCountLabel.textContent = `Showing ${data.length} transaction${
                data.length === 1 ? "" : "s"
            } ordered by date descending`;

            if (!data.length) {
                transactionsTbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="empty-cell">
                            No transactions match the active filter criteria.
                        </td>
                    </tr>
                `;
                return;
            }

            transactionsTbody.innerHTML = data
                .map((tx) => {
                    const isIncome = tx.transaction_type === "Income";
                    const amountPrefix = isIncome ? "+" : "-";
                    const amountClass = isIncome ? "amount-income" : "amount-expense";

                    return `
                        <tr data-id="${tx.id}">
                            <td class="tabular-nums">${escapeHtml(tx.transaction_date)}</td>
                            <td>${escapeHtml(tx.category)}</td>
                            <td>${escapeHtml(tx.description || "—")}</td>
                            <td>${escapeHtml(tx.transaction_type)}</td>
                            <td class="text-right tabular-nums ${amountClass}">
                                ${amountPrefix}${formatCurrency(tx.amount)}
                            </td>
                            <td class="text-right">
                                <div class="row-actions">
                                    <button type="button" class="text-action-btn edit-tx-btn" data-id="${tx.id}">Edit</button>
                                    <button type="button" class="btn-danger-text delete-tx-btn" data-id="${tx.id}">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `;
                })
                .join("");
        } catch (err) {
            console.error("Error fetching transactions:", err);
            transactionsTbody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-cell">Unable to load transactions. Please try again.</td>
                </tr>
            `;
        }
    }

    /**
     * Synchronizes both summary metrics and transaction table without refreshing the browser
     */
    async function refreshDashboard() {
        await Promise.all([loadSummary(), loadTransactions()]);
    }

    /**
     * Resets the Add/Edit form back to "Add Transaction" mode
     */
    function resetFormMode() {
        txIdInput.value = "";
        txForm.reset();
        formPanelTitle.textContent = "Add Transaction";
        submitTxBtn.textContent = "Save Transaction";
        cancelEditBtn.classList.add("hidden");
        formFeedback.classList.add("hidden");
    }

    /**
     * Populates the form with an existing transaction for editing
     */
    function enterEditMode(tx) {
        txIdInput.value = tx.id;
        txAmountInput.value = tx.amount;
        txTypeSelect.value = tx.transaction_type;
        txCategorySelect.value = tx.category;
        txDateInput.value = tx.transaction_date;
        txDescriptionInput.value = tx.description || "";

        formPanelTitle.textContent = `Edit Transaction #${tx.id}`;
        submitTxBtn.textContent = "Update Transaction";
        cancelEditBtn.classList.remove("hidden");
        txAmountInput.focus();
    }

    // Handle Form Submit (POST /api/transactions or PUT /api/transactions/<id>)
    txForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        formFeedback.classList.add("hidden");

        const editingId = txIdInput.value.trim();
        const payload = {
            amount: parseFloat(txAmountInput.value),
            transaction_type: txTypeSelect.value,
            category: txCategorySelect.value,
            transaction_date: txDateInput.value,
            description: txDescriptionInput.value.trim(),
        };

        const url = editingId ? `/api/transactions/${editingId}` : "/api/transactions";
        const method = editingId ? "PUT" : "POST";

        try {
            const response = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const result = await response.json();

            if (!response.ok) {
                showFormFeedback(result.error || "Validation error occurred.", "error");
                return;
            }

            resetFormMode();
            showFormFeedback(
                editingId
                    ? `Transaction #${editingId} updated successfully.`
                    : "Transaction recorded successfully.",
                "success"
            );
            await refreshDashboard();
        } catch (err) {
            showFormFeedback("Network error while saving transaction.", "error");
        }
    });

    cancelEditBtn.addEventListener("click", () => {
        resetFormMode();
    });

    // Delegate Edit and Delete Row Actions in Ledger Table
    transactionsTbody.addEventListener("click", async (event) => {
        const editBtn = event.target.closest(".edit-tx-btn");
        if (editBtn) {
            const txId = Number(editBtn.dataset.id);
            const targetTx = currentTransactions.find((item) => item.id === txId);
            if (targetTx) {
                enterEditMode(targetTx);
            }
            return;
        }

        const deleteBtn = event.target.closest(".delete-tx-btn");
        if (deleteBtn) {
            const txId = Number(deleteBtn.dataset.id);
            try {
                const response = await fetch(`/api/transactions/${txId}`, {
                    method: "DELETE",
                });
                if (response.ok) {
                    if (Number(txIdInput.value) === txId) {
                        resetFormMode();
                    }
                    await refreshDashboard();
                }
            } catch (err) {
                console.error("Failed to delete transaction:", err);
            }
        }
    });

    // Inline Budget Editor Controls (PUT /api/budget)
    function toggleBudgetEditor(show) {
        if (show) {
            metricMonthlyBudget.classList.add("hidden");
            inlineBudgetEditor.classList.remove("hidden");
            budgetInput.focus();
        } else {
            metricMonthlyBudget.classList.remove("hidden");
            inlineBudgetEditor.classList.add("hidden");
        }
    }

    inlineEditBudgetBtn.addEventListener("click", () => toggleBudgetEditor(true));
    openBudgetModalBtn.addEventListener("click", () => toggleBudgetEditor(true));
    alertEditBudgetBtn.addEventListener("click", () => toggleBudgetEditor(true));
    cancelBudgetBtn.addEventListener("click", () => toggleBudgetEditor(false));

    saveBudgetBtn.addEventListener("click", async () => {
        const newBudget = parseFloat(budgetInput.value);
        if (isNaN(newBudget) || newBudget <= 0) {
            showFormFeedback("Monthly budget must be a positive number greater than 0.", "error");
            return;
        }

        try {
            const response = await fetch("/api/budget", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ monthly_budget: newBudget }),
            });
            const result = await response.json();

            if (!response.ok) {
                showFormFeedback(result.error || "Failed to update budget.", "error");
                return;
            }

            toggleBudgetEditor(false);
            await refreshDashboard();
        } catch (err) {
            console.error("Failed to update budget:", err);
        }
    });

    // Filter Controls
    filterCategorySelect.addEventListener("change", () => {
        loadTransactions();
    });

    filterMonthInput.addEventListener("change", () => {
        refreshDashboard();
    });

    resetFiltersBtn.addEventListener("click", () => {
        filterCategorySelect.value = "all";
        filterMonthInput.value = "";
        refreshDashboard();
    });

    // Export CSV Action
    exportCsvBtn.addEventListener("click", () => {
        if (!currentTransactions.length) return;
        const headers = ["ID", "Date", "Category", "Type", "Amount", "Description"];
        const rows = currentTransactions.map((tx) => [
            tx.id,
            tx.transaction_date,
            `"${String(tx.category).replace(/"/g, '""')}"`,
            tx.transaction_type,
            tx.amount.toFixed(2),
            `"${String(tx.description || "").replace(/"/g, '""')}"`,
        ]);
        const csvContent =
            "data:text/csv;charset=utf-8," +
            [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `fintrack_transactions_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Initial Dashboard Load
    refreshDashboard();
});
