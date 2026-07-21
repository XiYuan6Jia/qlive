# get_danmu.py 监听B站直播间，进场和弹幕

from bilibili_api import live, Credential, live_area
import asyncio
import json
from datetime import datetime
from client import send as sendinfo
import threading

#直播间号
#room_id = 23929781 #罗太
#room_id = 1828188060 #怪猎
room_id = 12434708 #我

with open('credential.json','r', encoding='UTF-8') as file:
    cred = json.load(file)

async def main() -> None:
    try:
        a_Credential = Credential(**cred)
        danmaku1 = live.LiveDanmaku(room_id, False, a_Credential)
                            
        @danmaku1.on("DANMU_MSG")
        async def handler(event):
            info = event['data']['info']
            print(f"{info[2][1]}: {info[1]}")
            '''                # 添加时间戳
                        danmu_data = {
                            'timestamp': datetime.now().isoformat(),
                            'info': info,  # 完整的info结构
                            'raw_event': event  # 可选：保存完整事件
                        }
                        with open('danmu.json','a', encoding='UTF-8') as file:
                            file.write(json.dumps(danmu_data, ensure_ascii=False) + '\n')
            '''
            data = {'cmd':'DANMU_MSG',
                    'uname':info[2][1],
                    'msg':info[1]}
            sendinfo(data)

        @danmaku1.on("INTERACT_WORD_V2")
        async def handler(event):
            info = event['data']['data']['pb_decoded']
            welcome_msg = f"欢迎 {info['uname']} 进入直播间！"
            print(welcome_msg)
            data = {'cmd':'INTERACT_WORD_V2',
                    'uname':info['uname'],
                    'msg':welcome_msg}

        await danmaku1.connect()
            
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 清理资源
        if 'danmaku1' in locals():
            await danmaku1.disconnect()
if __name__ == "__main__":
    asyncio.run(main())
