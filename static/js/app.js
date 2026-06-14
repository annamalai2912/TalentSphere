// TalentSphere AI - Dashboard Controller

document.addEventListener("DOMContentLoaded", () => {
    // State Variables
    let uploadedFiles = [];
    let candidatesData = [];
    let jobSkills = [];

    // DOM Elements
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const fileList = document.getElementById("file-list");
    const rankBtn = document.getElementById("rank-btn");
    const btnSpinner = document.getElementById("btn-spinner");
    const jobDescTextarea = document.getElementById("job-desc");
    const demoBtn = document.getElementById("demo-btn");
    
    const emptyState = document.getElementById("empty-state");
    const candidatesList = document.getElementById("candidates-list");
    const rankingsContainer = document.getElementById("rankings-container");
    const resultsCount = document.getElementById("results-count");
    const jobTag = document.getElementById("job-tag");
    
    // Details Drawer Elements
    const detailsDrawer = document.getElementById("details-drawer");
    const closeDrawerBtn = document.getElementById("close-drawer");
    const detailName = document.getElementById("detail-name");
    const detailFilename = document.getElementById("detail-filename");
    const detailScoreVal = document.getElementById("detail-score-val");
    const detailRadialProgress = document.getElementById("detail-radial-progress");
    const detailEmail = document.getElementById("detail-email");
    const detailPhone = document.getElementById("detail-phone");
    const detailEduSummary = document.getElementById("detail-edu-summary");
    const detailExpSummary = document.getElementById("detail-exp-summary");
    
    const detailValSemantic = document.getElementById("detail-val-semantic");
    const detailBarSemantic = document.getElementById("detail-bar-semantic");
    const detailValSkills = document.getElementById("detail-val-skills");
    const detailBarSkills = document.getElementById("detail-bar-skills");
    const detailValEdu = document.getElementById("detail-val-edu");
    const detailBarEdu = document.getElementById("detail-bar-edu");
    const detailValExp = document.getElementById("detail-val-exp");
    const detailBarExp = document.getElementById("detail-bar-exp");
    
    const detailMatchedTags = document.getElementById("detail-matched-tags");
    const detailMissingTags = document.getElementById("detail-missing-tags");
    const detailHighlights = document.getElementById("detail-highlights");
    const toast = document.getElementById("toast");

    /* ==========================================================================
       1. File Upload & Drag & Drop Handling
       ========================================================================== */
    
    // Trigger file dialog
    dropZone.addEventListener("click", () => fileInput.click());

    // File input selection
    fileInput.addEventListener("change", (e) => {
        handleFiles(e.target.files);
    });

    // Drag events
    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("drag-over");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("drag-over");
        }, false);
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    // Handle files validation and state updates
    function handleFiles(files) {
        const allowedExtensions = [".pdf", ".docx", ".doc", ".txt"];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const name = file.name;
            const ext = name.substring(name.lastIndexOf(".")).toLowerCase();
            
            if (allowedExtensions.includes(ext)) {
                // Check if file is already in the list to avoid duplicates
                if (!uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
                    uploadedFiles.push(file);
                }
            } else {
                showToast(`Unsupported file format: ${name}. Please upload PDF, DOCX, or TXT files.`, "error");
            }
        }
        updateFileList();
        validateForm();
    }

    // Render list of files
    function updateFileList() {
        fileList.innerHTML = "";
        
        if (uploadedFiles.length === 0) {
            fileList.style.display = "none";
            return;
        }
        
        fileList.style.display = "flex";
        uploadedFiles.forEach((file, index) => {
            const li = document.createElement("li");
            li.className = "file-item";
            
            // Shorten file size display
            const sizeInKb = (file.size / 1024).toFixed(1);
            
            li.innerHTML = `
                <div class="file-item-info">
                    <span class="file-icon">${getFileIcon(file.name)}</span>
                    <span class="file-item-name" title="${file.name}">${file.name}</span>
                    <span class="text-muted">(${sizeInKb} KB)</span>
                </div>
                <button type="button" class="btn-remove-file" data-index="${index}">&times;</button>
            `;
            
            fileList.appendChild(li);
        });

        // Add event listeners to remove buttons
        document.querySelectorAll(".btn-remove-file").forEach(button => {
            button.addEventListener("click", (e) => {
                const index = parseInt(e.target.getAttribute("data-index"));
                uploadedFiles.splice(index, 1);
                updateFileList();
                validateForm();
            });
        });
    }

    function getFileIcon(filename) {
        const ext = filename.substring(filename.lastIndexOf(".")).toLowerCase();
        if (ext === ".pdf") return "📕";
        if (ext === ".docx" || ext === ".doc") return "📘";
        return "📄";
    }

    /* ==========================================================================
       2. UI Form Validation & Operations
       ========================================================================== */
    
    jobDescTextarea.addEventListener("input", validateForm);

    function validateForm() {
        const hasText = jobDescTextarea.value.trim().length > 10;
        const hasFiles = uploadedFiles.length > 0;
        rankBtn.disabled = !(hasText && hasFiles);
    }

    /* ==========================================================================
       3. 1-Click Demo Feature
       ========================================================================== */
    
    demoBtn.addEventListener("click", async () => {
        try {
            demoBtn.disabled = true;
            showToast("Loading demo dataset...", "success");
            
            const response = await fetch("/api/samples");
            if (!response.ok) throw new Error("Failed to retrieve sample dataset.");
            const data = await response.json();
            
            // 1. Populate Job Description
            jobDescTextarea.value = data.job_description;
            
            // 2. Convert mock candidates to File objects (Blobs)
            uploadedFiles = [];
            data.candidates.forEach(cand => {
                const blob = new Blob([cand.text], { type: "text/plain" });
                const file = new File([blob], cand.filename, { type: "text/plain" });
                uploadedFiles.push(file);
            });
            
            updateFileList();
            validateForm();
            showToast("Demo data loaded. Starting NLP pipeline...", "success");
            
            // 3. Auto run pipeline
            runRankingPipeline();
        } catch (error) {
            showToast(error.message, "error");
            demoBtn.disabled = false;
        }
    });

    /* ==========================================================================
       4. Rank Action & API Request
       ========================================================================== */
    
    rankBtn.addEventListener("click", () => {
        runRankingPipeline();
    });

    async function runRankingPipeline() {
        if (uploadedFiles.length === 0 || !jobDescTextarea.value.trim()) return;

        // Set Loading state
        rankBtn.disabled = true;
        btnSpinner.style.display = "inline-block";
        rankBtn.querySelector("span").textContent = "Processing NLP Pipeline...";
        demoBtn.disabled = true;

        const formData = new FormData();
        formData.append("job_description", jobDescTextarea.value.trim());
        
        uploadedFiles.forEach(file => {
            formData.append("resumes", file);
        });

        try {
            const response = await fetch("/api/rank", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Server error in NLP screening pipeline.");
            }

            const data = await response.json();
            candidatesData = data.candidates;
            jobSkills = data.required_skills_detected;
            
            // Render results
            renderResults(data);
            showToast(`Screened ${candidatesData.length} resumes successfully!`, "success");
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            // Restore button states
            rankBtn.disabled = false;
            btnSpinner.style.display = "none";
            rankBtn.querySelector("span").textContent = "Screen and Rank Candidates";
            demoBtn.disabled = false;
        }
    }

    /* ==========================================================================
       5. Render Rankings List
       ========================================================================== */
    
    function renderResults(data) {
        // Hide empty state
        emptyState.style.display = "none";
        candidatesList.style.display = "flex";
        
        // Update header badges
        resultsCount.textContent = `Found and sorted ${data.candidates.length} candidates by relevance score.`;
        
        jobTag.textContent = data.job_title_detected;
        jobTag.style.display = "inline-block";
        
        candidatesList.innerHTML = "";
        
        data.candidates.forEach((cand, idx) => {
            const rank = idx + 1;
            const card = document.createElement("div");
            
            // Setup card rank class names
            let rankClass = "";
            if (rank === 1) rankClass = "rank-1";
            else if (rank === 2) rankClass = "rank-2";
            else if (rank === 3) rankClass = "rank-3";
            
            card.className = `candidate-card ${rankClass}`;
            card.dataset.index = idx;
            
            // Score style rating
            let matchRatingClass = "low-match";
            if (cand.overall_score >= 80) matchRatingClass = "high-match";
            else if (cand.overall_score >= 55) matchRatingClass = "med-match";
            
            // Display sub-skills tags (show up to 4 tags)
            const tagsToShow = cand.skills_found.slice(0, 4);
            let tagsHtml = tagsToShow.map(s => `<span class="pill pill-default">${s}</span>`).join("");
            if (cand.skills_found.length > 4) {
                tagsHtml += `<span class="pill pill-default">+${cand.skills_found.length - 4} more</span>`;
            }
            if (tagsHtml === "") {
                tagsHtml = `<span class="pill pill-default">No technical skills detected</span>`;
            }

            // Degree summary
            const degreeText = cand.education_extracted.length > 0 ? cand.education_extracted.join(", ") : "Self-taught / Other";
            const expText = cand.experience_years > 0 ? `${cand.experience_years} yrs exp` : "Entry-level";

            card.innerHTML = `
                <div class="rank-badge">${rank}</div>
                <div class="candidate-meta">
                    <h3>${cand.candidate_name}</h3>
                    <span class="candidate-file">${cand.filename}</span>
                    <div class="candidate-tags">
                        <span class="pill pill-success">${degreeText} • ${expText}</span>
                        ${tagsHtml}
                    </div>
                </div>
                <div class="score-indicator">
                    <span class="score-percent ${matchRatingClass}">${cand.overall_score}%</span>
                    <span class="text-muted" style="font-size: 0.75rem;">relevance</span>
                </div>
            `;
            
            // Click to open details
            card.addEventListener("click", () => openDetails(idx));
            candidatesList.appendChild(card);
        });
    }

    /* ==========================================================================
       6. Candidate Detailed Report Drawer
       ========================================================================== */
    
    function openDetails(index) {
        const candidate = candidatesData[index];
        if (!candidate) return;

        // Populate header details
        detailName.textContent = candidate.candidate_name;
        detailFilename.textContent = `File source: ${candidate.filename}`;
        
        // Progress Circular Ring Animation
        detailScoreVal.textContent = `${candidate.overall_score}%`;
        detailRadialProgress.style.setProperty("--val", Math.round(candidate.overall_score));
        
        // Contact details
        detailEmail.textContent = candidate.email || "Not found in resume";
        detailPhone.textContent = candidate.phone || "Not found in resume";
        
        const degrees = candidate.education_extracted.length > 0 ? candidate.education_extracted.join(", ") : "No specific degree found";
        detailEduSummary.textContent = `Education: ${degrees}`;
        
        const exp = candidate.experience_years > 0 ? `${candidate.experience_years} Year(s)` : "Entry-level / Minimal industry mentions";
        detailExpSummary.textContent = `Experience: ${exp}`;

        // Populate Score Breakdowns (Sub-score percentages & Widths)
        animateBar(detailBarSemantic, detailValSemantic, candidate.semantic_score);
        animateBar(detailBarSkills, detailValSkills, candidate.skill_score);
        animateBar(detailBarEdu, detailValEdu, candidate.education_score);
        animateBar(detailBarExp, detailValExp, candidate.experience_score);

        // Populate Match Skills (Pills)
        detailMatchedTags.innerHTML = "";
        if (candidate.skills_found.length > 0) {
            candidate.skills_found.forEach(skill => {
                const tag = document.createElement("span");
                tag.className = "tag-pill tag-matched";
                tag.innerHTML = `✓ ${skill}`;
                detailMatchedTags.appendChild(tag);
            });
        } else {
            detailMatchedTags.innerHTML = `<span class="text-muted" style="font-size:0.875rem;">No direct matching skills detected.</span>`;
        }

        // Populate Missing Skills (Pills)
        detailMissingTags.innerHTML = "";
        if (candidate.skills_missing.length > 0) {
            candidate.skills_missing.forEach(skill => {
                const tag = document.createElement("span");
                tag.className = "tag-pill tag-missing";
                tag.innerHTML = `✕ ${skill}`;
                detailMissingTags.appendChild(tag);
            });
        } else {
            detailMissingTags.innerHTML = `<span class="text-muted" style="font-size:0.875rem; color:var(--success-color);">None! Perfect skill alignment.</span>`;
        }

        // Semantic Highlights
        detailHighlights.innerHTML = "";
        if (candidate.key_highlights && candidate.key_highlights.length > 0) {
            candidate.key_highlights.forEach(highlight => {
                const li = document.createElement("li");
                li.textContent = highlight;
                detailHighlights.appendChild(li);
            });
        } else {
            detailHighlights.innerHTML = `<li class="text-muted" style="list-style:none;">No major semantic highlights were extracted from this candidate's resume.</li>`;
        }

        // Open drawer
        detailsDrawer.classList.add("open");
    }

    function animateBar(barElement, textElement, score) {
        textElement.textContent = `${score}%`;
        barElement.style.width = "0%";
        setTimeout(() => {
            barElement.style.width = `${score}%`;
        }, 150);
    }

    // Close drawer handlers
    closeDrawerBtn.addEventListener("click", closeDrawer);
    
    detailsDrawer.addEventListener("click", (e) => {
        if (e.target === detailsDrawer) closeDrawer();
    });

    function closeDrawer() {
        detailsDrawer.classList.remove("open");
    }

    /* ==========================================================================
       7. Helper Utilities (Toasts)
       ========================================================================== */
    
    let toastTimeout;
    function showToast(message, type = "success") {
        clearTimeout(toastTimeout);
        toast.className = `toast toast-${type} show`;
        toast.textContent = message;
        
        toastTimeout = setTimeout(() => {
            toast.classList.remove("show");
        }, 4000);
    }
});
