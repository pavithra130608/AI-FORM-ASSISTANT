import subprocess
import os

def pdf_to_image(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    out_prefix = os.path.join(output_dir, base)

    cmd = [
        "pdftoppm",
        "-r", "300",
        "-png",
        pdf_path,
        out_prefix
    ]

    subprocess.run(cmd, check=True)

    return sorted([
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.startswith(base) and f.endswith(".png")
    ])
