from time import sleep

import requests
import mysql.connector
from flask import Flask
from dotenv import load_dotenv

import os
import re
import time
from pprint import pprint

load_dotenv()

LAST_ID = 17493
FIRST_ID = 5151
TEST_FIRST_ID = 17101
TOKEN_OL = os.getenv("TOKEN_OL")
SOURCES_CONSTANTS = {
    "wz_whatsapp": "whatsapp",
    "livechat": "online_chat",
    "telegrambot": "telegram",
    "wz_telegram": "telegram",
    "vkgroup": "vk",
    "fbinstagram": "instagram",
    "wz_instagram": "instagram",
    "facebook": "facebook"
}
SLEEP_CONST_SEC = 0.5


def get_all_sessions(first_id: int = FIRST_ID) -> None:
    """
    Iterates over all client sessions starting from the given session ID,
    filters out sessions with no external participants (i.e. keeps only sessions
    with at least 2 senders where at least one is not a Company Name employee).

    Each session is inserted into the DB on first encounter. The is_finished field
    tracks whether the session is closed. Sessions with is_finished=0 are updated
    on subsequent runs.

    session_id is the PRIMARY KEY and is unique. client_id may repeat across sessions
    since one client can have multiple sessions over time. When using dialog text for
    further processing, texts should be merged by client_id in ascending session_id order.

    :param first_id: <int>
    :return: <None>:
    """
    # Production

    def construct_dialog(result_response_: dict, client_name_: str):
        dialog_text_ = ''
        messages_dict: dict = result_response_.get("message")
        msg_values = list(messages_dict.values())[::-1]
        senders_ = []
        is_finished_ = False
        for msg in msg_values:
            if isinstance(msg, dict):
                msg: dict
                params = msg.get("params")
                if params:
                    if params.get("connectorMid"):
                        raw_text: str = msg.get("text")
                        file_id = params.get("fileId")
                        if raw_text.startswith("=== Исходящее сообщение, автор:"):
                            sender = raw_text.split("\n")[0]
                            sender_match = re.search(r'\(([^)]+)\)', sender)
                            if sender_match:
                                sender = f"{sender_match.group(1)} |COMPANY|"
                            elif "Телефон" in sender:
                                sender = "Телефонный звонок |COMPANY|"
                            dialog_without_sender = '\n'.join(raw_text.split("\n")[1:])
                        else:
                            sender = client_name_
                            dialog_without_sender = raw_text

                        if sender not in senders_:
                            senders_.append(sender)
                        dialog_text_ += f"{sender}:\n{dialog_without_sender}\n"

                        if file_id:
                            dialog_text_ += f"file_id: {file_id}\n"
                        else:
                            dialog_text_ += "\n"

                    elif params.get("class") == "bx-messenger-content-item-ol-end":
                        is_finished_ = True
        return dialog_text_, senders_, is_finished_

    db_conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    db_cur = db_conn.cursor()

    db_cur.execute(
        """CREATE TABLE IF NOT EXISTS sessions(
            session_id INT PRIMARY KEY,
            client_id INT,
            client_name VARCHAR (255),
            source VARCHAR(255),
            is_finished TINYINT(1),
            text TEXT
        )"""
    )

    errors_list = []

    select_not_finished_query = "SELECT session_id FROM sessions WHERE is_finished = %s"
    db_cur.execute(select_not_finished_query, (False,))
    not_finished_id_tuples = db_cur.fetchall()
    not_finished_ids = [tup[0] for tup in not_finished_id_tuples]
    print(f"{not_finished_ids=}")

    if not_finished_ids:
        for not_finished_id in not_finished_ids:
            try:
                dialog_response = requests.get(f"{TOKEN_OL}imopenlines.session.history.get.json?SESSION_ID={not_finished_id}").json()
                print(f"{not_finished_id=}")
                result_response = dialog_response.get("result")
                if result_response:
                    client_name_query = "SELECT client_name FROM sessions WHERE session_id = %s"
                    db_cur.execute(client_name_query, (not_finished_id,))
                    client_name = db_cur.fetchone()[0]
                    dialog_text, _, is_finished = construct_dialog(result_response, client_name)
                    update_text_query = "UPDATE sessions SET text = %s WHERE session_id = %s"
                    db_cur.execute(update_text_query, (dialog_text, not_finished_id))
                    if is_finished:
                        update_is_finished_query = "UPDATE sessions SET is_finished = %s WHERE session_id = %s"
                        db_cur.execute(update_is_finished_query, (is_finished, not_finished_id))
                    db_conn.commit()
                time.sleep(SLEEP_CONST_SEC)
            except Exception:
                print(f"\nERROR by {not_finished_id=}\n")
                errors_list.append(not_finished_id)
    else:
        session_id = first_id
        while True:
            # try:
            dialog_response = requests.get(f"{TOKEN_OL}imopenlines.session.history.get.json?SESSION_ID={session_id}").json()
            print()
            print()
            print('=' * 85)
            print(f"{session_id=}")

        # Test
        # test_ids = (17183,)
        # for test_id in test_ids:
        #
        #     dialog_response = requests.get(f"{TOKEN_OL}imopenlines.session.history.get.json?SESSION_ID={test_id}").json()
        #     print()
        #     print()
        #     print('=' * 85)
        #
        #     print(f"{test_id=}")
        #     pprint(dialog_response)

            result_response = dialog_response.get("result")

            if result_response:
                client_id = str(result_response.get("chatId"))  # chatId or chat<chatId>

                client_name = result_response.get("chat").get(client_id).get("name").split(" - Открытая линия")[0]  # strip Open Line suffix

                # resolve source platform
                entity_id: str = result_response.get("chat").get(client_id).get("entityId").split('|')[0]
                for sources_key in SOURCES_CONSTANTS.keys():
                    if entity_id.startswith(sources_key):
                        source = SOURCES_CONSTANTS.get(sources_key)
                        break
                else:
                    raise ValueError(f"Error with source_key in entityId: {entity_id}!")

                # build dialog text
                dialog_text, senders, is_finished = construct_dialog(result_response, client_name)

                def are_all_company(senders_arr: list) -> bool:
                    for sender_ in senders_arr:
                        if "|COMPANY|" not in sender_:
                            return False
                    return True

                print(f"{senders=}")

                if len(senders) > 1 and (not are_all_company(senders)):
                    insert_sessions_query = "INSERT INTO sessions (session_id, client_id, client_name, source, is_finished, text) VALUES (%s, %s, %s, %s, %s, %s)"
                    db_cur.execute(insert_sessions_query,(session_id, client_id, client_name, source, is_finished, dialog_text))
                    db_conn.commit()

            elif dialog_response.get("error"):
                pprint(dialog_response)
                print(session_id)
                break

            time.sleep(SLEEP_CONST_SEC)

            # except Exception:
            #     print(f"\nERROR by {session_id=}\n")
            #     errors_list.append(session_id)

            session_id += 2

    db_cur.close()
    db_conn.close()

    print(f"\nERRORS: {len(errors_list)}")
    print(errors_list)
    print()


# app = Flask(__name__)
# FLASK_SLEEP_CONST_SEC = 43200
#
# @app.route('/')
# def index():
#     try:
#         while True:
#             get_all_sessions(FIRST_ID)
#             sleep(FLASK_SLEEP_CONST_SEC)  # every 12 hours
#     except Exception as e:
#         print("ERROR by Flask!")
#         print(e.args)


if __name__ == "__main__":
    get_all_sessions(FIRST_ID)

    # app.run(
    #     debug=True,
    # )
