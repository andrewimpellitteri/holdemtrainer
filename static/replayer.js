document.addEventListener('DOMContentLoaded', () => {
    const playButton = document.getElementById('play-hand');
    const themeToggle = document.getElementById('theme-toggle');
    let correctAnswers = 0;
    let totalHands = 0;

    // Initialize theme
    initializeTheme();
    
    // Theme toggle functionality
    themeToggle.addEventListener('click', toggleTheme);

    function initializeTheme() {
        const savedTheme = localStorage.getItem('poker-theme') || 'light';
        document.body.setAttribute('data-theme', savedTheme);
        updateThemeToggleUI(savedTheme);
    }

    function toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('poker-theme', newTheme);
        updateThemeToggleUI(newTheme);
    }

    function updateThemeToggleUI(theme) {
        const icon = themeToggle.querySelector('i');
        const span = themeToggle.querySelector('span');
        
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            span.textContent = 'Light Mode';
        } else {
            icon.className = 'fas fa-moon';
            span.textContent = 'Dark Mode';
        }
    }

    function updateStats() {
        document.getElementById('stats-correct').textContent = correctAnswers;
        document.getElementById('stats-total').textContent = totalHands;
        
        const percentage = totalHands > 0 ? Math.round((correctAnswers / totalHands) * 100) : 0;
        document.getElementById('stats-percentage').textContent = percentage + '%';
    }

    playButton.addEventListener('click', () => {
        playButton.disabled = true;
        playButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        fetchHandAndPlay();
    });

    async function fetchHandAndPlay() {
        try {
            const response = await axios.get('/api/replayer_hand');
            totalHands++;
            updateStats();
            
            const replayer = new HandReplayer(response.data, () => {
                correctAnswers++;
                updateStats();
            });
            replayer.play();
        } catch (error) {
            console.error("Failed to fetch hand:", error);
            document.getElementById('log-content').innerHTML = '<div class="alert alert-danger">Could not load hand data.</div>';
        } finally {
            const playButton = document.getElementById('play-hand');
            playButton.disabled = false;
            playButton.innerHTML = '<i class="fas fa-play"></i> Load New Hand';
        }
    }

    updateStats(); // Initial stat display
});

class HandReplayer {
    constructor(handHistory, onCorrectDecision) {
        this.handHistory = handHistory;
        this.onCorrectDecision = onCorrectDecision;
        this.actionIndex = 0;
        this.seatsContainer = document.querySelector('.seats');
        this.boardContainer = document.querySelector('.board');
        this.potContainer = document.querySelector('.pot');
        this.logContainer = document.getElementById('log-content');
        this.decisionControls = document.getElementById('decision-controls');
        this.feedbackContainer = document.getElementById('feedback');
        this.clearTable();
        this.setupSeats();
        this.showHeroCards();
    }

    clearTable() {
        this.seatsContainer.innerHTML = '';
        this.boardContainer.innerHTML = '';
        this.potContainer.innerHTML = '';
        this.logContainer.innerHTML = '';
        this.decisionControls.style.display = 'none';
        this.feedbackContainer.style.display = 'none';
        this.feedbackContainer.innerHTML = '';
        document.querySelectorAll('.player-action').forEach(el => el.innerHTML = '');
    }

    setupSeats() {
        const numPlayers = this.handHistory.players.length;
        const radiusX = 275;
        const radiusY = 180;
        const centerX = 340;
        const centerY = 180;
        const seatWidth = 90;
        const seatHeight = 90;

        this.handHistory.players.forEach((player, i) => {
            const angle = (i / numPlayers) * 2 * Math.PI - Math.PI / 2;
            const x = centerX + radiusX * Math.cos(angle) - (seatWidth / 2);
            const y = centerY + radiusY * Math.sin(angle) - (seatHeight / 2);

            const seat = document.createElement('div');
            seat.className = 'seat';
            seat.id = `seat-${player.id}`;
            seat.style.left = `${x}px`;
            seat.style.top = `${y}px`;

            let badge = player.id === this.handHistory.heroId ? '<span class="badge bg-success">Hero</span>' : '';
            seat.innerHTML = `
                <div class="player-info">
                    <strong>${player.name} ${badge}</strong>
                </div>
                <div class="player-cards"></div>
                <div class="player-action"></div>
            `;
            this.seatsContainer.appendChild(seat);
        });
    }

