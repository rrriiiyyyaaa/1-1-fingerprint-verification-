import webbrowser
import threading
import time
import shutil
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
import requests
import base64
import cv2
import numpy as np
import hashlib
import torch
from PIL import Image
import torchvision.transforms as T

DATABASE_DIR = Path("database")

def get_folder_id(user_id):

    return hashlib.sha256(
        user_id.encode()
    ).hexdigest()


def open_browser():

    time.sleep(1)

    webbrowser.open(
        "http://127.0.0.1:8000"
    )

threading.Thread(
    target=open_browser
).start()

app = FastAPI()


# ---------------------------------
# LOAD MODEL
# ---------------------------------

from flx.models.deep_print_arch import DeepPrint_TexMinu

device = torch.device("cpu")

# fixed seed for deterministic weight init
# (ensures filtered-out logits layers are
#  identical across restarts)
torch.manual_seed(42)

model = DeepPrint_TexMinu(
    num_fingerprints=1000,
    texture_embedding_dims=256,
    minutia_embedding_dims=256
).to(device)

ckpt = torch.load(
    "models/fine tuned model/best_model_lr0.025.pyt",
    map_location=device
)

state_dict = ckpt.get(
    "model_state_dict",
    ckpt
)

filtered_state = {
    k: v for k, v in state_dict.items()
    if not (
        k.startswith("texture_logits")
        or
        k.startswith("minutia_logits")
    )
}

result = model.load_state_dict(
    filtered_state,
    strict=False
)

if result.missing_keys:
    print("MISSING KEYS:", result.missing_keys)

if result.unexpected_keys:
    print("UNEXPECTED KEYS:", result.unexpected_keys)

model.eval()

print("DeepPrint model loaded")

SCANNER_URL = "http://127.0.0.1:5220/capture"


def capture_fingerprint():

    try:

        response = requests.get(
            SCANNER_URL,
            timeout=5
        )

        data = response.json()

        return data

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

transform = T.Compose([
    T.Resize((299, 299)),
    T.ToTensor()
])


def get_embedding_from_base64(base64_string):

    image_bytes = base64.b64decode(base64_string)

    np_array = np.frombuffer(
        image_bytes,
        np.uint8
    )

    img = cv2.imdecode(
        np_array,
        cv2.IMREAD_GRAYSCALE
    )

    pil_img = Image.fromarray(img)

    x = transform(pil_img).unsqueeze(0).to(device)


    # avoid squeeze issue
    x = x.repeat(2,1,1,1)

    with torch.no_grad():

        out = model(x)

        tex = out.texture_embeddings
        minu = out.minutia_embeddings

        emb = torch.cat(
            [tex, minu],
            dim=1
        )

    return emb[0].cpu().numpy()    

BASE_DIR = Path(__file__).parent

templates_dir = BASE_DIR / "templates"



# ---------------------------------
# SAVE EMBEDDING
# ---------------------------------
# ---------------------------------
# SAVE TEMP EMBEDDING
# ---------------------------------

TEMP_DIR = Path("temp")

DATABASE_DIR = Path("database")


def save_embedding(
    user_id,
    embedding,
    sample_no
):

    folder_id = get_folder_id(user_id)

    user_temp_dir = TEMP_DIR / folder_id

    user_temp_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    save_path = (
        user_temp_dir /
        f"sample_{sample_no}.npy"
    )

    np.save(
        save_path,
        embedding
    )

    return str(save_path)

# ---------------------------------
# LOAD ENROLLED EMBEDDINGS
# ---------------------------------

def load_user_embeddings(user_id):

    folder_id = get_folder_id(user_id)

    user_dir = DATABASE_DIR / folder_id

    if not user_dir.exists():

        return None

    embeddings = []

    for i in range(1, 7):

        file_path = (
            user_dir /
            f"sample_{i}.npy"
        )

        if not file_path.exists():

            return None

        emb = np.load(file_path)

        embeddings.append(emb)

    return embeddings


# ---------------------------------
# FINALIZE ENROLLMENT
# ---------------------------------

def finalize_enrollment(user_id):

    folder_id = get_folder_id(user_id)

    temp_user_dir = TEMP_DIR / folder_id

    final_user_dir = DATABASE_DIR / folder_id

    # existing enrolled user
    if final_user_dir.exists():

        raise Exception(
            "User ID already enrolled"
        )

    shutil.move(
        str(temp_user_dir),
        str(final_user_dir)
    )

