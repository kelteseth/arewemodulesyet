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

            new Chart(chartCanvas, {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Completed Projects',
                        data: completedData,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.8)',
                        tension: 0.1,
                        showLine: true,
                        pointRadius: 3
                    }, {
                        label: 'Total Projects',
                        data: totalData,
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.8)',
                        tension: 0.1,
                        showLine: true,
                        pointRadius: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'month'
                            },
                            title: {
                                display: true,
                                text: 'Commit Date'
                            }
                        },
                        y: {
                            type: 'logarithmic',
                            title: {
                                display: true,
                                text: 'Number of Projects'
                            },
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'C++ Module Adoption (Completed vs. Total Projects)'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
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
