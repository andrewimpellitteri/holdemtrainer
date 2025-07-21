document.addEventListener('DOMContentLoaded', () => {
    const playButton = document.getElementById('play-hand');
    playButton.addEventListener('click', () => {
        playButton.disabled = true;
        playButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Loading...';
        fetchHandAndPlay();
    });
});

async function fetchHandAndPlay() {
    try {
        const response = await axios.get('/api/hand');
        const replayer = new HandReplayer(response.data);
        replayer.play();
    } catch (error) {
        console.error("Failed to fetch hand:", error);
        document.getElementById('log-content').innerHTML = '<div class="alert alert-danger">Could not load hand data.</div>';
    } finally {
        const playButton = document.getElementById('play-hand');
        playButton.disabled = false;
        playButton.textContent = 'Load New Hand';
    }
}

class HandReplayer {
    constructor(handHistory) {
        this.handHistory = handHistory;
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
        this.feedbackContainer.innerHTML = '';
        // Clear all player actions when table is cleared
        document.querySelectorAll('.player-action').forEach(el => el.innerHTML = '');
    }

    setupSeats() {
        const numPlayers = this.handHistory.players.length;
        const radiusX = 275; // Horizontal radius for ellipse
        const radiusY = 145; // Vertical radius for ellipse
        const centerX = 340;
        const centerY = 165;
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
        // Update pot size display
        this.potContainer.textContent = `Pot: ${action.pot_size}bb`;

        // Clear previous action for the current player before showing new one
        const playerActionElements = document.querySelectorAll('.player-action');
        playerActionElements.forEach(el => el.innerHTML = '');

        if (action.type === 'street') {
            this.dealBoard(action.board);
        } else if (action.type === 'action' && action.amount) {
            this.showPlayerAction(action.player, `${action.action} ${action.amount}`);
        } else if (action.type === 'action') { // For actions without amount like 'check', 'fold'
            this.showPlayerAction(action.player, action.action);
        }
    }

    dealBoard(cards) {
        this.boardContainer.innerHTML += cards.map(c => `<div class="card">${this.formatCard(c)}</div>`).join('');
    }

    showPlayerAction(playerId, text) {
        const seat = document.getElementById(`seat-${playerId}`);
        if (seat) {
            const actionContainer = seat.querySelector('.player-action');
            actionContainer.innerHTML = `<span class="badge bg-info">${text}</span>`;
            // Removed setTimeout to make it persistent
        }
    }

    logAction(action) {
        const logEntry = document.createElement('div');
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
        this.decisionControls.innerHTML = '<h5>Your turn. What is your decision?</h5>';
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'btn-group';

        this.handHistory.available_moves.forEach(move => {
            const button = document.createElement('button');
            button.className = 'btn btn-outline-primary';
            button.textContent = move;
            button.onclick = () => this.checkDecision(move);
            buttonGroup.appendChild(button);
        });
        this.decisionControls.appendChild(buttonGroup);
    }

    checkDecision(chosenMove) {
        const correctMove = this.handHistory.correct_decision;
        const isCorrect = chosenMove.toLowerCase() === correctMove.toLowerCase();
        this.decisionControls.innerHTML = '';
        const feedbackClass = isCorrect ? 'alert-success' : 'alert-danger';
        const feedbackMessage = isCorrect ? `Correct! The best move is to ${correctMove}.` : `Incorrect. The best move is to ${correctMove}.`;
        this.feedbackContainer.innerHTML = `<div class="alert ${feedbackClass}">${feedbackMessage}</div>`;
    }
}