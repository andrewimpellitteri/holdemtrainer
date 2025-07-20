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
        const handHistory = response.data;
        const replayer = new HandReplayer(handHistory);
        replayer.play();
    } catch (error) {
        console.error("Failed to fetch hand:", error);
        const log = document.getElementById('log-content');
        log.innerHTML = '<div class="alert alert-danger">Could not load hand data.</div>';
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
    }

    clearTable() {
        this.seatsContainer.innerHTML = '';
        this.boardContainer.innerHTML = '';
        this.potContainer.innerHTML = '';
        this.logContainer.innerHTML = '';
        this.decisionControls.style.display = 'none';
        this.feedbackContainer.innerHTML = '';
    }

    setupSeats() {
        const numPlayers = this.handHistory.players.length;
        const radius = 160;
        const centerX = 340;
        const centerY = 165;

        this.handHistory.players.forEach((player, i) => {
            const angle = (i / numPlayers) * 2 * Math.PI - Math.PI / 2;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);

            const seat = document.createElement('div');
            seat.className = 'seat';
            seat.id = `seat-${player.id}`;
            seat.style.left = `${x}px`;
            seat.style.top = `${y}px`;

            let heroBadge = '';
            if (player.id === this.handHistory.heroId) {
                heroBadge = '<span class="badge bg-success">Hero</span>';
            }

            seat.innerHTML = `
                <div class="player-info">
                    <strong>${player.name} ${heroBadge}</strong>
                </div>
                <div class="player-cards"></div>
            `;
            this.seatsContainer.appendChild(seat);
        });
    }

    play() {
        const action = this.handHistory.actions[this.actionIndex];
        if (!action) {
            this.showHeroCards();
            this.promptForDecision();
            return;
        }

        this.executeAction(action);
        this.actionIndex++;

        setTimeout(() => this.play(), 800);
    }

    executeAction(action) {
        this.logAction(action);
        if (action.type === 'street') {
            this.dealBoard(action.board);
        }
    }

    showHeroCards() {
        const heroSeat = document.getElementById(`seat-${this.handHistory.heroId}`);
        if (heroSeat) {
            const cardsContainer = heroSeat.querySelector('.player-cards');
            cardsContainer.innerHTML = this.formatCards(this.handHistory.hand);
        }
    }

    dealBoard(cards) {
        this.boardContainer.innerHTML += cards.map(c => `<div class="card">${this.formatCard(c)}</div>`).join('');
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
        switch (action.type) {
            case 'action': return `<strong>${action.player}:</strong> ${action.action}`;
            case 'street': return `<strong class="text-info text-capitalize">${action.street}:</strong> ${action.board.map(c => this.formatCard(c)).join(' ')}`;
            default: return JSON.stringify(action);
        }
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

        let feedbackClass = isCorrect ? 'alert-success' : 'alert-danger';
        let feedbackMessage = isCorrect ? `Correct! The best move is to ${correctMove}.` : `Incorrect. The best move is to ${correctMove}.`;

        this.feedbackContainer.innerHTML = `<div class="alert ${feedbackClass}">${feedbackMessage}</div>`;
    }
}