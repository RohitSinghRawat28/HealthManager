// Upload page JavaScript functionality
class FoodUploader {
    constructor() {
        this.currentFile = null;
        this.isAnalyzing = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupDragAndDrop();
    }

    bindEvents() {
        const imageInput = document.getElementById('image-input');
        const analyzeBtn = document.getElementById('analyze-btn');
        const uploadArea = document.getElementById('upload-area');

        // File input change
        imageInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // Analyze button click
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                this.analyzeImage();
            });
        }

        // Upload area click
        uploadArea.addEventListener('click', () => {
            imageInput.click();
        });
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('upload-area');

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });

        // Handle dropped files
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            this.showError('Please select a valid image file.');
            return;
        }

        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('Image file is too large. Please select a file smaller than 10MB.');
            return;
        }

        this.currentFile = file;
        this.displayImagePreview(file);
    }

    displayImagePreview(file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const previewImg = document.getElementById('preview-img');
            const imagePreview = document.getElementById('image-preview');
            const uploadArea = document.getElementById('upload-area');

            previewImg.src = e.target.result;
            imagePreview.style.display = 'block';
            uploadArea.style.display = 'none';
        };

        reader.readAsDataURL(file);
    }

    async analyzeImage() {
        if (!this.currentFile || this.isAnalyzing) return;

        this.isAnalyzing = true;
        this.showLoading(true);
        this.hideResults();

        try {
            const formData = new FormData();
            formData.append('image', this.currentFile);

            const response = await fetch('/api/classify_food', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.displayResults(result);
            } else {
                throw new Error(result.error || 'Failed to analyze image');
            }

        } catch (error) {
            console.error('Error analyzing image:', error);
            this.showError('Failed to analyze image: ' + error.message);
        } finally {
            this.isAnalyzing = false;
            this.showLoading(false);
        }
    }

    displayResults(result) {
        const resultsSection = document.getElementById('results-section');
        const predictionResults = document.getElementById('prediction-results');
        const recipeList = document.getElementById('recipe-list');

        // Display prediction results - handle both single prediction and multiple predictions
        if (result.predictions && result.predictions.length > 0) {
            predictionResults.innerHTML = result.predictions.map((pred, index) => 
                this.createPredictionHTML(pred, index === 0)
            ).join('');
        } else if (result.prediction) {
            predictionResults.innerHTML = this.createPredictionHTML(result.prediction, true);
        } else if (result.top_prediction) {
            predictionResults.innerHTML = this.createPredictionHTML(result.top_prediction, true);
        }

        // Display recipe suggestions
        if (result.recipes && result.recipes.length > 0) {
            const recipesHTML = result.recipes.map(recipe => 
                this.createRecipeCardHTML(recipe)
            ).join('');
            recipeList.innerHTML = recipesHTML;
        } else {
            recipeList.innerHTML = '<div class="col-12"><div class="alert alert-info">No specific recipes found, but try searching our recipe database for similar dishes!</div></div>';
        }

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    createPredictionHTML(prediction, isPrimary = true) {
        const confidence = (prediction.confidence * 100).toFixed(1);
        const categoryName = prediction.category ? prediction.category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
                           (prediction.category_name || 'Unknown Food');
        
        const cardClass = isPrimary ? 'border-success' : 'border-info';
        const textClass = isPrimary ? 'text-success' : 'text-info';
        const progressClass = isPrimary ? 'bg-success' : 'bg-info';
        const title = isPrimary ? 'Best Match' : 'Alternative Match';
        
        return `
            <div class="col-md-6 mb-3">
                <div class="card ${cardClass}">
                    <div class="card-body text-center">
                        <h5 class="card-title ${textClass}">
                            <i data-feather="target"></i>
                            ${title}
                        </h5>
                        <h4 class="${textClass}">${categoryName}</h4>
                        <div class="progress mb-2" style="height: 10px;">
                            <div class="progress-bar ${progressClass}" style="width: ${confidence}%"></div>
                        </div>
                        <small class="text-muted">${confidence}% confidence</small>
                    </div>
                </div>
            </div>
                            </div>
                            <p class="mb-0">Confidence: ${confidence}%</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i data-feather="list"></i>
                                Top Predictions
                            </h6>
                            ${prediction.top_predictions.map((pred, index) => `
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span class="badge bg-secondary">${index + 1}</span>
                                    <span class="flex-grow-1 ms-2">${pred.category_name}</span>
                                    <span class="text-muted">${(pred.confidence * 100).toFixed(0)}%</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createRecipeCardHTML(recipe) {
        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card h-100 recipe-card">
                    <div class="card-body">
                        <h6 class="card-title">${recipe.name}</h6>
                        <div class="row text-center mb-2">
                            <div class="col-4">
                                <small class="text-muted">Prep</small><br>
                                <strong>${recipe.prep_time || 0}m</strong>
                            </div>
                            <div class="col-4">
                                <small class="text-muted">Cook</small><br>
                                <strong>${recipe.cook_time || 0}m</strong>
                            </div>
                            <div class="col-4">
                                <small class="text-muted">Cal</small><br>
                                <strong>${recipe.calories_per_serving || 0}</strong>
                            </div>
                        </div>
                        <div class="d-grid gap-2">
                            <a href="/recipe/${recipe.id}" class="btn btn-outline-primary btn-sm">
                                <i data-feather="eye"></i>
                                View Recipe
                            </a>
                            <button class="btn btn-success btn-sm" onclick="quickLogRecipe(${recipe.id}, '${recipe.name}', ${recipe.calories_per_serving || 0})">
                                <i data-feather="plus"></i>
                                Quick Log
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        const analyzeBtn = document.getElementById('analyze-btn');
        
        if (show) {
            loading.style.display = 'block';
            if (analyzeBtn) {
                analyzeBtn.disabled = true;
                analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';
            }
        } else {
            loading.style.display = 'none';
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i data-feather="zap"></i> Analyze Food';
                feather.replace(); // Re-render feather icons
            }
        }
    }

    hideResults() {
        const resultsSection = document.getElementById('results-section');
        resultsSection.style.display = 'none';
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            <strong>Error!</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alert, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    clearImage() {
        this.currentFile = null;
        this.isAnalyzing = false;
        
        const imagePreview = document.getElementById('image-preview');
        const uploadArea = document.getElementById('upload-area');
        const imageInput = document.getElementById('image-input');
        
        imagePreview.style.display = 'none';
        uploadArea.style.display = 'block';
        imageInput.value = '';
        
        this.hideResults();
        this.showLoading(false);
    }
}

// Global functions for template usage
function clearImage() {
    if (window.foodUploader) {
        window.foodUploader.clearImage();
    }
}

async function quickLogRecipe(recipeId, recipeName, calories) {
    try {
        const response = await fetch('/api/log_food', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                recipe_id: recipeId,
                food_name: recipeName,
                servings: 1,
                calories: calories,
                protein: 0,
                carbs: 0,
                fat: 0,
                meal_type: getCurrentMealType()
            })
        });

        const result = await response.json();
        
        if (result.success) {
            showSuccess(`${recipeName} logged successfully!`);
        } else {
            throw new Error(result.error || 'Failed to log food');
        }
    } catch (error) {
        console.error('Error logging food:', error);
        showError('Error logging food: ' + error.message);
    }
}

function getCurrentMealType() {
    const hour = new Date().getHours();
    if (hour < 11) return 'breakfast';
    if (hour < 15) return 'lunch';
    if (hour < 19) return 'dinner';
    return 'snack';
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px;';
    alert.innerHTML = `
        <strong>Success!</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 3000);
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px;';
    alert.innerHTML = `
        <strong>Error!</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// Initialize uploader
function initializeUpload() {
    window.foodUploader = new FoodUploader();
}

// Auto-initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUpload);
} else {
    initializeUpload();
}
