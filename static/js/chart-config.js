// 🔁 Track chart instances so we can destroy old ones
let chartInstances = {};

function renderCharts(data) {
    // 🧹 Clear old summaries before rendering new ones
    ['aovSummary', 'productsSummary', 'campaignSummary', 'categoriesSummary'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });

    renderAOVChart(data.aovData);
    renderTopProductsChart(data.topProducts);
    renderCampaignImpactChart(data.campaignImpact);
    renderTopCategoriesChart(data.topCategories);
}

// 🔹 Average Order Value Chart (Bar)
function renderAOVChart(aovData) {
    const ctx = document.getElementById('aovChart').getContext('2d');

    if (chartInstances.aovChart) {
        chartInstances.aovChart.destroy();
    }

    chartInstances.aovChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: aovData.map(item => item.CustomerID),
            datasets: [{
                label: 'Avg Order Value',
                data: aovData.map(item => item.AvgOrderValue),
                backgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    const summaryDiv = document.getElementById('aovSummary');
    if (aovData.length > 0) {
        const topCustomer = aovData[0];
        summaryDiv.innerHTML = `
            <p><strong>Top Customer:</strong> ${topCustomer.CustomerID}</p>
            <p><strong>Avg Order Value:</strong> ₹${topCustomer.AvgOrderValue.toLocaleString()}</p>
        `;
    }
}

// 🔹 Top Products Chart (Bar)
function renderTopProductsChart(products) {
    const ctx = document.getElementById('productsChart').getContext('2d');

    if (chartInstances.productsChart) {
        chartInstances.productsChart.destroy();
    }

    chartInstances.productsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: products.map(p => p.product),
            datasets: [{
                label: 'Units Sold',
                data: products.map(p => p.totalSold),
                backgroundColor: ['#60a5fa', '#2563eb', '#1e3a8a', '#93c5fd', '#1d4ed8']
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'top' } },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    const productSummary = document.getElementById('productsSummary');
    if (products.length > 0) {
        const best = products[0];
        productSummary.innerHTML = `
            <p><strong>Best Selling:</strong> ${best.product}</p>
            <p><strong>Units Sold:</strong> ${best.totalSold}</p>
        `;
    }
}

// 🔹 Campaign Impact Chart (Line)
function renderCampaignImpactChart(campaigns) {
    const ctx = document.getElementById('campaignChart').getContext('2d');

    if (chartInstances.campaignChart) {
        chartInstances.campaignChart.destroy();
    }

    chartInstances.campaignChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: campaigns.map(c => c.campaignId),
            datasets: [{
                label: 'Campaign Revenue',
                data: campaigns.map(c => c.totalRevenue),
                fill: false,
                borderColor: '#1d4ed8',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'top' } },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    const campaignSummary = document.getElementById('campaignSummary');
    if (campaigns.length > 0) {
        const best = campaigns.reduce((a, b) => a.totalRevenue > b.totalRevenue ? a : b);
        campaignSummary.innerHTML = `
            <p><strong>Top Campaign:</strong> ${best.campaignId}</p>
            <p><strong>Total Revenue:</strong> ₹${best.totalRevenue.toLocaleString()}</p>
        `;
    }
}

// 🔹 Top Categories Chart (Pie)
function renderTopCategoriesChart(categories) {
    const ctx = document.getElementById('categoriesChart').getContext('2d');

    if (chartInstances.categoriesChart) {
        chartInstances.categoriesChart.destroy();
    }

    chartInstances.categoriesChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                label: 'Category Share',
                data: categories.map(c => c.count),
                backgroundColor: ['#4ade80', '#facc15', '#f472b6', '#60a5fa', '#a78bfa']
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } }
        }
    });

    const categorySummary = document.getElementById('categoriesSummary');
    if (categories.length > 0) {
        const best = categories[0];
        categorySummary.innerHTML = `
            <p><strong>Most Popular Category:</strong> ${best.category}</p>
            <p><strong>Total Products:</strong> ${best.count}</p>
        `;
    }
}

// 🔹 Recommendations Display
function renderInsights(recommendations) {
    const container = document.getElementById('recommendations');
    container.innerHTML = '';

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p>No recommendations available.</p>';
        return;
    }

    recommendations.forEach(rec => {
        const div = document.createElement('div');
        div.classList.add('recommendation-box');
        div.innerHTML = `
            <h4>${rec.type.toUpperCase()} (${rec.priority.toUpperCase()})</h4>
            <p>${rec.message}</p>
        `;
        container.appendChild(div);
    });
}
