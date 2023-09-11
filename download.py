import re
import requests
from validators import url
import time
import math
import subprocess
import shutil
import os

def is_can_decode(content):
    if content.startswith('#EXTM3U'): 
        return True

    return False

def is_m3u8_file(content):
    if '#EXT-X-STREAM-INF' in content: 
        return True

    return False

def is_ts_file(content):
    if '#EXTINF' in content:
        return True
    
    return False

def log_strftime(str):
    self_update.update_text.emit(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))} {str}')

def dialog_show(index):
    popup_active['active'] = True
    popup_active['index'] = index

def change_parent_dir():
    # 获取当前工作目录
    current_dir = os.getcwd() 

    # 将当前工作目录切分成目录路径组成的列表
    path_parts = current_dir.split(os.sep)

    # 弹出最后一个目录名,重新拼接成上级目录路径
    parent_dir = os.sep.join(path_parts[:-1])

    # 切换到上级目录
    os.chdir(parent_dir)

def set_global(update_p, m3u8_url,batch_s,refresh_f,aria2p):
    global self_update
    self_update = update_p
    # 并行数量
    global batch_size
    batch_size = batch_s
    # 刷新频率
    global refresh_frequency
    refresh_frequency = refresh_f
    # aria2
    global aria2
    aria2 = aria2p
    popup_active['active'] = False
    popup_active['index'] = 0
    complete_list = []

    ts_urls = []
    m3u8_init_url = m3u8_url
    download_m3u8(m3u8_url)

def longest_common_substring(s1, s2):
    pattern = re.compile(r"(/\w+)+/")

    match1 = pattern.search(s1)
    match2 = pattern.search(s2)

    if match1 and match2:
        common_part = match1.group()
        result = s1[:s1.find(common_part)] + s2[s2.find(common_part):]
    else:
        parts = s1.split("/")
        base_url = "/".join(parts[:-1]) + "/"
        result = base_url + s2

    return result

def download_m3u8(m3u8_url):
    log_strftime('解析文件内容')
    global m3u8_init_url
    m3u8_init_url = m3u8_url

    try:
        resp = requests.get(m3u8_url)
        m3u8_content = resp.text
    except:
        log_strftime('解析文件失败')
    
    
    if is_can_decode(m3u8_content):
        # 可解析类型
        if is_m3u8_file(m3u8_content):
            m3u8_urls = re.findall(r'^(.*?\.m3u8)', m3u8_content, re.M)

            # 选择码率视频
            if len(m3u8_urls) > 1:
                all_rate = re.findall(r'^(#EXT-X-STREAM-INF.*)', m3u8_content, re.M)
                # 多码率视频选择
                print('多码率视频选择')
                
                self_update.rate_select.emit(all_rate)

                while True:
                    if popup_active['active']:
                        break

                download_url = m3u8_urls[popup_active['index']]

                print(download_url)
            else:
                download_url = m3u8_urls[0]

            # 区别相对路径和绝对路径，相对路径一般是域名拼接 url
            if url(download_url):
                download_m3u8(download_url)
            else:
                print(longest_common_substring(m3u8_url,download_url))
                download_m3u8(longest_common_substring(m3u8_url,download_url))
                
        elif is_ts_file(m3u8_content):
            global ts_urls
            global complete_list

            ts_urls = ts_urls + (re.findall(r'^(.*?\.ts)', m3u8_content, re.M))

            f = open('video/merge.txt',"w",encoding='utf-8')    
            for i in range(len(ts_urls)):
                f.write("file 'ts/"+ts_urls[i].split('/')[-1] + ("'\n" if i != len(ts_urls)-1 else ''))
            f.close()
            
            # 状态存储
            status_map = {}

            log_strftime('开始下发切片任务')

            # 先下发一批
            for i in range(batch_size):
                download = download_ts(ts_urls[i])
                status_map[download.gid] = {
                    'down_url':ts_urls[i],
                }
            
            cycle_download(status_map, ts_urls[batch_size:])

            complete_list = []
            ts_urls = []
            log_strftime('切片下载完毕，开始合并')

            os.chdir('video')

            # 等待所有任务完成之后再合并
            timestamp = time.time()
            video_format = time.strftime("%Y%m%d_%H%M%S", time.localtime(timestamp)) + '.mp4'
            
            proc = subprocess.run(f'ffmpeg.exe -f concat -safe 0 -i merge.txt -c copy -bsf:a aac_adtstoasc ../output/{video_format}', shell=True)

            if proc.returncode == 0:
                print('视频合并成功，视频下载完成')
                log_strftime('视频合并成功，视频下载完成')
                # 删除ts文件
                shutil.rmtree('ts')
                
            else:
                print('视频合并失败', proc.returncode)
                log_strftime('视频合并失败'+ str(proc.returncode))
            # 切换到上级目录
            change_parent_dir()
            self_update.download_done.emit()
            # for download in downloads:
            #     print(download.gid,download.name,download.download_speed,download.status)
            print('是ts文件了')
        else:
            print('未知类型')
            log_strftime('未知类型无法下载')
            self_update.download_done.emit()

    else:
        log_strftime('未知类型无法下载')
        self_update.download_done.emit()

def cycle_download(s_map, t_urls):
    fail_status = {}
    full_num = len(t_urls)
    task_num = 0
    
    # 按照任务状态逐步补充
    while task_num <= full_num:
        for gid in s_map.copy():
            download = aria2.get_download(gid)
            if download.status == 'complete':
                complete_list.append(s_map[gid])
                del s_map[gid]
            if download.status == 'error':
                fail_status[gid] = s_map[gid]
                del s_map[gid]

        # 需要补充的任务数量
        complete_num = batch_size - len(s_map)
        print(complete_num, task_num, len(complete_list))
        self_update.update_progress.emit(int(100 * len(complete_list)/len(ts_urls)))

        self_update.update_text.emit(f'成功{len(complete_list)}条，总数{len(ts_urls)}条')

        if complete_num != 0:
            
            start_index = task_num
            end_index = (start_index + complete_num) if (start_index + complete_num) <= len(t_urls) else len(t_urls)

            print('补充范围', start_index,end_index)

            for url_item in t_urls[start_index: end_index]:
                download = download_ts(url_item)
                s_map[download.gid] = {
                    'down_url':url_item,
                }

        task_num = task_num + complete_num
        # 暂停1秒
        time.sleep(refresh_frequency)
    print('------------一轮完毕------------')
    # print('一轮完毕s_map',len(s_map),s_map, '\n')
    # print('一轮完毕fail_status',len(fail_status),fail_status)

    # 没有失败任务并不代表完成，此时还有运行中的任务，运行中的任务可能失败
    if len(fail_status) != 0 or len(s_map) != 0:
        next_urls = []
        for key in fail_status:
            next_urls.append(fail_status[key]['down_url'])
        cycle_download(s_map, next_urls)

def download_ts(ts_url):
    if url(ts_url):
        down_url = ts_url
    else:
        down_url = longest_common_substring(m3u8_init_url,ts_url)

    options = {
        "split": 100,
        "max-concurrent-downloads": 20,
    }

    return aria2.add_uris([down_url], options=options)

m3u8_init_url = 'https://vip.kuaikan-cdn2.com/20230818/AUTLNkSM/index.m3u8'
popup_active = {'active': False, 'index': 0}
m3u8_num = 0
ts_urls = []
complete_list = []