    showHeroCards() {
        const heroSeat = document.getElementById(`seat-${this.handHistory.heroId}`);
        if (heroSeat) {
            const cardsContainer = heroSeat.querySelector('.player-cards');
            cardsContainer.innerHTML = this.formatCards(this.handHistory.hand);
        }
    }

    play() {
        const action = this.handHistory.actions[this.actionIndex];
        if (!action) {
            this.promptForDecision();
            return;
        }

        this.executeAction(action);
        this.actionIndex++;

        setTimeout(() => this.play(), 800);
    }

    executeAction(action) {
        this.logAction(action);
        this.potContainer.textContent = `Pot: ${action.pot_size}bb`;

        document.querySelectorAll('.player-action').forEach(el => el.innerHTML = '');

        if (action.type === 'street') {
            this.dealBoard(action.board);
        } else if (action.type === 'action') {
            const amountText = action.amount ? ` ${action.amount}bb` : '';
            this.showPlayerAction(action.player, `${action.action}${amountText}`);
        }
    }

    dealBoard(cards) {
        this.boardContainer.innerHTML += cards.map(c => `<div class="card">${this.formatCard(c)}</div>`).join('');
    }

    showPlayerAction(playerId, text) {
        // Handle case where playerId might be a position string
        let seat = document.getElementById(`seat-${playerId}`);
        if (!seat) {
            // Try to find seat by player name if ID doesn't work
            const allSeats = document.querySelectorAll('.seat');
            allSeats.forEach(s => {
                const playerInfo = s.querySelector('.player-info strong');
                if (playerInfo && playerInfo.textContent.includes(playerId)) {
                    seat = s;
                }
            });
        }
        
        if (seat) {
            const actionContainer = seat.querySelector('.player-action');
            actionContainer.innerHTML = `<span class="badge bg-info">${text}</span>`;
        }
    }

    logAction(action) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = this.formatAction(action);
        this.logContainer.appendChild(logEntry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }

    formatCards(handString) {
        const cards = handString.match(/.{1,2}/g) || [];
        return cards.map(c => `<div class="card">${this.formatCard(c)}</div>`).join('');
    }

    formatCard(card) {
        const suit_map = { s: '♠', h: '♥', d: '♦', c: '♣' };
        const suit = card.slice(-1);
        const rank = card.slice(0, -1);
        const color = (suit === 'h' || suit === 'd') ? 'text-danger' : 'text-dark';
        return `${rank}<span class="${color}">${suit_map[suit]}</span>`;
    }

    formatAction(action) {
        if (action.type === 'street') {
            return `<strong class="text-info text-capitalize">${action.street}:</strong> ${action.board.map(c => this.formatCard(c)).join(' ')}`;
        }
        return `<strong>${action.player}:</strong> ${action.action}`;
    }

    promptForDecision() {
        this.decisionControls.style.display = 'block';
        this.decisionControls.innerHTML = '<h3 class="decision-title">Your turn. What is your decision?</h3>';
        
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'controls';
        
        this.handHistory.available_moves.forEach(move => {
            const button = document.createElement('button');
            button.className = 'btn btn-outline-primary';
            button.innerHTML = `<i class="fas fa-hand-point-right"></i> ${move}`;
            button.onclick = () => this.checkDecision(move);
            controlsDiv.appendChild(button);
        });
        
        this.decisionControls.appendChild(controlsDiv);
    }

    checkDecision(chosenMove) {
        const correctMove = this.handHistory.correct_decision;
        const isCorrect = chosenMove.toLowerCase() === correctMove.toLowerCase();
        
        this.decisionControls.style.display = 'none';
        
        const feedbackClass = isCorrect ? 'alert-success' : 'alert-danger';
        const icon = isCorrect ? 'fas fa-check-circle' : 'fas fa-times-circle';
        const feedbackMessage = isCorrect 
            ? `Correct! The best move is to ${correctMove}.` 
            : `Incorrect. The best move is to ${correctMove}.`;
            
        this.feedbackContainer.innerHTML = `
            <div class="alert ${feedbackClass}">
                <i class="${icon}"></i>
                ${feedbackMessage}
            </div>
        `;
        this.feedbackContainer.style.display = 'block';

        if (isCorrect) {
            this.onCorrectDecision();
        }
        
        // Auto-hide feedback after 3 seconds
        setTimeout(() => {
            this.feedbackContainer.style.display = 'none';
        }, 3000);
    }
}