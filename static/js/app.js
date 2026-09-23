/* =========================================================
   DELETE CONFIRMATION
   ========================================================= */

function confirmDelete() {

    return confirm(
        "Are you sure you want to delete this item?"
    );

}


/* =========================================================
   DATE INPUT DEFAULT
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const dateInputs =
            document.querySelectorAll(
                'input[type="date"]'
            );

        dateInputs.forEach(function (input) {

            if (!input.value) {

                const today =
                    new Date()
                    .toISOString()
                    .split("T")[0];

                input.value = today;

            }

        });


        /* =================================================
           DASHBOARD CHARTS
           ================================================= */

        initializeDashboardCharts();

    }
);


/* =========================================================
   DASHBOARD CHART INITIALIZATION
   ========================================================= */

function initializeDashboardCharts() {

    /*
     * Check whether Chart.js is available.
     * This prevents errors on other pages.
     */

    if (typeof Chart === "undefined") {
        return;
    }


    /*
     * Find dashboard chart elements.
     */

    const expenseCanvas =
        document.getElementById(
            "expenseCategoryChart"
        );

    const incomeExpenseCanvas =
        document.getElementById(
            "incomeExpenseChart"
        );


    /*
     * If neither chart exists, this is not
     * the dashboard page.
     */

    if (
        !expenseCanvas &&
        !incomeExpenseCanvas
    ) {
        return;
    }


    /* =====================================================
       GET DASHBOARD DATA
       ===================================================== */

    const dashboardData =
        document.getElementById(
            "dashboardChartData"
        );


    if (!dashboardData) {
        return;
    }


    let categoryLabels = [];
    let categoryValues = [];
    let totalIncome = 0;
    let totalExpenses = 0;


    try {

        categoryLabels =
            JSON.parse(
                dashboardData.dataset.categories || "[]"
            );

        categoryValues =
            JSON.parse(
                dashboardData.dataset.categoryValues || "[]"
            );

        totalIncome =
            Number(
                dashboardData.dataset.income || 0
            );

        totalExpenses =
            Number(
                dashboardData.dataset.expenses || 0
            );

    }

    catch (error) {

        console.error(
            "Unable to load dashboard chart data:",
            error
        );

        return;

    }


    /* =====================================================
       CHART COLORS
       ===================================================== */

    const categoryColors = [

        "#082f63",
        "#174f91",
        "#365273",
        "#475569",
        "#64748b",
        "#94a3b8",
        "#111827",
        "#1e3a5f"

    ];


    /* =====================================================
       EXPENSE CATEGORY DOUGHNUT
       ===================================================== */

    if (expenseCanvas) {

        new Chart(
            expenseCanvas,
            {

                type: "doughnut",

                data: {

                    labels: categoryLabels,

                    datasets: [

                        {

                            data: categoryValues,

                            backgroundColor:
                                categoryColors,

                            borderWidth: 2,

                            borderColor:
                                "#ffffff",

                            hoverOffset: 8

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    cutout: "65%",

                    plugins: {

                        legend: {

                            position: "bottom",

                            labels: {

                                color: "#475569",

                                usePointStyle: true,

                                pointStyle:
                                    "circle",

                                padding: 15,

                                font: {
                                    size: 11
                                }

                            }

                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    function (context) {

                                    const value =
                                        Number(
                                            context.raw
                                        );

                                    return (
                                        " " +
                                        context.label +
                                        ": ₹" +
                                        value.toLocaleString(
                                            "en-IN",
                                            {
                                                minimumFractionDigits:
                                                    2
                                            }
                                        )
                                    );

                                }

                            }

                        }

                    }

                }

            }
        );

    }


    /* =====================================================
       INCOME VS EXPENSE BAR CHART
       ===================================================== */

    if (incomeExpenseCanvas) {

        new Chart(
            incomeExpenseCanvas,
            {

                type: "bar",

                data: {

                    labels: [

                        "Income",
                        "Expenses"

                    ],

                    datasets: [

                        {

                            label: "Amount",

                            data: [

                                totalIncome,
                                totalExpenses

                            ],

                            backgroundColor: [

                                "#174f91",
                                "#111827"

                            ],

                            borderRadius: 8,

                            borderSkipped: false,

                            maxBarThickness: 65

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    scales: {

                        x: {

                            grid: {
                                display: false
                            },

                            ticks: {

                                color: "#64748b",

                                font: {
                                    size: 11
                                }

                            }

                        },

                        y: {

                            beginAtZero: true,

                            grid: {

                                color: "#edf1f5"

                            },

                            ticks: {

                                color: "#64748b",

                                font: {
                                    size: 10
                                },

                                callback:
                                    function (value) {

                                    return (
                                        "₹" +
                                        Number(
                                            value
                                        ).toLocaleString(
                                            "en-IN"
                                        )
                                    );

                                }

                            }

                        }

                    },

                    plugins: {

                        legend: {
                            display: false
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    function (context) {

                                    return (
                                        " ₹" +
                                        Number(
                                            context.raw
                                        ).toLocaleString(
                                            "en-IN",
                                            {
                                                minimumFractionDigits:
                                                    2
                                            }
                                        )
                                    );

                                }

                            }

                        }

                    }

                }

            }
        );

    }

}