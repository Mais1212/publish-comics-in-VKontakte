import os
import random

import requests

from dotenv import load_dotenv


def raise_for_vk_status(response):
    if "error" in response.text:
        raise requests.HTTPError(response.json()["error"]["error_msg"])


def get_random_comic_url():
    response = requests.get("https://xkcd.com/info.0.json")
    
    response.raise_for_status()
    raise_for_vk_status(response)

    last_comic_id = response.json()["num"]
    random_id = random.randint(1, last_comic_id)
    comix_url = f"http://xkcd.com/{random_id}/info.0.json"

    return comix_url


def post_comic(vk_access_token, group_id, comment, owner_id, media_id):
    method_name = "wall.post"
    attachments = f"photo{owner_id}_{media_id}"
    params = {
        "attachments": attachments,
        "message": comment,
        "owner_id": f"-{group_id}",
        "access_token": vk_access_token,
        "v": "5.131"
    }

    response = requests.post(
        f"https://api.vk.com/method/{method_name}", params=params
    )
    
    response.raise_for_status()
    raise_for_vk_status(response)


def save_comic_in_album(server, photo, image_hash, group_id, vk_access_token):
    method_name = "photos.saveWallPhoto"
    params = {
        "server": server,
        "photo": photo,
        "hash": image_hash,
        "group_id": group_id,
        "access_token": vk_access_token,
        "v": "5.131"
    }
    response = requests.post(
        f"https://api.vk.com/method/{method_name}", params=params
    )
    
    response.raise_for_status()
    raise_for_vk_status(response)
    response = response.json()

    owner_id = response["response"][0]["owner_id"]
    media_id = response["response"][0]["id"]
    return owner_id, media_id


def upload_comic_to_server(comic_title, upload_url):
    with open(comic_title, "rb") as file:
        files = {
            "photo": file,
        }
        response = requests.post(upload_url, files=files)
    
    response.raise_for_status()
    raise_for_vk_status(response)
    response = response.json()

    server = response["server"]
    photo = response["photo"]
    image_hash = response["hash"]

    return server, photo, image_hash


def get_address(vk_access_token, group_id):
    method_name = "photos.getWallUploadServer"
    params = {
        "access_token": vk_access_token,
        "v": "5.131",
        "group_id": group_id
    }
    response = requests.get(
        f"https://api.vk.com/method/{method_name}", params=params
    )
    
    response.raise_for_status()
    raise_for_vk_status(response)
    upload_url = response.json()["response"]["upload_url"]

    return upload_url


def download_picture(response, comic_title):
    img_url = response["img"]
    img = requests.get(img_url)

    img.raise_for_status()
    raise_for_vk_status(img)

    with open(comic_title, "wb") as file:
        file.write(img.content)


def download_comic(url):
    response = requests.get(url)
    
    response.raise_for_status()
    raise_for_vk_status(response)
    response = response.json()

    comic_comment = response["alt"]
    comic_title = f"{response['title']}.png"

    download_picture(response, comic_title)

    return comic_title, comic_comment


def main():
    load_dotenv()
    vk_access_token = os.getenv("VK_ACCESS_TOKEN")
    group_id = os.getenv("GROUP_ID")
    try:
        url = get_random_comic_url()
        comic_title, comic_comment = download_comic(url)
        upload_url = get_address(vk_access_token, group_id)

        server, photo, image_hash = upload_comic_to_server(
            comic_title, upload_url)

        owner_id, media_id = save_comic_in_album(
            server, photo, image_hash, group_id, vk_access_token)

        post_comic(vk_access_token, group_id,
                   comic_comment, owner_id, media_id)

    except requests.exceptions.HTTPError as exception:
        print(exception)
    finally:
        os.remove(os.path.join(".", comic_title))




if __name__ == "__main__":
    main()
