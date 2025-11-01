// Perfume Visual Generator - Frontend JavaScript

class PerfumeGenerator {
    constructor() {
        this.form = document.getElementById('generateForm');
        this.generateBtn = document.getElementById('generateBtn');
        this.previewArea = document.getElementById('previewArea');
        this.processingSteps = document.getElementById('processingSteps');
        this.imageInfo = document.getElementById('imageInfo');
        this.errorToast = document.getElementById('errorToast');
        
        // Randewoo products
        this.productsTable = document.getElementById('productsTable');
        this.productsTableBody = document.getElementById('productsTableBody');
        this.selectPerfumeBtn = document.getElementById('selectPerfumeBtn');
        this.selectedProductInfo = document.getElementById('selectedProductInfo');
        this.selectedProductText = document.getElementById('selectedProductText');
        
        // Telegram
        this.telegramSection = document.getElementById('telegramSection');
        this.publishTelegramBtn = document.getElementById('publishTelegramBtn');
        
        this.currentGeneration = null;
        this.products = [];
        this.selectedProduct = null;
        this.globalPrompts = null;  // Store global prompts from database
        
        this.init();
    }
    
    init() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleGenerate();
        });
        
        // Character counter
        const description = document.getElementById('description');
        const charCount = document.getElementById('charCount');
        description.addEventListener('input', () => {
            const count = description.value.length;
            charCount.textContent = count;
            if (count > 2000) {
                charCount.style.color = 'var(--error)';
            } else {
                charCount.style.color = 'var(--text-tertiary)';
            }
        });
        
        // Example URL buttons
        document.querySelectorAll('.example-url-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('brand').value = btn.dataset.brand || '';
                document.getElementById('perfume_name').value = btn.dataset.perfume || '';
                document.getElementById('description').value = btn.dataset.desc || '';
                document.getElementById('image_url').value = btn.dataset.url || '';
                
                // Update char counter
                charCount.textContent = (btn.dataset.desc || '').length;
                
                // Visual feedback
                btn.style.background = 'var(--success)';
                btn.style.color = 'white';
                btn.textContent = '✓ Loaded!';
                setTimeout(() => {
                    btn.style.background = '';
                    btn.style.color = '';
                    btn.textContent = btn.getAttribute('data-original-text') || 'Load Example';
                }, 2000);
            });
            // Store original text
            btn.setAttribute('data-original-text', btn.textContent);
        });
        
        // Auto-Find Image button
        document.getElementById('autoFindBtn').addEventListener('click', () => {
            this.handleAutoFind();
        });
        
        // Save Main button
        document.getElementById('saveMainBtn').addEventListener('click', () => {
            this.handleSaveMain();
        });
        
        // Download button
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadImage();
        });
        
        // Generate Video button
        document.getElementById('generateVideoBtn').addEventListener('click', () => {
            this.handleGenerateVideo();
        });
        
        // Download Video button
        document.getElementById('downloadVideoBtn').addEventListener('click', () => {
            this.downloadVideo();
        });
        
        // Toggle AI Prompts section
        document.getElementById('togglePromptsBtn').addEventListener('click', () => {
            this.togglePrompts();
        });
        
        // Randewoo products
        document.getElementById('refreshProductsBtn').addEventListener('click', () => {
            this.loadProducts();
        });
        
        this.selectPerfumeBtn.addEventListener('click', () => {
            this.handleSelectPerfume();
        });
        
        // Telegram
        document.getElementById('showTelegramBtn').addEventListener('click', () => {
            this.showTelegramSection();
        });
        
        document.getElementById('closeTelegramBtn').addEventListener('click', () => {
            this.telegramSection.style.display = 'none';
        });
        
        document.getElementById('recreateTgBtn').addEventListener('click', () => {
            this.handleRecreateTgCaption();
        });
        
        // Sync caption textarea with preview
        document.getElementById('tgCaption').addEventListener('input', (e) => {
            document.getElementById('telegramPreviewCaption').textContent = e.target.value;
        });
        
        this.publishTelegramBtn.addEventListener('click', () => {
            this.handlePublishToTelegram();
        });
        
        // Save Prompts button
        document.getElementById('savePromptsBtn').addEventListener('click', () => {
            this.handleSavePrompts();
        });
        
        // Load test endpoint, prompts, and products
        this.testConnection();
        this.loadGlobalPrompts();
        this.loadProducts();
    }
    
    togglePrompts() {
        const content = document.getElementById('promptsContent');
        const toggleBtn = document.getElementById('togglePromptsBtn');
        const toggleText = toggleBtn.querySelector('.toggle-text');
        const toggleIcon = toggleBtn.querySelector('.toggle-icon');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            toggleText.textContent = 'Hide Prompts';
            toggleIcon.classList.add('rotated');
        } else {
            content.style.display = 'none';
            toggleText.textContent = 'Show Prompts';
            toggleIcon.classList.remove('rotated');
        }
    }
    
    async testConnection() {
        try {
            const response = await fetch('/api/test');
            const data = await response.json();
            console.log('Server status:', data);
        } catch (error) {
            console.error('Server connection error:', error);
        }
    }
    
    async loadGlobalPrompts() {
        try {
            console.log('[PROMPTS] Loading global prompts from database...');
            
            const response = await fetch('/api/settings/prompts');
            const data = await response.json();
            
            if (data.success) {
                this.globalPrompts = data.prompts;
                
                // Update textareas with values from database
                if (this.globalPrompts.stylize) {
                    document.getElementById('prompt_stylize').value = this.globalPrompts.stylize;
                    console.log('[PROMPTS] Loaded stylize prompt:', this.globalPrompts.stylize.length, 'chars');
                }
                
                if (this.globalPrompts.caption) {
                    document.getElementById('prompt_caption_global').value = this.globalPrompts.caption;
                    console.log('[PROMPTS] Loaded caption prompt:', this.globalPrompts.caption.length, 'chars');
                }
                
                console.log('[PROMPTS] ✓ Global prompts loaded from database');
            } else {
                console.error('[PROMPTS] Failed to load:', data.error);
            }
            
        } catch (error) {
            console.error('[PROMPTS ERROR] Failed to load global prompts:', error);
        }
    }
    
    async handleSavePrompts() {
        const saveBtn = document.getElementById('savePromptsBtn');
        const btnText = saveBtn.querySelector('.btn-text');
        const btnLoader = saveBtn.querySelector('.btn-loader');
        const statusSpan = document.getElementById('promptsSaveStatus');
        
        // Get values from textareas
        const promptStylize = document.getElementById('prompt_stylize').value.trim();
        const promptCaption = document.getElementById('prompt_caption_global').value.trim();
        
        if (!promptStylize || !promptCaption) {
            this.showError('Both prompts are required');
            return;
        }
        
        // Set loading state
        saveBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        statusSpan.style.display = 'none';
        
        try {
            console.log('[PROMPTS] Saving to database...');
            
            const response = await fetch('/api/settings/prompts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt_stylize: promptStylize,
                    prompt_caption: promptCaption
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('[PROMPTS] ✓ Saved successfully');
                
                // Update cached prompts
                this.globalPrompts = {
                    stylize: promptStylize,
                    caption: promptCaption
                };
                
                // Show success status
                statusSpan.textContent = '✓ Settings saved!';
                statusSpan.style.display = 'inline';
                statusSpan.style.color = 'var(--success)';
                
                this.showSuccess('💾 Prompts saved to database!');
                
                // Hide status after 3 seconds
                setTimeout(() => {
                    statusSpan.style.display = 'none';
                }, 3000);
                
            } else {
                throw new Error(result.error || 'Failed to save prompts');
            }
            
        } catch (error) {
            console.error('[PROMPTS ERROR]', error);
            this.showError('Failed to save prompts: ' + error.message);
            
            statusSpan.textContent = '❌ Save failed';
            statusSpan.style.display = 'inline';
            statusSpan.style.color = 'var(--error)';
            
        } finally {
            // Reset button
            saveBtn.disabled = false;
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    }
    
    async handleGenerate() {
        const formData = new FormData(this.form);
        const data = {
            brand: formData.get('brand').trim(),
            perfume_name: formData.get('perfume_name').trim(),
            description: formData.get('description').trim(),
            image_url: formData.get('image_url').trim(),
            prompt_background: (formData.get('prompt_background') || '').trim(),
            prompt_stylize: (formData.get('prompt_stylize') || '').trim()
        };
        
        // Use main image from database if available
        if (this.selectedProduct && this.selectedProduct.image_path) {
            data.image_path = this.selectedProduct.image_path;
            console.log('[GENERATE] Using main image from database:', data.image_path);
        }
        
        // Add product_id if product is selected
        if (this.selectedProduct && this.selectedProduct.id) {
            data.product_id = this.selectedProduct.id;
            console.log('[GENERATE] Product ID:', data.product_id);
        }
        
        // Validation
        if (!data.brand || !data.perfume_name || !data.description) {
            this.showError('Please fill in all required fields');
            return;
        }
        
        // Check if we have either image_url or image_path
        if (!data.image_url && !data.image_path) {
            this.showError('Please provide an image: use Auto-Find, enter Image URL, or Save as main');
            return;
        }
        
        if (data.description.length > 2000) {
            this.showError('Description is too long (max 2000 characters)');
            return;
        }
        
        // Start generation
        this.setLoading(true);
        this.showProcessingSteps();
        
        try {
            // Step 1: Submit to backend
            this.updateStep(1, 'active', 'Starting...');
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Generation failed');
            }
            
            const result = await response.json();
            this.currentGeneration = result.data;
            
            console.log('Generation started:', result);
            console.log('API returned image_url:', result.data.image_url);
            console.log('API returned final_filename:', result.data.final_filename);
            
            // Update selected product with new styled image path
            if (this.selectedProduct && result.data.final_filename) {
                this.selectedProduct.styled_image_path = result.data.final_filename;
                console.log('[DB] Updated selectedProduct.styled_image_path:', result.data.final_filename);
            }
            
            // Update steps
            this.updateStep(1, 'completed', 'Complete');
            
            if (result.data.requires_manual_processing) {
                // Show manual processing instructions
                this.showManualProcessingInstructions(data);
            } else {
                // Automated processing - pass API response data, not form data!
                await this.processImage(result.data);
            }
            
        } catch (error) {
            console.error('Generation error:', error);
            this.showError(error.message);
            this.setLoading(false);
            this.hideProcessingSteps();
        }
    }
    
    showManualProcessingInstructions(data) {
        this.updateStep(1, 'completed', 'Image downloaded');
        this.updateStep(2, 'active', 'Processing...');
        
        // Show instructions in preview area
        this.previewArea.innerHTML = `
            <div class="manual-processing-instructions">
                <h3>🎨 Manual Processing Required</h3>
                <p>Please run the following commands to complete the image generation:</p>
                
                <div class="code-block">
                    <h4>Step 1: Remove Background</h4>
                    <pre>python process_image.py remove-bg "${data.brand}" "${data.perfume_name}" "${data.image_url}"</pre>
                </div>
                
                <div class="code-block">
                    <h4>Step 2: Add Styled Background</h4>
                    <pre>python process_image.py stylize "${data.brand}" "${data.perfume_name}" "${data.description.substring(0, 100)}..."</pre>
                </div>
                
                <p class="instructions-note">
                    The image will automatically appear here once processing is complete.
                </p>
                
                <button class="btn-retry" onclick="location.reload()">Start New Generation</button>
            </div>
        `;
        
        this.setLoading(false);
    }
    
    async processImage(data) {
        try {
            // Step 2: Remove background
            this.updateStep(2, 'active', 'Removing background...');
            
            // Simulate API call
            await this.sleep(2000);
            
            this.updateStep(2, 'completed', 'Background removed');
            
            // Step 3: Stylize
            this.updateStep(3, 'active', 'Adding styled background...');
            
            await this.sleep(3000);
            
            this.updateStep(3, 'completed', 'Stylization complete');
            
            // Show final result
            this.showFinalImage(data);
            
        } catch (error) {
            throw error;
        }
    }
    
    showFinalImage(data) {
        // Use image_url from API response (server knows the correct filename)
        const imagePath = data.image_url || `/images/${data.final_filename || 'unknown.png'}`;
        
        console.log('[Frontend] Loading image:', imagePath);
        
        this.previewArea.innerHTML = `
            <img src="${imagePath}" alt="${data.brand} ${data.perfume_name}" class="preview-image" 
                 onerror="console.error('Failed to load image:', '${imagePath}'); this.style.border='2px solid red';" />
        `;
        
        // Show image info
        this.imageInfo.style.display = 'block';
        document.getElementById('infoBrand').textContent = data.brand;
        document.getElementById('infoPerfume').textContent = data.perfume_name;
        document.getElementById('infoTime').textContent = new Date().toLocaleString();
        document.getElementById('downloadBtn').style.display = 'block';
        
        // Show Generate Video button
        document.getElementById('generateVideoBtn').style.display = 'block';
        
        // Hide processing steps
        setTimeout(() => {
            this.hideProcessingSteps();
        }, 1000);
        
        this.setLoading(false);
    }
    
    downloadImage() {
        if (!this.currentGeneration) return;
        
        // Use correct filename from API response
        const imagePath = this.currentGeneration.image_url || `/images/${this.currentGeneration.final_filename}`;
        
        const link = document.createElement('a');
        link.href = imagePath;
        link.download = `${this.currentGeneration.brand}_${this.currentGeneration.perfume_name}_styled.png`;
        link.click();
    }
    
    async handleGenerateVideo() {
        if (!this.currentGeneration) {
            this.showError('No image available. Generate an image first.');
            return;
        }
        
        // Get description from form
        const description = document.getElementById('description').value.trim();
        
        if (!description) {
            this.showError('Please enter fragrance description first.');
            return;
        }
        
        const generateVideoBtn = document.getElementById('generateVideoBtn');
        const btnText = generateVideoBtn.querySelector('.btn-text');
        const btnLoader = generateVideoBtn.querySelector('.btn-loader');
        
        // Set loading state
        generateVideoBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
        btnText.textContent = '⏳ Generating with Claude + Seedance...';
        
        try {
            console.log('Starting video generation with Claude + Seedance-1-pro...');
            
            const payload = {
                image_filename: this.currentGeneration.final_filename,
                brand: this.currentGeneration.brand,
                perfume_name: this.currentGeneration.perfume_name,
                description: description
            };
            
            // Add product_id if product is selected
            if (this.selectedProduct && this.selectedProduct.id) {
                payload.product_id = this.selectedProduct.id;
                console.log('[VIDEO] Product ID:', payload.product_id);
            }
            
            const response = await fetch('/api/generate-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Video generation failed');
            }
            
            const result = await response.json();
            
            console.log('Video generated:', result);
            
            // Update selected product with new video path
            if (this.selectedProduct && result.data.video_filename) {
                this.selectedProduct.video_path = result.data.video_filename;
                console.log('[DB] Updated selectedProduct.video_path:', result.data.video_filename);
            }
            
            // Show video preview with concept and prompt
            this.showVideoPreview(result.data);
            
            // Reset button
            btnText.textContent = '🎬 Generate Video';
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            generateVideoBtn.disabled = false;
            
            // Show success message
            this.showSuccess('Video generated with Claude + Seedance-1-pro!');
            
        } catch (error) {
            console.error('Video generation error:', error);
            
            // More informative error messages
            let errorMsg = error.message;
            
            if (errorMsg.includes('502') || errorMsg.includes('Bad Gateway')) {
                errorMsg = '⚠️ Replicate API temporarily unavailable (502 Gateway Error). Please try again in a few minutes.';
            } else if (errorMsg.includes('503')) {
                errorMsg = '⚠️ Replicate API is overloaded (503). Please try again in a few minutes.';
            } else if (errorMsg.includes('timeout')) {
                errorMsg = '⏱️ Request timeout. Replicate may be slow. Try again later.';
            } else if (errorMsg.includes('Replicate API may be temporarily unavailable')) {
                errorMsg = '⚠️ Replicate API is temporarily unavailable. Please try again in 5-10 minutes. Check status: https://status.replicate.com';
            }
            
            this.showError(errorMsg);
            
            // Reset button
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            generateVideoBtn.disabled = false;
        }
    }
    
    showVideoPreview(data) {
        const videoPreview = document.getElementById('videoPreview');
        const videoPlayer = document.getElementById('videoPlayer');
        
        // Set video source
        videoPlayer.src = data.video_url;
        
        // Store video data for download
        this.currentVideoData = data;
        
        // Show concept and prompt if available
        if (data.concept || data.prompt) {
            const conceptDiv = document.getElementById('videoConcept');
            const promptDiv = document.getElementById('videoPrompt');
            
            if (conceptDiv && data.concept) {
                conceptDiv.textContent = data.concept;
                conceptDiv.parentElement.style.display = 'block';
            }
            
            if (promptDiv && data.prompt) {
                promptDiv.textContent = data.prompt;
                promptDiv.parentElement.style.display = 'block';
            }
        }
        
        // Show nobg image info if available
        if (data.nobg_image) {
            console.log('Used nobg image:', data.nobg_image);
        }
        
        // Show video preview
        videoPreview.style.display = 'block';
        
        // Scroll to video
        videoPreview.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    downloadVideo() {
        if (!this.currentVideoData) return;
        
        const link = document.createElement('a');
        link.href = this.currentVideoData.video_url;
        link.download = `${this.currentVideoData.brand}_${this.currentVideoData.perfume_name}_video.mp4`;
        link.click();
    }
    
    showProcessingSteps() {
        this.processingSteps.style.display = 'flex';
        this.imageInfo.style.display = 'none';
        
        // Reset all steps
        const steps = this.processingSteps.querySelectorAll('.step');
        steps.forEach(step => {
            step.classList.remove('active', 'completed');
            const status = step.querySelector('.step-status');
            status.textContent = 'Pending...';
        });
    }
    
    hideProcessingSteps() {
        this.processingSteps.style.display = 'none';
    }
    
    updateStep(stepNumber, state, statusText) {
        const step = this.processingSteps.querySelector(`[data-step="${stepNumber}"]`);
        if (!step) return;
        
        step.classList.remove('active', 'completed');
        if (state) {
            step.classList.add(state);
        }
        
        const status = step.querySelector('.step-status');
        status.textContent = statusText;
    }
    
    setLoading(isLoading) {
        this.generateBtn.disabled = isLoading;
        const btnText = this.generateBtn.querySelector('.btn-text');
        const btnLoader = this.generateBtn.querySelector('.btn-loader');
        
        if (isLoading) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'flex';
        } else {
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    }
    
    showError(message) {
        const toastMessage = this.errorToast.querySelector('.toast-message');
        toastMessage.textContent = message;
        
        this.errorToast.style.display = 'block';
        
        setTimeout(() => {
            this.errorToast.style.display = 'none';
        }, 5000);
    }
    
    async handleAutoFind() {
        const brand = document.getElementById('brand').value.trim();
        const perfumeName = document.getElementById('perfume_name').value.trim();
        
        // Validation
        if (!brand || !perfumeName) {
            this.showError('Please enter Brand Name and Perfume Name first');
            return;
        }
        
        const autoFindBtn = document.getElementById('autoFindBtn');
        const btnText = autoFindBtn.querySelector('.btn-auto-text');
        const btnLoader = autoFindBtn.querySelector('.btn-auto-loader');
        
        // Set loading state
        autoFindBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
        
        try {
            console.log(`Searching for image: ${brand} ${perfumeName}`);
            
            // Check if we have a selected Randewoo product
            const requestBody = {
                brand: brand,
                perfume_name: perfumeName
            };
            
            // Add product_url if available (for Randewoo image extraction)
            if (this.selectedProduct && this.selectedProduct.product_url) {
                requestBody.product_url = this.selectedProduct.product_url;
                console.log(`[AUTO-FIND] Will try Randewoo first: ${this.selectedProduct.product_url}`);
            }
            
            const response = await fetch('/api/search-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            // Check if response is ok
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error:', response.status, errorText);
                throw new Error(`API returned error ${response.status}`);
            }
            
            // Parse JSON
            let result;
            try {
                result = await response.json();
            } catch (parseError) {
                console.error('Failed to parse JSON:', parseError);
                throw new Error('Invalid response from server');
            }
            
            console.log('API Response:', result);
            
            // Check if result exists and has success field
            if (!result) {
                throw new Error('Empty response from server');
            }
            
            if (result.success === true) {
                // Set found image URL
                document.getElementById('image_url').value = result.image_url;
                
                // Show success feedback
                btnText.textContent = '✓ Found!';
                btnText.style.display = 'inline';
                btnLoader.style.display = 'none';
                autoFindBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
                
                // Show toast with info including source
                const source = result.source === 'randewoo' ? '📦 Randewoo' : '🔍 Google';
                const title = result.title || 'Perfume bottle';
                this.showSuccess(`Found image from ${source}: ${title}`);
                
                // Reset button after delay
                setTimeout(() => {
                    btnText.textContent = '🔍 Auto-Find';
                    autoFindBtn.disabled = false;
                }, 3000);
            } else {
                // API returned error
                const errorMsg = result.message || result.error || 'Image search failed';
                console.error('Search failed:', errorMsg);
                throw new Error(errorMsg);
            }
            
        } catch (error) {
            console.error('Auto-find error:', error);
            
            // Show user-friendly error message
            let errorMessage = 'Failed to find image automatically';
            
            if (error.message.includes('API not configured')) {
                errorMessage = 'OpenAI API not configured. Please add OPENAI_API_KEY to .env file';
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            this.showError(errorMessage);
            
            // Reset button
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            autoFindBtn.disabled = false;
        }
    }
    
    showSuccess(message) {
        // Create success toast (similar to error toast)
        const toast = document.createElement('div');
        toast.className = 'toast toast-success';
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">✓</span>
                <span class="toast-message">${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    // ========================================================================
    // RANDEWOO PRODUCTS METHODS
    // ========================================================================
    
    async loadProducts() {
        console.log('[PRODUCTS] Loading from API...');
        
        try {
            const response = await fetch('/api/products');
            const data = await response.json();
            
            if (data.success) {
                this.products = data.products;
                console.log(`[PRODUCTS] Loaded ${this.products.length} products`);
                this.renderProducts();
            } else {
                throw new Error(data.error || 'Failed to load products');
            }
            
        } catch (error) {
            console.error('[PRODUCTS ERROR]', error);
            this.productsTableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 20px; color: var(--error);">
                        ❌ Error loading products: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
    
    renderProducts() {
        if (!this.products || this.products.length === 0) {
            this.productsTableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 20px; color: var(--text-secondary);">
                        No products found
                    </td>
                </tr>
            `;
            return;
        }
        
        this.productsTableBody.innerHTML = '';
        
        this.products.forEach(product => {
            const row = document.createElement('tr');
            row.dataset.productId = product.id;
            
            // Truncate description for display
            const descPreview = product.description 
                ? (product.description.length > 150 
                    ? this.escapeHtml(product.description.substring(0, 150)) + '...' 
                    : this.escapeHtml(product.description))
                : '<span style="color: var(--text-tertiary);">No description</span>';
            
            // Image thumbnail
            const imageHtml = product.image_path 
                ? `<img src="/images/${this.escapeHtml(product.image_path)}" alt="${this.escapeHtml(product.brand)} ${this.escapeHtml(product.name)}" style="width: 60px; height: 60px; object-fit: contain; border-radius: 4px;">`
                : '<span style="color: var(--text-tertiary); font-size: 0.8em;">No image</span>';
            
            row.innerHTML = `
                <td>${product.id}</td>
                <td style="text-align: center;">${imageHtml}</td>
                <td>${this.escapeHtml(product.brand)}</td>
                <td>${this.escapeHtml(product.name)}</td>
                <td style="font-size: 0.9em; line-height: 1.4;">${descPreview}</td>
                <td><a href="${product.product_url}" target="_blank" onclick="event.stopPropagation()">View</a></td>
                <td>${product.fragrantica_url ? `<a href="${product.fragrantica_url}" target="_blank" onclick="event.stopPropagation()">View</a>` : '-'}</td>
            `;
            
            row.addEventListener('click', () => {
                this.handleProductRowClick(product, row);
            });
            
            this.productsTableBody.appendChild(row);
        });
    }
    
    handleProductRowClick(product, row) {
        // Remove previous selection
        document.querySelectorAll('.products-table tbody tr').forEach(tr => {
            tr.classList.remove('selected');
        });
        
        // Mark current as selected
        row.classList.add('selected');
        
        this.selectedProduct = product;
        
        // Update UI
        this.selectedProductText.textContent = `${product.brand} - ${product.name}`;
        this.selectedProductInfo.style.display = 'flex';
        this.selectPerfumeBtn.disabled = false;
        
        console.log('[PRODUCT] Selected:', product);
    }
    
    async handleSelectPerfume() {
        if (!this.selectedProduct) {
            this.showError('Please select a product first');
            return;
        }
        
        const product = this.selectedProduct;
        
        // Fill form fields
        document.getElementById('brand').value = product.brand;
        document.getElementById('perfume_name').value = product.name;
        
        // Fill description from database
        const descriptionField = document.getElementById('description');
        if (product.description) {
            descriptionField.value = product.description;
            console.log('[SELECT] Description loaded from database');
        } else {
            descriptionField.value = '';
            console.log('[SELECT] No description in database');
        }
        
        // Show main image preview if available
        this.updateMainImagePreview(product.image_path);
        
        // Show styled image preview if available
        if (product.styled_image_path) {
            this.showStyledImageFromDB(product.styled_image_path, product.brand, product.name);
        }
        
        // Show video preview if available
        if (product.video_path) {
            this.showVideoFromDB(product.video_path);
        }
        
        // Scroll to form
        document.querySelector('.form-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Show success message
        let message = `✨ Selected: ${product.brand} - ${product.name}`;
        if (product.styled_image_path) message += ' [Image ✓]';
        if (product.video_path) message += ' [Video ✓]';
        this.showSuccess(message);
    }
    
    updateMainImagePreview(imagePath) {
        const preview = document.getElementById('mainImagePreview');
        const thumb = document.getElementById('mainImageThumb');
        const filename = document.getElementById('mainImageFilename');
        
        if (imagePath) {
            thumb.src = `/images/${imagePath}`;
            filename.textContent = imagePath;
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    }
    
    showStyledImageFromDB(styledImagePath, brand, perfumeName) {
        console.log('[DB] Loading styled image from database:', styledImagePath);
        
        // Create currentGeneration object to match existing structure
        this.currentGeneration = {
            brand: brand,
            perfume_name: perfumeName,
            image_url: `/images/${styledImagePath}`,
            styled_url: `/images/${styledImagePath}`,
            final_filename: styledImagePath
        };
        
        // Show in preview area
        const imagePath = `/images/${styledImagePath}`;
        this.previewArea.innerHTML = `
            <img src="${imagePath}" alt="${brand} ${perfumeName}" class="preview-image" 
                 onerror="console.error('Failed to load image:', '${imagePath}'); this.style.border='2px solid red';" />
        `;
        
        // Show image info
        this.imageInfo.style.display = 'block';
        document.getElementById('infoBrand').textContent = brand;
        document.getElementById('infoPerfume').textContent = perfumeName;
        document.getElementById('infoTime').textContent = 'From Database';
        document.getElementById('downloadBtn').style.display = 'block';
        
        // Show Generate Video button
        document.getElementById('generateVideoBtn').style.display = 'block';
        
        console.log('[DB] ✓ Styled image loaded from database');
    }
    
    showVideoFromDB(videoPath) {
        console.log('[DB] Loading video from database:', videoPath);
        
        const videoPlayer = document.getElementById('videoPlayer');
        const videoPreview = document.getElementById('videoPreview');
        
        // Set video source
        videoPlayer.src = `/videos/${videoPath}`;
        
        // Store video data
        this.currentVideoData = {
            video_url: `/videos/${videoPath}`,
            video_filename: videoPath
        };
        
        // Hide concept/prompt sections (loaded from DB, no Claude data)
        const conceptParent = document.getElementById('videoConcept')?.parentElement;
        const promptParent = document.getElementById('videoPrompt')?.parentElement;
        if (conceptParent) conceptParent.style.display = 'none';
        if (promptParent) promptParent.style.display = 'none';
        
        // Show video preview
        videoPreview.style.display = 'block';
        videoPreview.scrollIntoView({ behavior: 'smooth' });
        
        console.log('[DB] ✓ Video loaded from database');
    }
    
    async handleSaveMain() {
        const imageUrl = document.getElementById('image_url').value.trim();
        
        if (!imageUrl) {
            this.showError('Please enter Image URL first');
            return;
        }
        
        if (!this.selectedProduct) {
            this.showError('Please select a product first');
            return;
        }
        
        const saveBtn = document.getElementById('saveMainBtn');
        const btnText = saveBtn.querySelector('.btn-save-text');
        const btnLoader = saveBtn.querySelector('.btn-save-loader');
        
        // Set loading state
        saveBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'flex';
        
        try {
            console.log('[SAVE MAIN] Saving image:', imageUrl);
            
            const response = await fetch('/api/save-main-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_url: imageUrl,
                    product_id: this.selectedProduct.id,
                    brand: this.selectedProduct.brand,
                    name: this.selectedProduct.name
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('[SAVE MAIN] Image saved:', result.image_path);
                
                // Update preview
                this.updateMainImagePreview(result.image_path);
                
                // Update selectedProduct
                this.selectedProduct.image_path = result.image_path;
                
                // Show success
                this.showSuccess('💾 Image saved as main!');
                
                // Reset button after delay
                setTimeout(() => {
                    btnText.textContent = '💾 Save as main';
                    btnText.style.display = 'inline';
                    btnLoader.style.display = 'none';
                    saveBtn.disabled = false;
                }, 2000);
            } else {
                throw new Error(result.error || 'Failed to save image');
            }
            
        } catch (error) {
            console.error('[SAVE MAIN ERROR]', error);
            this.showError(`Failed to save image: ${error.message}`);
            
            // Reset button
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            saveBtn.disabled = false;
        }
    }
    
    // ========================================================================
    // TELEGRAM PUBLISH METHODS
    // ========================================================================
    
    async showTelegramSection() {
        if (!this.currentGeneration) {
            this.showError('Please generate visual first');
            return;
        }
        
        // Show section first
        this.telegramSection.style.display = 'block';
        this.telegramSection.scrollIntoView({ behavior: 'smooth' });
        
        // Get form data
        const brand = document.getElementById('brand').value.trim();
        const perfumeName = document.getElementById('perfume_name').value.trim();
        const description = document.getElementById('description').value.trim();
        
        // Update media preview (video if available, otherwise image)
        const previewImage = document.getElementById('telegramPreviewImage');
        const previewVideo = document.getElementById('telegramPreviewVideo');
        const mediaBadge = document.getElementById('telegramMediaBadge');
        
        if (this.currentVideoData && this.currentVideoData.video_url) {
            // Show video
            previewVideo.src = this.currentVideoData.video_url;
            previewVideo.style.display = 'block';
            previewImage.style.display = 'none';
            mediaBadge.textContent = '🎬 Video';
        } else {
            // Show image
            previewImage.src = this.currentGeneration.styled_url;
            previewImage.style.display = 'block';
            previewVideo.style.display = 'none';
            mediaBadge.textContent = '🖼️ Image';
        }
        
        // Set prompt from global settings (database) or use default
        const tgPrompt = document.getElementById('tgPrompt');
        
        if (this.globalPrompts && this.globalPrompts.caption) {
            // Use prompt from database and replace placeholders
            let prompt = this.globalPrompts.caption;
            prompt = prompt.replace('{BRAND}', brand);
            prompt = prompt.replace('{PERFUME_NAME}', perfumeName);
            prompt = prompt.replace('{DESCRIPTION}', description);
            tgPrompt.value = prompt;
            console.log('[TG] Using global prompt from database');
        } else {
            // Fallback to hardcoded default
            tgPrompt.value = `Создай продающий пост для Telegram канала о парфюме ${brand} ${perfumeName}.

Описание аромата: ${description}

Требования:
- Текст должен быть живым и эмоциональным
- Вызывать желание купить
- Подчеркивать уникальность аромата
- Использовать емодзи (но не переборщить)
- Длина: 3-5 предложений
- Стиль: casual, но профессионально

Формат ответа: только текст поста, без заголовков и пояснений.`;
            console.log('[TG] Using fallback default prompt (database not loaded)');
        }
        
        // Generate caption automatically
        await this.generateTgCaption();
    }
    
    async generateTgCaption() {
        const brand = document.getElementById('brand').value.trim();
        const perfumeName = document.getElementById('perfume_name').value.trim();
        const description = document.getElementById('description').value.trim();
        const customPrompt = document.getElementById('tgPrompt').value.trim();
        
        const tgCaption = document.getElementById('tgCaption');
        const previewCaption = document.getElementById('telegramPreviewCaption');
        
        // Show loading
        tgCaption.value = '⏳ Generating caption with Claude...';
        previewCaption.textContent = '⏳ Generating...';
        
        try {
            console.log('[TG] Generating caption...');
            
            const response = await fetch('/api/generate-tg-caption', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    brand,
                    perfume_name: perfumeName,
                    description,
                    prompt: customPrompt
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to generate caption');
            }
            
            const result = await response.json();
            
            console.log('[TG] Caption generated:', result.caption);
            
            // Update caption fields
            tgCaption.value = result.caption;
            previewCaption.textContent = result.caption;
            
        } catch (error) {
            console.error('[TG ERROR]', error);
            tgCaption.value = '';
            previewCaption.textContent = error.message;
            this.showError('Failed to generate caption: ' + error.message);
        }
    }
    
    async handleRecreateTgCaption() {
        const btn = document.getElementById('recreateTgBtn');
        const btnText = btn.querySelector('.btn-text');
        const btnLoader = btn.querySelector('.btn-loader');
        
        // Set loading state
        btn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        
        try {
            await this.generateTgCaption();
        } finally {
            // Reset button
            btn.disabled = false;
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    }
    
    async handlePublishToTelegram() {
        if (!this.currentGeneration) {
            this.showError('Please generate visual first');
            return;
        }
        
        // Get caption from textarea
        const caption = document.getElementById('tgCaption').value.trim();
        
        if (!caption) {
            this.showError('Please wait for caption to generate or enter caption manually');
            return;
        }
        
        const btn = this.publishTelegramBtn;
        const btnText = btn.querySelector('.btn-text');
        const btnLoader = btn.querySelector('.btn-loader');
        
        try {
            btn.disabled = true;
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
            
            const brand = document.getElementById('brand').value;
            const perfumeName = document.getElementById('perfume_name').value;
            
            // Use video if available, otherwise use image
            let mediaFile = '';
            let mediaType = 'image';
            
            if (this.currentVideoData && this.currentVideoData.video_filename) {
                mediaFile = this.currentVideoData.video_filename;
                mediaType = 'video';
            } else {
                mediaFile = this.currentGeneration.final_filename;
                mediaType = 'image';
            }
            
            const payload = {
                brand: brand,
                perfume_name: perfumeName,
                caption: caption,  // Use generated caption from textarea
                media_file: mediaFile,
                media_type: mediaType,
                product_url: this.selectedProduct ? this.selectedProduct.product_url : ''
            };
            
            console.log('[TELEGRAM] Publishing:', payload);
            
            const response = await fetch('/api/publish-to-telegram', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Success!
                console.log('[TELEGRAM] ✓ Published successfully!');
                
                const statusEl = document.getElementById('telegramStatus');
                statusEl.className = 'telegram-status success';
                statusEl.querySelector('.status-icon').textContent = '✅';
                statusEl.querySelector('.status-text').textContent = 'Published successfully!';
                
                this.showSuccess('🎉 Published to Telegram successfully!');
                
                // Hide section after 3 seconds
                setTimeout(() => {
                    this.telegramSection.style.display = 'none';
                }, 3000);
                
            } else {
                throw new Error(data.error || 'Failed to publish');
            }
            
        } catch (error) {
            console.error('[TELEGRAM ERROR]', error);
            
            const statusEl = document.getElementById('telegramStatus');
            statusEl.className = 'telegram-status error';
            statusEl.querySelector('.status-icon').textContent = '❌';
            statusEl.querySelector('.status-text').textContent = error.message;
            
            this.showError(`Failed to publish: ${error.message}`);
            
        } finally {
            btn.disabled = false;
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
        }
    }
    
    // ========================================================================
    // UTILITY METHODS
    // ========================================================================
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.perfumeGenerator = new PerfumeGenerator();
    console.log('Perfume Visual Generator initialized');
});

