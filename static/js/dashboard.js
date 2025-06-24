// Dashboard JavaScript functionality
class Dashboard {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadNutritionData();
        this.updateMetrics();
    }

    bindEvents() {
        // Refresh data every 5 minutes
        setInterval(() => {
            this.loadNutritionData();
        }, 300000);

        // Handle window resize for chart responsiveness
        window.addEventListener('resize', () => {
            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.resize === 'function') {
                    chart.resize();
                }
            });
        });
    }

    async loadNutritionData() {
        try {
            const response = await fetch('/api/nutrition_summary?days=7');
            if (!response.ok) {
                throw new Error('Failed to load nutrition data');
            }
            
            const data = await response.json();
            this.updateCharts(data);
        } catch (error) {
            console.error('Error loading nutrition data:', error);
            this.showNotification('Error loading nutrition data', 'error');
        }
    }

    updateCharts(data) {
        // Update weekly chart if it exists
        const weeklyChart = this.charts.weekly;
        if (weeklyChart) {
            const dates = Object.keys(data).sort();
            const calories = dates.map(date => data[date].calories);
            const protein = dates.map(date => data[date].protein);
            
            weeklyChart.data.labels = dates.map(date => 
                new Date(date).toLocaleDateString('en-US', { 
                    weekday: 'short', 
                    month: 'short', 
                    day: 'numeric' 
                })
            );
            
            weeklyChart.data.datasets[0].data = calories;
            if (weeklyChart.data.datasets[1]) {
                weeklyChart.data.datasets[1].data = protein;
            }
            
            weeklyChart.update();
        }
    }

    updateMetrics() {
        // Update real-time metrics
        const metrics = document.querySelectorAll('.metric-value');
        metrics.forEach(metric => {
            metric.style.animation = 'none';
            metric.offsetHeight; // Trigger reflow
            metric.style.animation = 'fadeIn 0.5s ease-in';
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px;';
        
        notification.innerHTML = `
            <strong>${type === 'error' ? 'Error!' : 'Info:'}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    async logQuickFood(foodName, calories, protein = 0, carbs = 0, fat = 0) {
        try {
            const response = await fetch('/api/log_food', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    food_name: foodName,
                    servings: 1,
                    calories: calories,
                    protein: protein,
                    carbs: carbs,
                    fat: fat,
                    meal_type: this.getCurrentMealType()
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`${foodName} logged successfully!`, 'success');
                // Refresh the page to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error(result.error || 'Failed to log food');
            }
        } catch (error) {
            console.error('Error logging food:', error);
            this.showNotification('Error logging food: ' + error.message, 'error');
        }
    }

    getCurrentMealType() {
        const hour = new Date().getHours();
        if (hour < 11) return 'breakfast';
        if (hour < 15) return 'lunch';
        if (hour < 19) return 'dinner';
        return 'snack';
    }

    // Progress calculation utilities
    calculateProgress(current, goal) {
        if (!goal || goal === 0) return 0;
        return Math.min(100, (current / goal) * 100);
    }

    updateProgressBar(elementId, current, goal) {
        const progressBar = document.querySelector(`#${elementId} .progress-bar`);
        if (progressBar) {
            const progress = this.calculateProgress(current, goal);
            progressBar.style.width = `${progress}%`;
            
            // Update color based on progress
            progressBar.className = 'progress-bar';
            if (progress < 50) {
                progressBar.classList.add('bg-danger');
            } else if (progress < 80) {
                progressBar.classList.add('bg-warning');
            } else {
                progressBar.classList.add('bg-success');
            }
        }
    }

    // Chart creation helpers
    createLineChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        };

        const chart = new Chart(ctx, {
            type: 'line',
            data: data,
            options: { ...defaultOptions, ...options }
        });

        this.charts[canvasId] = chart;
        return chart;
    }

    createDoughnutChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        };

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: { ...defaultOptions, ...options }
        });

        this.charts[canvasId] = chart;
        return chart;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new Dashboard();
});

// Utility functions
function formatNumber(num, decimals = 1) {
    return parseFloat(num).toFixed(decimals);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
    });
}

function getMealTypeIcon(mealType) {
    const icons = {
        breakfast: '🌅',
        lunch: '☀️',
        dinner: '🌙',
        snack: '🍎'
    };
    return icons[mealType] || '🍽️';
}

// Export for use in other scripts
window.DashboardUtils = {
    formatNumber,
    formatDate,
    getMealTypeIcon
};
