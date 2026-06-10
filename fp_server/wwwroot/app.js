// ======================================
// Capture fingerprint from C# server
// ======================================

async function captureFingerprint() {

    let response = await fetch(
        "http://localhost:5220/capture?FingerID=temp"
    );

    let data = await response.json();

    if (!data.image) {
        throw new Error("No image received");
    }

    return data.image;
}


// ======================================
// ENROLL
// ======================================

async function enrollFingerprint() {

    let userId = document.getElementById("userId").value;

    if (!userId) {
        alert("Enter User ID");
        return;
    }

    document.getElementById("status").innerText =
        "Capturing fingerprint...";

    try {

        // capture
        let base64img = await captureFingerprint();

        // show image
        document.getElementById("fingerImage").src =
            "data:image/bmp;base64," + base64img;

        // convert base64 → blob
        let blob = await fetch(
            "data:image/bmp;base64," + base64img
        ).then(r => r.blob());

        let formData = new FormData();
        formData.append("file", blob, "finger.png");
        formData.append("user_id", userId);

        // send to FastAPI
        let response = await fetch(
            "http://127.0.0.1:8000/enroll",
            {
                method: "POST",
                body: formData
            }
        );

        let result = await response.json();

        document.getElementById("status").innerText =
            JSON.stringify(result);

    }
    catch (err) {

        console.error(err);

        document.getElementById("status").innerText =
            "Enrollment failed";

    }
}


// ======================================
// VERIFY
// ======================================

async function verifyFingerprint() {

    document.getElementById("status").innerText =
        "Capturing fingerprint...";

    try {

        // capture
        let base64img = await captureFingerprint();

        // show image
        document.getElementById("fingerImage").src =
            "data:image/bmp;base64," + base64img;

        // convert to blob
        let blob = await fetch(
            "data:image/bmp;base64," + base64img
        ).then(r => r.blob());

        let formData = new FormData();
        formData.append("file", blob, "finger.bmp");

        // call FastAPI
        let response = await fetch(
            "http://127.0.0.1:8000/verify",
            {
                method: "POST",
                body: formData
            }
        );

        let result = await response.json();

        console.log(result);

        if (result.result.status === "AUTHENTICATED") {

            document.getElementById("result").innerText =
                "✅ AUTHENTICATED";

            document.getElementById("result").style.color =
                "lime";

        }
        else {

            document.getElementById("result").innerText =
                "❌ REJECTED";

            document.getElementById("result").style.color =
                "red";
        }

        document.getElementById("status").innerText =
            "User: " + result.result.user +
            " | Score: " + result.result.score.toFixed(3);

    }
    catch (err) {

        console.error(err);

        document.getElementById("status").innerText =
            "Verification failed";

    }
}