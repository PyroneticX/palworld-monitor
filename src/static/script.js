// Theme management
function getThemeFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('theme');
}

function setThemeInURL(theme) {
    const url = new URL(window.location);
    if (theme) {
        url.searchParams.set('theme', theme);
    } else {
        url.searchParams.delete('theme');
    }
    window.history.replaceState({}, '', url);
}

function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function initTheme() {
    const savedTheme = getThemeFromURL();
    const systemTheme = getSystemTheme();
    const theme = savedTheme || systemTheme;
    
    document.body.setAttribute('data-theme', theme);
    updateThemeButton(theme);
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        // Only auto-switch if no manual theme is set in URL
        if (!getThemeFromURL()) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.body.setAttribute('data-theme', newTheme);
            updateThemeButton(newTheme);
        }
    });
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const isManualTheme = getThemeFromURL() !== null;
    
    // If currently following system theme, set manual theme
    if (!isManualTheme) {
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.body.setAttribute('data-theme', newTheme);
        setThemeInURL(newTheme);
        updateThemeButton(newTheme);
    } else {
        // If manual theme is set, reset to system theme
        resetToSystemTheme();
    }
}

function resetToSystemTheme() {
    const systemTheme = getSystemTheme();
    document.body.setAttribute('data-theme', systemTheme);
    setThemeInURL(null); // Remove manual theme from URL
    updateThemeButton(systemTheme);
}

function updateThemeButton(theme) {
    const button = document.getElementById('themeToggle');
    const isManualTheme = getThemeFromURL() !== null;
    
    if (theme === 'dark') {
        button.innerHTML = '<span class="icon">☀️</span>';
        button.title = isManualTheme ? 'Switch to light mode' : 'System dark mode (click to override)';
    } else {
        button.innerHTML = '<span class="icon">🌙</span>';
        button.title = isManualTheme ? 'Switch to dark mode' : 'System light mode (click to override)';
    }
    
    // Add visual indicator for system theme
    if (!isManualTheme) {
        button.classList.add('system-theme');
    } else {
        button.classList.remove('system-theme');
    }
}

// Server action scheduling
function scheduleStatusCheck() {
    setTimeout(function(){
        handleServerAction("getStatus");
    }, 5000);
}

// UI update functions
function updateServerStatusUI(data, response) {
    const runningElements = document.querySelectorAll(".status-indicator.running");
    const offElements = document.querySelectorAll(".status-indicator.off");
    const offBtn = document.getElementById("offBtn");
    const onBtn = document.getElementById("onBtn");
    const statusOn = document.querySelector('.status-on');
    const statusOff = document.querySelector('.status-off');
    
    if(data.running){
        if (statusOn) statusOn.style.display = "inline-block";
        if (statusOff) statusOff.style.display = "none";
        runningElements.forEach(el => el.style.display = "inline-block");
        offElements.forEach(el => el.style.display = "none");
        if (offBtn) offBtn.style.display = "block";
        if (onBtn) onBtn.style.display = "none";
    }
    else{
        if (statusOn) statusOn.style.display = "none";
        if (statusOff) statusOff.style.display = "inline-block";
        runningElements.forEach(el => el.style.display = "none");
        offElements.forEach(el => el.style.display = "inline-block");
        if (offBtn) offBtn.style.display = "none";
        if (onBtn) onBtn.style.display = "block";
    }
}



function updatePlayerInfoUI(data, response) {
    const playersInfoElement = document.getElementById("playersInfo");
    if (!playersInfoElement) return;
    if (response.players && response.players.length > 0) {
        let playerList = "";
        // Sort by online first, then level (desc), then name
        const sortedPlayers = response.players.sort((a, b) => {
            if (a.currently_online !== b.currently_online) return b.currently_online - a.currently_online;
            const levelA = parseInt(a.level) || 0;
            const levelB = parseInt(b.level) || 0;
            if (levelA !== levelB) return levelB - levelA;
            return a.name.localeCompare(b.name);
        });
        sortedPlayers.forEach(player => {
            const status = player.currently_online ? '🟢 Online' : '🔴 Offline';
            const lastOnlineText = player.currently_online ? '' : `<span class="last-online">Last online: ${formatTimestamp(player.last_online)}</span>`;
            playerList += `<div class="player-entry ${player.currently_online ? 'online' : 'offline'}">
                <span class="player-name">${player.name}</span><br>
                <span class="player-level">LVL ${player.level}</span>
                <span class="player-status">${status}</span>
                ${lastOnlineText}
            </div>`;
        });
        playersInfoElement.innerHTML = playerList;
    } else {
        playersInfoElement.textContent = "- No players found";
    }
}

function formatTimestamp(timestamp) {
    if (!timestamp) return "Unknown";
    try {
        const now = Date.now() / 1000;
        const diff = now - timestamp;
        if (diff < 60) {
            return "Just now";
        } else if (diff < 3600) {
            const minutes = Math.floor(diff / 60);
            return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        } else if (diff < 86400) {
            const hours = Math.floor(diff / 3600);
            return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        } else {
            const days = Math.floor(diff / 86400);
            return `${days} day${days !== 1 ? 's' : ''} ago`;
        }
    } catch (e) {
        return "Unknown";
    }
}

function updateLastUpdatedUI() {
    const lastUpdatedElement = document.getElementById("lastUpdatedText");
    if (lastUpdatedElement) lastUpdatedElement.textContent = new Date();
}

// AJAX request handling
async function makeServerRequest(action) {
    try {
        const formData = new FormData();
        formData.append('action', action);
        
        const response = await fetch('/action', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error making server request:', error);
        throw error;
    }
}

// Confirmation handler for server stop action
function confirmAndHandleServerAction(action) {
    if (confirm('Are you sure you want to stop the server?')) {
        handleServerAction(action);
    }
}

// Main server action handler
async function handleServerAction(action) {
    try {
        // Schedule status check for server start/stop actions
        if(action === "startServer" || action === "stopServer"){
            scheduleStatusCheck();
        }

        const response = await makeServerRequest(action);
        let data = response.data;

        updateServerStatusUI(data, response);
        updatePlayerInfoUI(data, response);
        updateLastUpdatedUI();
    } catch (error) {
        console.error('Error handling server action:', error);
    }
}



// Event listeners
document.addEventListener('DOMContentLoaded', function(){
    initTheme();
    handleServerAction("getStatus");
    
    // Get update interval from data attribute (default to 30 seconds if not set)
    const updateInterval = parseInt(document.body.getAttribute('data-update-interval')) || 30;
    
    // Set up automatic refresh using the configured update interval
    setInterval(function(){
        handleServerAction("getStatus");
    }, 1000 * updateInterval); // Use configured update interval
}); 