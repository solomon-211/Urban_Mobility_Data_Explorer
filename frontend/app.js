const API_BASE = 'http://localhost:5000/api';

let charts = {};
let map;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    populateHourFilter();
    initMap();
    loadSummaryStats();
    loadHourlyChart();
    loadZonesChart();
    loadBoroughChart();
    
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('resetFilters').addEventListener('click', resetFilters);
});

function populateHourFilter() {
    const select = document.getElementById('hourFilter');
    for (let i = 0; i < 24; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = `${i}:00`;
        select.appendChild(option);
    }
}

function initMap() {
    map = L.map('map').setView([40.7128, -74.0060], 11);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    fetch(`${API_BASE}/geojson`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                console.error('GeoJSON error:', data.error);
                return;
            }
            L.geoJSON(data, {
                style: feature => {
                    const count = feature.properties.trip_count || 0;
                    return {
                        fillColor: getColor(count),
                        weight: 1,
                        opacity: 1,
                        color: 'white',
                        fillOpacity: 0.7
                    };
                },
                onEachFeature: (feature, layer) => {
                    const props = feature.properties;
                    layer.bindTooltip(
                        `<strong>${props.zone || 'Unknown'}</strong><br>` +
                        `Borough: ${props.borough || 'N/A'}<br>` +
                        `Trips: ${(props.trip_count || 0).toLocaleString()}`
                    );
                }
            }).addTo(map);
        })
        .catch(err => console.error('Map error:', err));
}

function getColor(count) {
    return count > 10000 ? '#800026' :
           count > 5000  ? '#BD0026' :
           count > 2000  ? '#E31A1C' :
           count > 1000  ? '#FC4E2A' :
           count > 500   ? '#FD8D3C' :
           count > 200   ? '#FEB24C' :
           count > 100   ? '#FED976' :
                           '#FFEDA0';
}

function loadSummaryStats() {
    fetch(`${API_BASE}/stats/summary`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('totalTrips').textContent = (data.total_trips || 0).toLocaleString();
            document.getElementById('avgFare').textContent = `$${(data.avg_fare || 0).toFixed(2)}`;
            document.getElementById('avgDistance').textContent = `${(data.avg_distance || 0).toFixed(2)} mi`;
            document.getElementById('avgSpeed').textContent = `${(data.avg_speed || 0).toFixed(1)} mph`;
        })
        .catch(err => console.error('Error loading summary:', err));
}

function loadHourlyChart(borough = '', timeOfDay = '', hour = '') {
    // Build query string with filters
    let url = `${API_BASE}/insights/hourly`;
    const params = new URLSearchParams();
    if (borough) params.append('borough', borough);
    if (timeOfDay) params.append('time_of_day', timeOfDay);
    if (hour) params.append('hour', hour);
    if (params.toString()) url += '?' + params.toString();
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const ctx = document.getElementById('hourlyChart').getContext('2d');
            
            if (charts.hourly) charts.hourly.destroy();
            
            charts.hourly = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => `${d.pickup_hour}:00`),
                    datasets: [{
                        label: 'Trip Count',
                        data: data.map(d => d.trip_count),
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
            
            loadFareChart(data);
        })
        .catch(err => console.error('Error loading hourly chart:', err));
}

function loadFareChart(hourlyData) {
    const ctx = document.getElementById('fareChart').getContext('2d');
    
    if (charts.fare) charts.fare.destroy();
    
    charts.fare = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hourlyData.map(d => `${d.pickup_hour}:00`),
            datasets: [{
                label: 'Average Fare ($)',
                data: hourlyData.map(d => d.avg_fare),
                borderColor: 'rgba(234, 179, 8, 1)',
                backgroundColor: 'rgba(234, 179, 8, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

function loadZonesChart(borough = '', timeOfDay = '', hour = '') {
    // Build query string with filters
    let url = `${API_BASE}/insights/top-zones`;
    const params = new URLSearchParams();
    if (borough) params.append('borough', borough);
    if (timeOfDay) params.append('time_of_day', timeOfDay);
    if (hour) params.append('hour', hour);
    if (params.toString()) url += '?' + params.toString();
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const ctx = document.getElementById('zonesChart').getContext('2d');
            
            if (charts.zones) charts.zones.destroy();
            
            charts.zones = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.zone_name || 'Unknown'),
                    datasets: [{
                        label: 'Trip Count',
                        data: data.map(d => d.trip_count || 0),
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: true
                }
            });
        })
        .catch(err => console.error('Error loading top zones:', err));
}

function loadBoroughChart(borough = '', timeOfDay = '', hour = '') {
    // Build query string with filters
    let url = `${API_BASE}/insights/borough-summary`;
    const params = new URLSearchParams();
    if (borough) params.append('borough', borough);
    if (timeOfDay) params.append('time_of_day', timeOfDay);
    if (hour) params.append('hour', hour);
    if (params.toString()) url += '?' + params.toString();
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const ctx = document.getElementById('boroughChart').getContext('2d');
            
            if (charts.borough) charts.borough.destroy();
            
            charts.borough = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.borough || 'Unknown'),
                    datasets: [{
                        label: 'Total Trips',
                        data: data.map(d => d.total_trips || 0),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 206, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(153, 102, 255, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(err => console.error('Error loading borough summary:', err));
}

function applyFilters() {
    const borough = document.getElementById('boroughFilter').value;
    const timeOfDay = document.getElementById('timeFilter').value;
    const hour = document.getElementById('hourFilter').value;
    
    console.log('Filters applied:', { borough, timeOfDay, hour });
    
    // Show loading message
    alert('Filters applied! Charts will reload with filtered data.\n\nNote: With 7.4M trips, filtering may take 10-30 seconds.');
    
    // Reload charts with filters
    loadHourlyChart(borough, timeOfDay, hour);
    loadZonesChart(borough, timeOfDay, hour);
    loadBoroughChart(borough, timeOfDay, hour);
}

function resetFilters() {
    document.getElementById('boroughFilter').value = '';
    document.getElementById('timeFilter').value = '';
    document.getElementById('hourFilter').value = '';
    
    loadHourlyChart();
    loadZonesChart();
    loadBoroughChart();
}
