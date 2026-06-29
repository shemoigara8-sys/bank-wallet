"use strict";

// ===============================
// K Wallet Admin Dashboard
// ===============================

let lineChart = null;
let pieChart = null;
let usersChart = null;

// ===============================
// Load Everything
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    loadStats();
    loadUsers();
    loadTransactions();

    loadLineChart();
    loadPieChart();
    loadUsersChart();

});

// ===============================
// Statistics
// ===============================

async function loadStats() {

    const res = await fetch("/admin/stats");
    const data = await res.json();

    document.getElementById("total-users").innerHTML =
        data.users;

    document.getElementById("total-transactions").innerHTML =
        data.transactions;

    document.getElementById("total-money").innerHTML =
        "KES " + Number(data.money).toLocaleString();

}

// ===============================
// Users Table
// ===============================

async function loadUsers() {

    const res = await fetch("/admin/users");

    const users = await res.json();

    const table = document.getElementById("users-table");

    table.innerHTML = "";

    users.forEach(user => {

        table.innerHTML += `
        <tr>
            <td>${user.username}</td>
            <td>${user.account}</td>
            <td>KES ${Number(user.balance).toLocaleString()}</td>
        </tr>
        `;

    });

}

// ===============================
// Transactions Table
// ===============================

async function loadTransactions() {

    const res = await fetch("/admin/transactions");

    const transactions = await res.json();

    const table = document.getElementById("transactions-table");

    table.innerHTML = "";

    transactions.forEach(tx => {

        table.innerHTML += `
        <tr>
            <td>${tx.from}</td>
            <td>${tx.to}</td>
            <td>KES ${Number(tx.amount).toLocaleString()}</td>
            <td>${tx.date}</td>
        </tr>
        `;

    });

}

// ===============================
// Transactions Line Chart
// ===============================

async function loadLineChart() {

    const res = await fetch("/admin/chart");

    const data = await res.json();

    const ctx =
        document.getElementById("transactionsChart");

    if (!ctx) return;

    if (lineChart)
        lineChart.destroy();

    lineChart = new Chart(ctx, {

        type: "line",

        data: {

            labels: data.labels,

            datasets: [{

                label: "Transactions",

                data: data.values,

                borderWidth: 3,

                tension: .4,

                fill: true

            }]

        },

        options: {

            responsive: true,

            plugins: {

                legend: {

                    display: true

                }

            }

        }

    });

}

// ===============================
// Pie Chart
// ===============================

async function loadPieChart() {

    const res = await fetch("/admin/pie");

    const data = await res.json();

    const ctx =
        document.getElementById("pieChart");

    if (!ctx) return;

    if (pieChart)
        pieChart.destroy();

    pieChart = new Chart(ctx, {

        type: "pie",

        data: {

            labels: [

                "Money Sent",

                "Money In Wallets"

            ],

            datasets: [{

                data: [

                    data.sent,

                    data.wallets

                ]

            }]

        },

        options: {

            responsive: true

        }

    });

}

// ===============================
// Top Wallets Chart
// ===============================

async function loadUsersChart() {

    const res =
        await fetch("/admin/top-users");

    const data =
        await res.json();

    const ctx =
        document.getElementById("usersChart");

    if (!ctx) return;

    if (usersChart)
        usersChart.destroy();

    usersChart = new Chart(ctx, {

        type: "bar",

        data: {

            labels: data.labels,

            datasets: [{

                label: "Wallet Balance",

                data: data.balances,

                borderWidth: 2

            }]

        },

        options: {

            responsive: true,

            plugins: {

                legend: {

                    display: false

                }

            }

        }

    });

}