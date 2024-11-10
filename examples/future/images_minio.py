from PIL import Image
import os

import ell
from ell.stores.minio import MinioBlobStore, MinioConfig
from ell.stores.sql import PostgresStore


# Load the image using PIL
big_picture = Image.open(os.path.join(os.path.dirname(__file__), "bigpicture.jpg"))

@ell.simple(model="gpt-4o", temperature=0.5)
def make_a_joke_about_the_image(image: Image.Image):
    return [
        ell.system("You are a meme maker. You are given an image and you must make a joke about it."),
        ell.user(image)
    ]



if __name__ == "__main__":
    # Run "docker compose up" inside the `docker` folder to run
    # ell studio with minio for blob storage with postgres
    blob_store = MinioBlobStore(
        config=MinioConfig(
            endpoint="localhost:9000",
            access_key="minio_user",
            secret_key="minio_password",
            bucket="ell-bucket",
        )
    )
    store = PostgresStore(
        db_uri="postgresql://ell_user:ell_password@localhost:5432/ell_db",
        blob_store=blob_store,
    )
    ell.init(store=store, autocommit=True, verbose=True)
    joke = make_a_joke_about_the_image(big_picture)
    print(joke)