document.addEventListener('DOMContentLoaded', function() {
    loadPlayers();
    loadPinballMachines();
    setupInputListeners();

});

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
    const score = document.getElementById('score-input').value;

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
            alert('Score erfolgreich gespeichert!');
        } else {
            alert('Fehler beim Speichern des Scores.');
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





