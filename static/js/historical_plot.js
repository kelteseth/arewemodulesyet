let chartInstance = null;

const CHART_FONT = "'Source Code Pro', monospace";

function isDarkTheme() {
    return document.body.classList.contains('dark');
}

// Read a CSS custom property from the theme so the chart follows the site palette.
function cssVar(name, fallback) {
    const value = getComputedStyle(document.body).getPropertyValue(name).trim();
    return value || fallback;
}

function getThemeColors() {
    const isDark = isDarkTheme();
    return {
        textColor: cssVar('--secondary', isDark ? '#9b9c9d' : '#6c6c6c'),
        legendColor: cssVar('--content', isDark ? '#c4c4c5' : '#1f1f1f'),
        // Grid stays recessive: the theme border in light mode is too faint on dark.
        gridColor: isDark ? cssVar('--tertiary', '#414244') : cssVar('--border', '#eeeeee'),
        surface: cssVar('--entry', isDark ? '#2e2e33' : '#ffffff'),
        border: cssVar('--border', isDark ? '#333333' : '#eeeeee'),
        title: cssVar('--primary', isDark ? '#dadadb' : '#1e1e1e'),
        // Completed projects carry the story; the total is a dashed reference line.
        completed: cssVar('--accent', isDark ? '#3987e5' : '#2a78d6'),
        total: cssVar('--secondary', isDark ? '#9b9c9d' : '#6c6c6c')
    };
}

function applyThemeColors(chart, colors) {
    chart.data.datasets[0].borderColor = colors.completed;
    chart.data.datasets[0].backgroundColor = colors.completed;
    chart.data.datasets[0].pointBorderColor = colors.surface;
    chart.data.datasets[1].borderColor = colors.total;
    chart.data.datasets[1].backgroundColor = colors.total;
    chart.data.datasets[1].pointBorderColor = colors.surface;

    for (const axis of [chart.options.scales.x, chart.options.scales.y]) {
        axis.ticks.color = colors.textColor;
        axis.grid.color = colors.gridColor;
        axis.border.color = colors.gridColor;
    }
    chart.options.scales.y.title.color = colors.textColor;

    chart.options.plugins.legend.labels.color = colors.legendColor;
    chart.options.plugins.tooltip.backgroundColor = colors.surface;
    chart.options.plugins.tooltip.borderColor = colors.border;
    chart.options.plugins.tooltip.titleColor = colors.title;
    chart.options.plugins.tooltip.bodyColor = colors.legendColor;
}

function updateChartTheme() {
    if (!chartInstance) return;
    applyThemeColors(chartInstance, getThemeColors());
    chartInstance.update();
}

function plotHistoricalData() {
    const jsonUrl = '/data/cumulative_stats.json';
    const canvas = document.getElementById('project-cumulative-chart');
    const chartCanvas = canvas.getContext('2d');

    fetch(jsonUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch historical data: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            const completedData = data.map(row => ({
                x: row.commit_date,
                y: row.completed
            }));

            const totalData = data.map(row => ({
                x: row.commit_date,
                y: row.total
            }));

            const colors = getThemeColors();
            const font = { family: CHART_FONT, size: 12 };

            chartInstance = new Chart(chartCanvas, {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Completed projects',
                        data: completedData,
                        borderColor: colors.completed,
                        backgroundColor: colors.completed,
                        borderWidth: 2,
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointHitRadius: 12,
                        pointBorderColor: colors.surface,
                        pointBorderWidth: 2
                    }, {
                        label: 'Total projects',
                        data: totalData,
                        borderColor: colors.total,
                        backgroundColor: colors.total,
                        borderWidth: 2,
                        borderDash: [6, 4],
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointHitRadius: 12,
                        pointBorderColor: colors.surface,
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'month',
                                tooltipFormat: 'd MMM yyyy',
                                displayFormats: { month: 'MMM yyyy' }
                            },
                            ticks: {
                                color: colors.textColor,
                                font: font,
                                maxRotation: 0,
                                autoSkipPadding: 24
                            },
                            grid: {
                                color: colors.gridColor
                            },
                            border: {
                                color: colors.gridColor
                            }
                        },
                        y: {
                            type: 'logarithmic',
                            title: {
                                display: true,
                                text: 'Projects (log scale)',
                                color: colors.textColor,
                                font: font
                            },
                            ticks: {
                                color: colors.textColor,
                                font: font,
                                callback: value => value.toLocaleString()
                            },
                            // Keep only 1/2/5 × 10ⁿ ticks; the default log ticks are noisy.
                            afterBuildTicks: scale => {
                                scale.ticks = scale.ticks.filter(tick => /^[125]0*$/.test(String(tick.value)));
                            },
                            grid: {
                                color: colors.gridColor
                            },
                            border: {
                                color: colors.gridColor
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: false
                        },
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                color: colors.legendColor,
                                font: font,
                                usePointStyle: true,
                                pointStyle: 'line',
                                boxWidth: 28,
                                padding: 16
                            }
                        },
                        tooltip: {
                            backgroundColor: colors.surface,
                            borderColor: colors.border,
                            borderWidth: 1,
                            titleColor: colors.title,
                            bodyColor: colors.legendColor,
                            titleFont: font,
                            bodyFont: font,
                            padding: 10,
                            usePointStyle: true,
                            callbacks: {
                                label: item => ` ${item.dataset.label}: ${item.parsed.y.toLocaleString()}`
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('An error occurred during data fetching or plotting:', error);
            canvas.parentNode.innerHTML =
                `<p class="progress-meta is-centered">Could not load historical data. Error: ${error.message}</p>`;
        });
}
