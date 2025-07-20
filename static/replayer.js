document.addEventListener('DOMContentLoaded', () => {
    const playButton = document.getElementById('play-hand');
    playButton.addEventListener('click', () => {
        playButton.disabled = true;
        fetchHandAndPlay();
    });
});

async function fetchHandAndPlay() {
    try {
        const response = await axios.get('/api/replayer_hand');
        const handHistory = response.data;
        const replayer = new HandReplayer(handHistory);
        replayer.play();
    } catch (error) {
        console.error("Failed to fetch hand:", error);
        const log = document.getElementById('log-content');
        log.innerHTML = '<div class="alert alert-danger">Could not load hand.</div>';
        document.getElementById('play-hand').disabled = false;
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
                    <div class="stack">100bb</div>
                </div>
                <div class="player-cards"></div>
            `;
            this.seatsContainer.appendChild(seat);
        });
    }

    play() {
        const action = this.handHistory.actions[this.actionIndex];
        if (!action) {
            this.promptForDecision();
            return;
        }

        this.executeAction(action);
        this.actionIndex++;

        setTimeout(() => this.play(), 1000); // Delay for next action
    }

    executeAction(action) {
        this.logAction(action);
        switch (action.type) {
            case 'action':
                // Visual feedback for action can be added here
                break;
            case 'flop':
            case 'turn':
            case 'river':
                this.dealBoard(action.board);
                break;
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

    formatCard(card) {
        const suit_map = { s: '♠', h: '♥', d: '♦', c: '♣' };
        return card.slice(0, -1) + suit_map[card.slice(-1)];
    }

    formatAction(action) {
        switch (action.type) {
            case 'action': return `<strong>${action.player}:</strong> ${action.action} ${action.amount || ''}`.trim();
            case 'flop': return `<strong class="text-info">Flop:</strong> ${action.board.map(c => this.formatCard(c)).join(' ')}`;
            case 'turn': return `<strong class="text-info">Turn:</strong> ${this.formatCard(action.board[0])}`;
            case 'river': return `<strong class="text-info">River:</strong> ${this.formatCard(action.board[0])}`;
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

        this.decisionControls.innerHTML = ''; // Clear buttons

        let feedbackClass = isCorrect ? 'alert-success' : 'alert-danger';
        let feedbackMessage = isCorrect ? `Correct! The best move is to ${correctMove}.` : `Incorrect. The best move is to ${correctMove}.`;

        this.feedbackContainer.innerHTML = `<div class="alert ${feedbackClass}">${feedbackMessage}</div>`;
        document.getElementById('play-hand').disabled = false; // Allow playing a new hand
    }
}