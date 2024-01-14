document.addEventListener('DOMContentLoaded', function() {
    loadPlayers();
    loadPinballMachines();
    setupInputListeners();
    document.getElementById('player-select').addEventListener('change', loadScoreOverview);
    document.getElementById('pinball-select').addEventListener('change', loadScoreOverview);
});

// Funktionen zum Arbeiten mit Cookies
function setCookie(name, value, days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}


function setupInputListeners() {
    document.getElementById('player-select').addEventListener('change', validateInputs);
    document.getElementById('pinball-select').addEventListener('change', validateInputs);
    document.getElementById('score-input').addEventListener('input', validateInputs);
}

function validateInputs() {
    const player = document.getElementById('player-select').value;
    const pinball = document.getElementById('pinball-select').value;
    const score = document.getElementById('score-input').value;

    const submitButton = document.querySelector('.submit-button');
    if (player && pinball && score) {
        submitButton.disabled = false;
        submitButton.classList.remove('submit-button_disabled');
    } else {
        submitButton.disabled = true;
        submitButton.classList.add('submit-button_disabled');
    }
}


function loadPlayers() {
    fetch('/players')
        .then(response => response.json())
        .then(players => {
            const playerSelect = document.getElementById('player-select');
            players.forEach(player => {
                const option = document.createElement('option');
                option.value = player.abbreviation;
                option.textContent = player.name;
                playerSelect.appendChild(option);
            });

            // Setzt die Auswahl auf den Wert im Cookie, falls vorhanden
            const lastSelectedPlayer = getCookie("lastSelectedPlayer");
            if (lastSelectedPlayer) {
                playerSelect.value = lastSelectedPlayer;
            }
        });

    // Speichert die Auswahl, wenn sich die Auswahl ändert
    document.getElementById('player-select').addEventListener('change', function() {
        setCookie("lastSelectedPlayer", this.value, 365); // Speichert die Auswahl für 365 Tage
    });
}


function loadPinballMachines() {
    fetch('/pinball')
        .then(response => response.json())
        .then(pinballMachines => {
            const pinballSelect = document.getElementById('pinball-select');
            const groupedMachines = groupByRoom(pinballMachines);

            Object.keys(groupedMachines).forEach(room => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = `Raum ${room}`;
                groupedMachines[room].forEach(machine => {
                    const option = document.createElement('option');
                    option.value = machine.abbreviation;
                    option.textContent = machine.long_name;
                    optgroup.appendChild(option);
                });
                pinballSelect.appendChild(optgroup);
            });
        });
}

function groupByRoom(pinballMachines) {
    const groups = {};
    pinballMachines.forEach(machine => {
        if (!groups[machine.room]) {
            groups[machine.room] = [];
        }
        groups[machine.room].push(machine);
    });
    return groups;
}

function submitScore() {
    const player = document.getElementById('player-select').value;
    const pinball = document.getElementById('pinball-select').value;
    const scoreInput = document.getElementById('score-input');
    const score = scoreInput.value;

    console.log(parseInt(score.replaceAll(",","")));

    // Ermitteln des heutigen Datums im Format YYYY-MM-DD
    const today = new Date();
    const formattedDate = today.toISOString().split('T')[0];

    fetch('/score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            player_abbreviation: player,
            pinball_abbreviation: pinball,
            points: parseInt(score.replaceAll(",","")),
            date: formattedDate
        })
    })
    .then(response => {
        if (response.ok) {
            alert('Score submitted successful!');
            scoreInput.value = ''; // Clear the score input field
            validateInputs(); // Re-validate inputs to disable the submit button
        } else {
            alert('Error submitting score.');
        }
    });
}


function formatScoreInput(inputElement) {
    // Ersetze alle Zeichen außer Zahlen und entferne führende Nullen
    let value = inputElement.value.replace(/[^\d]/g, '').replace(/^0+/, '');

    // Teile die Zahl in Gruppen von drei Ziffern
    value = value.replace(/\B(?=(\d{3})+(?!\d))/g, ',');

    // Setze den formatierten Wert zurück ins Eingabefeld
    inputElement.value = value;
}

function loadScoreOverview() {
    const player = document.getElementById('player-select').value;
    const pinball = document.getElementById('pinball-select').value;

    if (player && pinball) {
        fetch(`/score-overview/${pinball}/${player}`)
            .then(response => response.json())
            .then(data => {
                const minScoreFormatted = data.minScore ? data.minScore.toLocaleString() : 'not scored yet';
                const maxScoreFormatted = data.maxScore ? data.maxScore.toLocaleString() : 'not scored yet';
                const playerScoreFormatted = data.playerScore ? data.playerScore.toLocaleString() : 'not scored yet';

                document.getElementById('score-overview').innerHTML = `
                    Minimum Score: ${minScoreFormatted} <br>
                    Grand Champion: ${maxScoreFormatted} <br>
                    Personal Best: ${playerScoreFormatted}
                `;
            });
    }
}





