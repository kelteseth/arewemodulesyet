let chartInstance = null;

function isDarkTheme() {
    return document.body.classList.contains('dark');
}

function getThemeColors() {
    const isDark = isDarkTheme();
    return {
        textColor: isDark ? '#ddd' : '#333',
        gridColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        completedBorder: isDark ? 'rgba(75, 192, 192, 1)' : 'rgba(75, 192, 192, 1)',
        completedBackground: isDark ? 'rgba(75, 192, 192, 0.8)' : 'rgba(75, 192, 192, 0.8)',
        totalBorder: isDark ? 'rgba(255, 99, 132, 1)' : 'rgba(255, 99, 132, 1)',
        totalBackground: isDark ? 'rgba(255, 99, 132, 0.8)' : 'rgba(255, 99, 132, 0.8)'
    };
}

function updateChartTheme() {
    if (!chartInstance) return;
    
    const colors = getThemeColors();
    
    // Update dataset colors
    chartInstance.data.datasets[0].borderColor = colors.completedBorder;
    chartInstance.data.datasets[0].backgroundColor = colors.completedBackground;
    chartInstance.data.datasets[1].borderColor = colors.totalBorder;
    chartInstance.data.datasets[1].backgroundColor = colors.totalBackground;
    
    // Update scales colors
    chartInstance.options.scales.x.ticks.color = colors.textColor;
    chartInstance.options.scales.x.grid.color = colors.gridColor;
    chartInstance.options.scales.y.ticks.color = colors.textColor;
    chartInstance.options.scales.y.grid.color = colors.gridColor;
    chartInstance.options.scales.y.title.color = colors.textColor;
    
    // Update legend colors
    chartInstance.options.plugins.legend.labels.color = colors.textColor;
    
    chartInstance.update();
}

function plotHistoricalData() {
    const jsonUrl = '/data/cumulative_stats.json';
    const chartCanvas = document.getElementById('project-cumulative-chart').getContext('2d');

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

            chartInstance = new Chart(chartCanvas, {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Completed Projects',
                        data: completedData,
                        borderColor: colors.completedBorder,
                        backgroundColor: colors.completedBackground,
                        tension: 0.1,
                        showLine: true,
                        pointRadius: 3
                    }, {
                        label: 'Total Projects',
                        data: totalData,
                        borderColor: colors.totalBorder,
                        backgroundColor: colors.totalBackground,
                        tension: 0.1,
                        showLine: true,
                        pointRadius: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    font: {
                        family: "'Source Code Pro', monospace"
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'month'
                            },
                            title: {
                                display: false,
                                text: 'Change Date'
                            },
                            ticks: {
                                color: colors.textColor,
                                font: {
                                    family: "'Source Code Pro', monospace"
                                }
                            },
                            grid: {
                                color: colors.gridColor
                            }
                        },
                        y: {
                            type: 'logarithmic',
                            title: {
                                display: true,
                                text: 'Number of Projects',
                                color: colors.textColor
                            },
                            ticks: {
                                color: colors.textColor,
                                font: {
                                    family: "'Source Code Pro', monospace"
                                }
                            },
                            grid: {
                                color: colors.gridColor
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: false,
                            text: 'C++ Module Adoption (Completed vs. Total Projects)',
                            font: {
                                family: "'Source Code Pro', monospace"
                            }
                        },
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                color: colors.textColor,
                                font: {
                                    family: "'Source Code Pro', monospace"
                                }
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            bodyFont: {
                                family: "'Source Code Pro', monospace"
                            },
                            titleFont: {
                                family: "'Source Code Pro', monospace"
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('An error occurred during data fetching or plotting:', error);
            document.getElementById('project-cumulative-chart').parentNode.innerHTML =
                `<p style="color: red; padding: 20px;">Could not load historical data. Error: ${error.message}</p>`;
        });
}
