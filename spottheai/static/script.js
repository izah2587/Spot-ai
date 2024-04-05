function joinGame() {
    var name = document.getElementById('username').value;
    var gameCode = document.getElementById('gameCode').value;
    // Make sure the name and game code are not empty
    if (name && gameCode) {
        // Create a form element and submit it to follow the redirect
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/join';

        var nameInput = document.createElement('input');
        nameInput.type = 'hidden';
        nameInput.name = 'name';
        nameInput.value = name;

        var codeInput = document.createElement('input');
        codeInput.type = 'hidden';
        codeInput.name = 'game_code';
        codeInput.value = gameCode;

        form.appendChild(nameInput);
        form.appendChild(codeInput);

        document.body.appendChild(form);
        form.submit();
    } else {
        alert('Please enter your name and game code.');
    }
}


function hostGame() {
    var name = document.getElementById('username').value;
    if (name) {
        // Create a form element and submit it to follow the redirect
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/host';

        var nameInput = document.createElement('input');
        nameInput.type = 'hidden';
        nameInput.name = 'name';
        nameInput.value = name;

        form.appendChild(nameInput);
        document.body.appendChild(form);
        form.submit();
    } else {
        alert('Please enter your name.');
    }
}

setInterval(function() {
    fetch('/game_status/' + gameCode)
        .then(response => response.json())
        .then(data => {
            if (data.game_status === 'in_progress') {
                window.location.href = '/play_game/' + gameCode; // Redirect to game page
            }
        });
}, 3000); // Check every 3 seconds