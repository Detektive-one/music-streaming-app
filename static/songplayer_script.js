var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function(event) {
    event.preventDefault(); 
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}


var audio = document.getElementById('audio');
var playPauseBtn = document.getElementById('play-pause-btn');
var stopBtn = document.getElementById('stop-btn');
var volumeControl = document.getElementById('volume-control');
var progressBar = document.getElementById('progress-bar');
var timeDisplay = document.getElementById('time-display');

playPauseBtn.addEventListener('click', function() {
    if (audio.paused) {
        audio.play();
        playPauseBtn.classList.add('playing');
    } else {
        audio.pause();
        playPauseBtn.classList.remove('playing');
    }
});

stopBtn.addEventListener('click', function() {
    audio.pause();
    audio.currentTime = 0;
    playPauseBtn.classList.remove('playing');
});

volumeControl.addEventListener('input', function() {
    audio.volume = volumeControl.value;
    timeDisplay.innerText = formatTime(audio.currentTime) + ' / ' + formatTime(audio.duration);
});

progressBar.addEventListener('click', function(event) {
    var clickPosition = event.clientX - progressBar.getBoundingClientRect().left;
    var newProgress = (clickPosition / progressBar.offsetWidth) * 100;
    progressBar.querySelector('.progress').style.width = newProgress + '%';
    audio.currentTime = (newProgress / 100) * audio.duration;
});

audio.addEventListener('timeupdate', function() {
    var progress = (audio.currentTime / audio.duration) * 100;
    progressBar.querySelector('.progress').style.width = progress + '%';
    timeDisplay.innerText = formatTime(audio.currentTime) + ' / ' + formatTime(audio.duration);
});

function formatTime(time) {
    var minutes = Math.floor(time / 60);
    var seconds = Math.floor(time % 60);
    return (minutes < 10 ? '0' : '') + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
}

