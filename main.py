import os
import random

from dotenv import load_dotenv
import requests


def delete_png(comic_title):
    folder = os.listdir(".")

    for file in folder:
        if file == comic_title:
            os.remove(os.path.join(".", file))
            break


def get_comix_url():
    response = requests.get("https://xkcd.com/info.0.json")
    response.raise_for_status()

    id_last_comic = response.json()["num"]
    random_id = random.randint(1, id_last_comic)
    comix_url = f"http://xkcd.com/{random_id}/info.0.json"

    return comix_url


def post_comic(vk_access_token, group_id, album_comic, comment):
    owner_id = album_comic["response"][0]["owner_id"]
    media_id = album_comic["response"][0]["id"]
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


def save_comic_in_album(comic_json, group_id, vk_access_token):
    method_name = "photos.saveWallPhoto"
    params = {
        "server": comic_json["server"],
        "photo": comic_json["photo"],
        "hash": comic_json["hash"],
        "group_id": group_id,
        "access_token": vk_access_token,
        "v": "5.131"
    }
    response = requests.post(
        f"https://api.vk.com/method/{method_name}", params=params
    )

    response.raise_for_status()
    return response


def upload_comic_to_server(comic_title, upload_url):
    with open(comic_title, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
    response.raise_for_status()

    return response.json()


def get_adress(vk_access_token, group_id):
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
    upload_url = response.json()["response"]["upload_url"]

    return upload_url


def download_picture(json_response, comic_title):
    img_url = json_response["img"]
    img = requests.get(img_url)

    with open(comic_title, "wb") as file:
        file.write(img.content)


def download_comic(url):
    response = requests.get(url)
    response.raise_for_status()
    json_response = response.json()

    comic_comment = json_response["alt"]
    comic_title = f'{json_response["title"]}.png'

    download_picture(json_response, comic_title)

    return comic_title, comic_comment


def main():
    load_dotenv()
    vk_access_token = os.getenv("VK_ACCESS_TOKEN")
    group_id = os.getenv("GROUP_ID")
    try:
        url = get_comix_url()
        comic_title, comic_comment = download_comic(url)
        upload_url = get_adress(vk_access_token, group_id)
        comic_json = upload_comic_to_server(comic_title, upload_url)
        album_comic = save_comic_in_album(
            comic_json, group_id, vk_access_token)
        # post_comic(vk_access_token, group_id, album_comic.json(), comic_comment)

    except requests.exceptions.HTTPError as exception:
        print(exception)
    finally:
        delete_png(comic_title)


if __name__ == "__main__":
    main()
