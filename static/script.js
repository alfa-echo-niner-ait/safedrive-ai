const video = document.getElementById("video");
const earDisplay = document.getElementById("earValue");
const statusDisplay = document.getElementById("status");
const alertBox = document.getElementById("alert");
const alarmSound = document.getElementById("alarm");

// Check camera support
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
	alert("❌ Camera not supported in this browser.");
	console.error("navigator.mediaDevices not available");
} else {
	navigator.mediaDevices
		.getUserMedia({ video: { facingMode: "user" } })
		.then((stream) => {
			video.srcObject = stream;
			console.log("✅ Camera access granted!");
		})
		.catch((err) => {
			alert("❌ Camera access denied or not supported");
			console.error("Camera error:", err);
		});
}

// Send frames to Flask every 200ms (~5 FPS)
setInterval(() => {
	if (!video.srcObject) return;

	const canvas = document.createElement("canvas");
	canvas.width = video.videoWidth;
	canvas.height = video.videoHeight;
	const ctx = canvas.getContext("2d");
	ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

	// Convert to Base64
	const imageDataURL = canvas.toDataURL("image/jpeg", 0.5);

	fetch("/process_frame", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ image: imageDataURL }),
	})
		.then((res) => res.json())
		.then((data) => {
			if (data.error) {
				console.error("Server error:", data.error);
				return;
			}

			earDisplay.textContent = data.ear || "--";
			statusDisplay.textContent = data.is_drowsy ? "Drowsy" : "Awake";

			if (data.is_drowsy) {
				alertBox.style.display = "block";
				try {
					alarmSound.currentTime = 0;
					alarmSound.play();
				} catch (e) {
					console.log("Audio play failed", e);
				}
			} else {
				alertBox.style.display = "none";
			}
		});
}, 200); // Every 200ms
