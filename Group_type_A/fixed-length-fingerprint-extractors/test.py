import numpy as np
import os

folder = "82f3e9c695dc6b8d1b11818d5701919e286de8d47f7c3eb3100c485f79e57828"

for i in range(1, 7):
    x = np.load(f"database/{folder}/sample_{i}.npy")

    print(f"\nSample {i}")
    print(x[:10])
    