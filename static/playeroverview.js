document.addEventListener('DOMContentLoaded', function() {

    loadPlayers();
    loadPinballMachinesData();
});

function loadPlayers() {
    fetch('/players')
        .then(response => response.json())
        .then(players => {
            const playerSelect = document.getElementById('player-select');
            playerSelect.innerHTML = '<option value="">Spieler wählen</option>';
            players.forEach(player => {
                const option = document.createElement('option');
                option.value = player.abbreviation;
                option.textContent = player.name;
                playerSelect.appendChild(option);
            });
        });
}

function loadPinballMachinesData() {
    fetch('/pinball')
        .then(response => response.json())
        .then(pinballMachines => {
            allPinballMachines = pinballMachines;
        });
}

function fetchPlayerData() {
    const playerAbbreviation = document.getElementById('player-select').value;
    if (playerAbbreviation) {
        fetch(`/get_player/${playerAbbreviation}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Fehler beim Abrufen der Spielerdaten');
                }
                return response.json();
            })
            .then(playerData => {
                displayPlayerData(playerData);
            })
            .catch(error => {
                console.error('Fehler:', error);
            });
    }
}

function displayPlayerData(playerData) {
    document.getElementById('player-name').textContent = playerData.player_info.name || '';
    document.getElementById('player-abbreviation').textContent = playerData.player_info.abbreviation || '';
    document.getElementById('played-dates').textContent = 'Gespielte Tage: ' + playerData.played_dates;

    const notPlayedMachinesDiv = document.getElementById('not-played-machines');
    notPlayedMachinesDiv.innerHTML = '<h4>Nicht gespielte Maschinen:</h4>';

    playerData.not_played_machines.forEach(abbreviation => {
        const machine = allPinballMachines.find(m => m.abbreviation === abbreviation);
        const machineName = machine ? machine.long_name : 'Unbekannte Maschine';
        const p = document.createElement('p');
        p.textContent = machineName;
        notPlayedMachinesDiv.appendChild(p);
    });
}
