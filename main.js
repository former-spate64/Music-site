const song_name = document.getElementById("songname");
const song_artist = document.getElementById("songartist");
const allAudio = document.querySelectorAll('audio');
const Audio1 = document.getElementById("song1");
const Audio2 = document.getElementById("song2");
const Audio3 = document.getElementById("song3");
const Audio4 = document.getElementById("song4");
const Audio5 = document.getElementById("song5");
const Audio6 = document.getElementById("song6");
const Audio7 = document.getElementById("song7");
const Audio8 = document.getElementById("song8");
const Audio9 = document.getElementById("song9");
const Audio0 = document.getElementById("song0");
const backbutton = document.getElementById("backbutton");
const pausebutton = document.getElementById("pausebutton");
const skipbutton = document.getElementById("skipbutton");
const closebutton = document.getElementById("closebutton");
const profilebutton = document.getElementById("ProfileButton");
const container1 = document.getElementById("container1");
const box1 = document.getElementById("box1");
const box2 = document.getElementById("box2");
const box3 = document.getElementById("box3");
const box4 = document.getElementById("box4");
const box5 = document.getElementById("box5");
const profile = document.getElementById("profile");
const searchBox = document.getElementById("searchBox");
let State = false;
let profileState = false;
let music_state = false;
let current_song = null;
closebutton.addEventListener("click", function() {
    if (State === false) {
        container1.style.transition = "left 0.3s ease";
        container1.style.left = "-15%";
        box1.style.transition = "left 0.3s ease";
        box1.style.left = "-10.25%";
        box2.style.transition = "left 0.3s ease";
        box2.style.left = "-15%";
        box3.style.transition = "left 0.3s ease";
        box3.style.left = "-15%";
        box4.style.transition = "left 0.3s ease";
        box4.style.left = "-15%";
        box5.style.transition = "left 0.3s ease";
        box5.style.left = "-15%";
        searchBox.style.transition = "transform 0.3s ease";
        searchBox.style.transform = "translateX(-7.55%) scaleX(1.15)";
        State = true;
        return;
    }
    if (State === true) {
        container1.style.transition = "left 0.3s ease";
        container1.style.left = "0%";
        box1.style.transition = "left 0.3s ease";
        box1.style.left = "0%";
        box2.style.transition = "left 0.3s ease";
        box2.style.left = "0%";
        box3.style.transition = "left 0.3s ease";
        box3.style.left = "0%";
        box4.style.transition = "left 0.3s ease";
        box4.style.left = "0%";
        box5.style.transition = "left 0.3s ease";
        box5.style.left = "0%";
        searchBox.style.transition = "transform 0.3s ease";
        searchBox.style.transform = "translateX(0%) scaleX(1)";
        State = false;
    }
});
profilebutton.addEventListener("click", function() {
    if (profileState === false) {
        profileState = true;
        profile.style.transition = "right 0.3s ease";
        profile.style.right = "0.7%";
    } else if (profileState === true) {     
        profileState = false;
        profile.style.transition = "right 0.3s ease";
        profile.style.right = "-4.5%";
    }
})
document.addEventListener("keypress", function (event) {
    if (event.key === " ") {
    pausebutton.click();
    }});
document.addEventListener("keypress", function (event) {
    if (event.key === "k") {
    pausebutton.click();
    }});
document.addEventListener("keypress", function (event) {
    if (event.key === "l") {
    skipbutton.click();
    }});
document.addEventListener("keypress", function (event) {
    if (event.key === "j") {
    backbutton.click();
    }});
document.addEventListener("keypress", function (event) {
    if (event.key === "1") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio1.play();
    music_state = true;
    current_song = Audio1;
    showText(1);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "2") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio2.play();
    music_state = true;
    current_song = Audio2;
    showText(2);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "3") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio3.play();
    music_state = true;
    current_song = Audio3;
    showText(3);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "4") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio4.play();
    music_state = true;
    current_song = Audio4;
    showText(4);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "5") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio5.play();
    music_state = true;
    current_song = Audio5;
    showText(5);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "6") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio6.play();
    music_state = true;
    current_song = Audio6;
    showText(6);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "7") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio7.play();
    music_state = true;
    current_song = Audio7;
    showText(7);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "8") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio8.play();
    music_state = true;
    current_song = Audio8;
    showText(8);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "9") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio9.play();
    music_state = true;
    current_song = Audio9;
    showText(9);
    })}});
document.addEventListener("keypress", function (event) {
    if (event.key === "0") {
    allAudio.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    Audio0.play();
    music_state = true;
    current_song = Audio0;
    showText(10);
    })}});
backbutton.addEventListener("click", function() {
current_song.currentTime = 0;
});
pausebutton.addEventListener("click", function() {
if (music_state === true) {
current_song.pause();
music_state = false;
} else {
current_song.play();
music_state = true;
}
});
skipbutton.addEventListener("click", function() {

});


async function showText(number) {
    if (number === 1) {
        song_name.innerHTML = "Lime coconut";
        song_artist.innerHTML = "Harry Nilsson";
    }
    if (number === 2) {
        song_name.innerHTML = "Don't forget your roots";
        song_artist.innerHTML = "Six60";
    }
    if (number === 3) {
        song_name.innerHTML = "24/7";
        song_artist.innerHTML = "Common Kings";
    }
    if (number === 4) {
        song_name.innerHTML = "Take it away";
        song_artist.innerHTML = "L.A.B";
    }
    if (number === 5) {
        song_name.innerHTML = "Bills";
        song_artist.innerHTML = "LunchMoney Lewis";
    }
    if (number === 6) {
        song_name.innerHTML = "Cool it down";
        song_artist.innerHTML = "Coolio";
    }
    if (number === 7) {
        song_name.innerHTML = "Everybody have fun tonight";
        song_artist.innerHTML = "Wang Chung";
    }
    if (number === 8) {
        song_name.innerHTML = "Go your own way";
        song_artist.innerHTML = "Fleetwood Mac";
    }
    if (number === 9) {
        song_name.innerHTML = "Aye como va";
        song_artist.innerHTML = "Santana";
    }
    if (number === 10) {
        song_name.innerHTML = "Overpass graffiti";
        song_artist.innerHTML = "Ed Sheeran";
    }
}