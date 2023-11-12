document.addEventListener('DOMContentLoaded', function() {
    loadPlayers();
    loadData();
    setInterval(loadData, 60000); // Aktualisiert die Daten jede Minute
});

let playerNamesMap = {};


function loadPlayers() {
    fetch('/players')
        .then(response => response.json())
        .then(players => {
            playerNamesMap = players.reduce((map, player) => {
                map[player.abbreviation] = player.name;
                return map;
            }, {});
        });
}

function loadData() {
    fetchTotalHighscores();
    fetchPinballHighscores();
}


function fetchTotalHighscores() {
    fetch('/total_highscore')
        .then(response => response.json())
        .then(data => displayTotalHighscores(data));
}

function displayTotalHighscores(data) {
    const table = document.getElementById('total-highscore-list');
    const tbody = document.createElement('tbody');
    table.classList.add('table-highscores');

    data.forEach(item => {
        const playerName = playerNamesMap[item.player] || item.player; // Vollständigen Namen verwenden
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.rank}</td>
            <td>${playerName}</td>
            <td>${item.total_points.toLocaleString()}</td>
        `;
        tbody.appendChild(row);
    });

    // Löschen des alten Inhalts der Tabelle und Hinzufügen des neuen tbody
//    table.innerHTML = `
//        <thead>
//            <tr>
//                <th>#</th>
//                <th>Player</th>
//                <th>Points</th>x
//            </tr>
//        </thead>
//    `;
    table.appendChild(tbody);
}


function fetchPinballHighscores() {
    fetch('/pinball')
        .then(response => response.json())
        .then(pinballMachines => {
            // Sortieren der Flipperautomaten alphabetisch nach ihrem langen Namen
            pinballMachines.sort((a, b) => a.long_name.localeCompare(b.long_name));

            // Leeren des Containers für die Highscores der Flipperautomaten
            const container = document.getElementById('pinball-highscore-content');
            container.innerHTML = '';

            // Highscores für jeden Flipperautomaten abrufen
            pinballMachines.forEach(machine => {
                fetch(`/highscore/pinball/${machine.abbreviation}`)
                    .then(response => response.json())
                    .then(highscores => {
                        displayPinballHighscores(machine, highscores);
                    });
            });
        });
}

function displayPinballHighscores(machine, highscores) {
    const container = document.getElementById('pinball-highscore-content');
    const section = document.createElement('section');
    section.innerHTML = `<h3>${machine.long_name}</h3>`;
    const table = document.createElement('table');
    table.classList.add('table-highscores');

    const tbody = document.createElement('tbody');
    const today = new Date().toISOString().split('T')[0]; // Heutiges Datum im Format YYYY-MM-DD

    highscores.slice(0, 15).forEach((score, index) => {
        const playerName = playerNamesMap[score.player] || score.player;
        const row = document.createElement('tr');

        // Umwandeln des Spielstanddatums in das Format YYYY-MM-DD für den Vergleich
        const today = new Date().toISOString().split('T')[0];

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${playerName}</td>
            <td>${score.score.toLocaleString()}</td>
        `;
        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    section.appendChild(table);
    container.appendChild(section);
}