# ---------------------------------
# CLEAR TEMP ENROLLMENT
# ---------------------------------

def clear_temp_enrollment(user_id):

    folder_id = get_folder_id(user_id)

    temp_user_dir = TEMP_DIR / folder_id

    if temp_user_dir.exists():

        shutil.rmtree(temp_user_dir)


# -----------------------------
# HOME
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def home():

    return """
    <html>

    <head>
        <title>Fingerprint System</title>
    </head>

    <body style="
        font-family:Arial;
        text-align:center;
        margin-top:80px;
    ">

        <h1>
            Fingerprint Authentication System
        </h1>

        <br>

        <a href="/enroll">
            <button style="
                padding:15px;
                width:220px;
                font-size:18px;
            ">
                Enrollment
            </button>
        </a>

        <br><br>

        <a href="/verify">
            <button style="
                padding:15px;
                width:220px;
                font-size:18px;
            ">
                Verification
            </button>
        </a>

    </body>

    </html>
    """


# -----------------------------
# ENROLL PAGE
# -----------------------------

@app.get("/enroll", response_class=HTMLResponse)
def enroll_page():

    file = templates_dir / "enroll.html"

    if file.exists():
        return file.read_text()

    return "<h1>enroll.html not found</h1>"


# -----------------------------
# VERIFY PAGE
# -----------------------------

@app.get("/verify", response_class=HTMLResponse)
def verify_page():

    file = templates_dir / "verify.html"

    if file.exists():
        return file.read_text()

    return "<h1>verify.html not found</h1>"


@app.get("/test-capture")
def test_capture():

    data = capture_fingerprint()

    if not data["success"]:
        return data

    embedding = get_embedding_from_base64(
        data["image"]
    )

    return {
        "success": True,
        "quality": data["quality"],
        "embedding_shape": embedding.shape[0]
    }

@app.get("/api/enroll")
def enroll(user_id: str, sample_no: int):

    folder_id = get_folder_id(user_id)

    final_user_dir = DATABASE_DIR / folder_id

    if final_user_dir.exists():

        return {
            "success": False,
            "message": "User ID already enrolled"
        }

    # 6 samples
    if sample_no < 1 or sample_no > 6:

        return {
            "success": False,
            "message": "Invalid sample number"
        }

    # capture fingerprint
    data = capture_fingerprint()

    # timeout / failure
    if not data["success"]:
        return data

    try:

        # generate embedding
        embedding = get_embedding_from_base64(
            data["image"]
        )

        # save embedding
        save_path = save_embedding(
            user_id,
            embedding,
            sample_no
        )

        # finalize after sample 6
        if sample_no == 6:
            finalize_enrollment(user_id)


        return {
            "success": True,
            "quality": data["quality"],
            "sample_no": sample_no,
            "saved_to": save_path
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }
    

# ---------------------------------
# COSINE SIMILARITY
# ---------------------------------

def cosine_similarity(a, b):

    return float(
        np.dot(a, b)
        /
        (
            np.linalg.norm(a)
            *
            np.linalg.norm(b)
            + 1e-9
        )
    )


# ---------------------------------
# VERIFY API
# ---------------------------------

@app.get("/api/verify")
def verify(user_id: str):

    # user exists?
    stored_embeddings = load_user_embeddings(
        user_id
    )

    if stored_embeddings is None:

        return {
            "success": False,
            "message": "User not enrolled"
        }

    # capture fingerprint
    data = capture_fingerprint()

    if not data["success"]:

        return data

    try:

        # live embedding
        live_embedding = (
            get_embedding_from_base64(
                data["image"]
            )
        )


        match_count = 0

        max_score = 0.0

        for emb in stored_embeddings:

            score = cosine_similarity(
                live_embedding,
                emb
            )

            print("Similarity:", score)

            if score >= 0.75:

                match_count += 1

            if score > max_score:

                max_score = score

        # final decision
        auth_success = (
            match_count >= 4
        )

        return {
            "success": True,
            "max_score": round(max_score, 4),
            "match_count": match_count,
            "authenticated": auth_success,
            "message":
                "AUTH SUCCESS"
                if auth_success
                else
                "AUTH FAILED"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }