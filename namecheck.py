import asyncio
import csv
import io
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

import aiohttp
from termcolor import colored


def read_json(filename):
    """read json file to dict"""
    data = {}
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        pass
    return data


def bool_to_color(flag: bool):
    """return color refered to flag"""
    if flag:
        return "cyan"
    return "red"


def user_exist_status(response_status, response_text, pattern_ok, pattern_nok):
    """
    asyncio:
        response.status_code -> response.status
        response.text -> await response.text()
    """
    if pattern_ok:
        if (response_status == 200) and pattern_ok in response_text:
            user_exist = True
        else:
            user_exist = False
    elif pattern_nok:
        if (response_status == 200) and pattern_nok in response_text:
            user_exist = False
        else:
            user_exist = True
    else:
        if response_status == 200:
            user_exist = True
        else:
            user_exist = False
    return user_exist


async def request_user_exist(
    *, session, key, url, pattern_ok, pattern_nok, allow_redirects, custom_user_agent
):
    """make asyncio request"""
    try:
        if custom_user_agent:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
            headers = {"User-Agent": user_agent}
        else:
            headers = None
        async with session.get(
            url, headers=headers, allow_redirects=allow_redirects, timeout=10
        ) as response:
            response_status = response.status
            if pattern_ok or pattern_nok:
                response_text = await response.text()
            else:
                response_text = ""
            user_exist = user_exist_status(
                response_status, response_text, pattern_ok, pattern_nok
            )
            # print(colored('[*] done for url: {}'.format(url), 'green') + colored(' (allow_redirects={})'.format(allow_redirects), bool_to_color(allow_redirects)))
            return (key, url, user_exist)

    except UnicodeDecodeError as err:
        # print(colored('[x] error catched: {}'.format(err), 'red'))
        return (key, url, None)

    except aiohttp.client_exceptions.ClientConnectorCertificateError as err:
        # print(colored('[x] error catched: {}'.format(err), 'red'))
        return (key, url, None)

    except aiohttp.client_exceptions.ClientConnectorError as err:
        # print(colored('[x] error catched: {}'.format(err), 'red'))
        return (key, url, None)

    except asyncio.exceptions.TimeoutError as err:
        # print(colored('[x] error catched: {}'.format(err), 'red'))
        return (key, url, None)


async def main(namecheck_urls, username):
    """create ascyncio tasks"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, (key, item) in enumerate(namecheck_urls.items()):
            url_encoded_username = urllib.parse.quote(username.encode("utf8"))
            url = item["url"].format(username=url_encoded_username)
            pattern_ok = item["pattern_ok"].format(username=username)
            pattern_nok = item["pattern_nok"].format(username=username)
            allow_redirects = item.get("allow_redirects", True)
            custom_user_agent = item.get("custom_user_agent", False)
            tasks.append(
                asyncio.ensure_future(
                    request_user_exist(
                        session=session,
                        key=key,
                        url=url,
                        pattern_ok=pattern_ok,
                        pattern_nok=pattern_nok,
                        allow_redirects=allow_redirects,
                        custom_user_agent=custom_user_agent,
                    )
                )
            )
        return await asyncio.gather(*tasks)


def filter_urls(namecheck_urls: dict, to_filter: list):
    """to_filter: list or tuple of urls"""
    namecheck_urls = {
        key: value for key, value in namecheck_urls.items() if key in to_filter
    }
    return namecheck_urls


def run_main(namecheck_urls: dict, username: str):
    """
    fix for <RuntimeError: Event loop is closed> error:
        https://stackoverflow.com/questions/45600579/asyncio-event-loop-is-closed-when-getting-loop
    https://stackoverflow.com/questions/48604341/what-is-event-loop-policy-and-why-is-it-needed-in-python-asyncio
    help(asyncio.get_event_loop_policy())
    """
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    response_values = asyncio.run(main(namecheck_urls, username))
    return response_values


if __name__ == "__main__":
    # ****** setup ******
    os.chdir(str(Path(sys.argv[0]).parent))
    if os.name == "nt":
        os.system("color")
    start_time = time.time()

    # ****** args ******
    args = sys.argv[1:]
    if not args:
        print("[*] usage:")
        print(colored("    python namecheck.py <username>", "cyan"))
        print(colored('        --csv    -output in csv format', "cyan"))
        sys.exit()
    if '--csv' in args:
        csv_mode = True
    else:
        csv_mode = False
    username = args[0]
    if not csv_mode:
        print("[*] username: {}".format(colored(username, "cyan")))

    # ****** collect urls & run main ******
    namecheck_urls = read_json("namecheck_urls.json")
    response_values = run_main(namecheck_urls, username)

    # ****** print output ******
    if csv_mode:
        rows = [[index+1, row[1], row[0], row[2]] for index, row in enumerate(response_values)]
        output = io.StringIO()
        writer = csv.writer(output)
        for row in rows:
            writer.writerow(row)
        csv_str = output.getvalue()
        print(csv_str)
    else:
        print()
        for index, (key, url, user_exist) in enumerate(response_values):
            if user_exist is None:
                color = "red"  # error
                result = 'Failed to check'
            elif user_exist:
                color = "green"
                result = 'User exists'
            else:
                color = "yellow"
                result = 'User not found'
            # print(colored("{:02}) {}".format(index + 1, (key, url, user_exist)), color))
            print(colored("{:02}) {} ({}) -> {}".format(index+1, url, key, result), color))
        print(colored("\n[*] total time: {:.2f} [s]".format(time.time() - start_time), 'cyan'))
