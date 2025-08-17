var audio = document.getElementById("sample");
var audio_source = document.getElementById("sample_src");
var playButton = document.getElementById("playButton");
var pauseButton = document.getElementById("pauseButton");


function playAudio() {
    audio.play();
}

function pauseAudio() {
    audio.pause();
}

audio.addEventListener("play", function (){
    playButton.disabled = true;
    pauseButton.disabled = false;
})

audio.addEventListener("pause", function (){
    playButton.disabled = false;
    pauseButton.disabled = true;
})

audio.addEventListener("ended", function(){
    audio.currentTime = 0;
    playButton.disabled = false;
    pauseButton.disabled = true;
});
