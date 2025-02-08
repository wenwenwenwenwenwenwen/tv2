import base64
import datetime
import time
import requests
from bs4 import BeautifulSoup
from eventlet.green import os
import re
import json
#'''
surls = [
    "河南", # 河南
    "陕西", # 陕西
    "山西", # 山西
    "河北", # 河北
    "北京", # 北京
    "湖北", # 湖北
    "湖南", # 湖南
    "广东", # 广东
    "山东", # 山东
    "浙江", # 浙江
    "上海", # 上海
    "重庆", # 重庆
    "天津", # 天津
    "四川", # 四川
    "云南", # 云南
    "贵州", # 贵州
    "广西", # 广西
    "内蒙古", # 内蒙古
    "福建", # 福建
    "甘肃", # 甘肃
    "辽宁", # 辽宁
    "安徽", # 安徽
]
#'''
'''
surls = [
    "安徽", # 安徽
]
'''
resultsUrl = []
def sort_key(item):
    # 检查'source'中是否包含'组播'
    contains_multicast = 1 if '组播' in item['source'] else 0

    # 将'online_time'从字符串转换为datetime对象
    online_time = datetime.strptime(item['online_time'], '%Y-%m-%d %H:%M')

    # 返回一个元组，第一个元素用于'组播'的优先级，第二个元素是datetime对象
    return (contains_multicast, online_time)
def get_sourceIps(province,city,org):
    # 发送POST请求
    #data={"saerch":c}
    qbase64='server="udpxy"'
    if(province):
        qbase64+='&&province="'+province+'"'
    if(city):
        qbase64+='&&city="'+city+'"'
    if(org):
        qbase64+='&&org="'+org+'"'
    qbase64_bytes = qbase64.encode('utf-8')
    qbase64_encoded = base64.b64encode(qbase64_bytes)
    qbase64_encoded_str = qbase64_encoded.decode('utf-8')
    qbase64pParam = qbase64_encoded_str.replace("=","%3D")
    response = None
    # 存储结果的列表
    results = []
    try:
        response = requests.get("https://fofa.info/result?qbase64="+qbase64pParam,timeout=(5, 7))
        #解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        # 定位到.tables元素
        tables_divs = soup.findAll('div', class_='hsxa-meta-data-item')
        # 查找所有的.result元素
        for result in tables_divs:
            # 获取.channel下的IP和端口
            channel_div = result.find('div', class_='hsxa-fl hsxa-meta-data-list-lv1-lf')
            if channel_div and channel_div.a:
                channel_a = channel_div.a
                url = channel_a['href']
            # 检查存活状态
            #alive_div = result.find('div', style="color:limegreen;")
            all_jumpa_div = result.findAll('a', class_='el-tooltip hsxa-jump-a item')
            if all_jumpa_div:
                source=''
                try:
                    source = all_jumpa_div[1].text
                    if('China Mobile' in source):
                        source='yidong'
                    if('UNICOM' in source or 'Unicom' in source):
                        source='liantong'
                    if('Chinanet' in source or 'China Networks' in source or 'CHINA TELECOM' in source or 'China Telecom' in source or 'ASN for TIANJIN Provincial Net of CT' in source):
                        source='dianxin'
                except Exception as e:
                    print(f"An error occurred: {e}")
                #矫正ip省份
                response1 = None
                try:
                    ip_pattern = r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}'
                    ip_address = re.search(ip_pattern, url).group(0)
                    response1 = requests.get("https://qifu-api.baidubce.com/ip/geo/v1/district?ip="+ip_address,timeout=(5, 5))
                    jsondata = response1.text
                    # 将JSON字符串转换为Python字典
                    data_dict = json.loads(jsondata)
                    # 从字典中获取'prov'的值
                    province = data_dict['data']['prov']
                    province = province.replace("市","")
                    province = province.replace("省","")
                    province = province.replace("壮族自治区","")
                    province = province.replace("自治区","")
                    provincename = province
                except Exception as e:
                    print(f"An error occurred: {e}")
                finally:
                    if response1 is not None:
                        response1.close()
                # 将数据添加到结果列表
                if("河南"==province):
                    province="henan"
                if("陕西"==province):
                    province="Shaanxi"
                if("山西"==province):
                    province="shanxi"
                if("湖北"==province):
                    province="hubei"
                if("湖南"==province):
                    province="hunan"
                if("四川"==province):
                    province="sichuan"
                if("重庆"==province):
                    province="chongqing"
                if("云南"==province):
                    province="yunnan"
                if("贵州"==province):
                    province="guizhou"
                if("广西"==province):
                    province="guangxi"
                if("广东"==province):
                    province="guangdong"
                if("福建"==province):
                    province="fujian"
                if("江西"==province):
                    province="jiangxi"
                if("浙江"==province):
                    province="zhejiang"
                if("上海"==province):
                    province="shanghai"
                if("江苏"==province):
                    province="jiangsu"
                if("山东"==province):
                    province="shandong"
                if("河北"==province):
                    province="hebei"
                if("北京"==province):
                    province="beijing"
                if("天津"==province):
                    province="tianjin"
                if("内蒙古"==province):
                    province="neimenggu"
                if("甘肃"==province):
                    province="gansu"
                if("新疆"==province):
                    province="xinjiang"
                if("青海"==province):
                    province="qinghai"
                if("辽宁"==province):
                    province="liaoning"
                if("黑龙江"==province):
                    province="heilongjiang"
                if("吉林"==province):
                    province="jilin"
                if("安徽"==province):
                    province="anhui"
                results.append({
                    'ip_port': url,
                    'source': province+source,
                    'province': provincename,
                })
        # 使用sorted()函数和上述定义的sort_key函数对results进行排序
        #sorted_results = sorted(results, key=sort_key, reverse=True)  # reverse=True表示降序排序
        # 打印结果
        '''
        for item in sorted_results:
            print(item)
        '''
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if response is not None:
            response.close()
    return results
def get_sourceIpsBy360(province,org):
    provincename = province
    source=''
    response1 = None
    # 存储结果的列表
    results = []
    try:
        # 构建 JSON 数据
        jsondata = {
            "latest": True,
            "ignore_cache": False,
            "shortcuts": ["635fcbaacc57190bd8826d0b"],
            "query": f"udpxy AND province: \"{province}\" AND isp: \"{org}\"",
            "start": 0,
            "size": 20,
            "device": {
                "device_type": "PC",
                "os": "Windows",
                "os_version": "10.0",
                "language": "zh_CN",
                "network": "4g",
                "browser_info": "Chrome（版本: 127.0.0.0&nbsp;&nbsp;内核: Blink）",
                "fingerprint": "2344faaa",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "date": "2025/1/18 16:27:48",
                "UUID": "e47c45a9-c394-5029-8ae0-064bf730f17f"
            }
        }
        #print(jsondata)
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'MyApp/0.0.1',
            'cookie': '__guid=73887506.1145885847278714400.1722561349758.917; cert_common=d1517207-dd16-4102-8741-4e761c92b044; Qs_lvt_357693=1722561348%2C1724829525%2C1724912672%2C1737188650; __quc_silent__=1; i360QRKEY=c334c6ed290ff6fdb236ae54bff1182dfc5; Q=u%3D360H2931642336%26n%3D%26le%3D%26m%3DZGt3WGWOWGWOWGWOWGWOWGWOAGZ3%26qid%3D2931642336%26im%3D1_t011655040b3ed000bf%26src%3Dpcw_i360%26t%3D1; __NS_Q=u%3D360H2931642336%26n%3D%26le%3D%26m%3DZGt3WGWOWGWOWGWOWGWOWGWOAGZ3%26qid%3D2931642336%26im%3D1_t011655040b3ed000bf%26src%3Dpcw_i360%26t%3D1; T=s%3D58f851da3c39b9714e0f5d27b4cfe09a%26t%3D1737188852%26lm%3D%26lf%3D2%26sk%3Df139bc324b560d2ebade7aab036e4856%26mt%3D1737188852%26rc%3D%26v%3D2.0%26a%3D1; __NS_T=s%3D58f851da3c39b9714e0f5d27b4cfe09a%26t%3D1737188852%26lm%3D%26lf%3D2%26sk%3Df139bc324b560d2ebade7aab036e4856%26mt%3D1737188852%26rc%3D%26v%3D2.0%26a%3D1; Qs_pv_357693=3012971034071502300%2C493375835945720450%2C349798382137149600%2C2583127537602119000%2C2616462266977020400'
        }
        responese = requests.post("https://quake.360.net/api/search/query_string/quake_service",data=json.dumps(jsondata, indent=4),headers=headers)
        parsed_json = json.loads(responese.text)
        ipsearchDatas = parsed_json.get("data")
        # 将数据添加到结果列表
        if("河南"==province):
            province="henan"
        if("陕西"==province):
            province="Shaanxi"
        if("山西"==province):
            province="shanxi"
        if("湖北"==province):
            province="hubei"
        if("湖南"==province):
            province="hunan"
        if("四川"==province):
            province="sichuan"
        if("重庆"==province):
            province="chongqing"
        if("云南"==province):
            province="yunnan"
        if("贵州"==province):
            province="guizhou"
        if("广西"==province):
            province="guangxi"
        if("广东"==province):
            province="guangdong"
        if("福建"==province):
            province="fujian"
        if("江西"==province):
            province="jiangxi"
        if("浙江"==province):
            province="zhejiang"
        if("上海"==province):
            province="shanghai"
        if("江苏"==province):
            province="jiangsu"
        if("山东"==province):
            province="shandong"
        if("河北"==province):
            province="hebei"
        if("北京"==province):
            province="beijing"
        if("天津"==province):
            province="tianjin"
        if("内蒙古"==province):
            province="neimenggu"
        if("甘肃"==province):
            province="gansu"
        if("新疆"==province):
            province="xinjiang"
        if("青海"==province):
            province="qinghai"
        if("辽宁"==province):
            province="liaoning"
        if("黑龙江"==province):
            province="heilongjiang"
        if("吉林"==province):
            province="jilin"
        if("安徽"==province):
            province="anhui"
        if('移动' in org):
            source='yidong'
        if('联通' in org):
            source='liantong'
        if('电信' in org):
            source='dianxin'
        for ipsearchData in ipsearchDatas:
            url="http://"+ipsearchData.get("ip")+":"+str(ipsearchData.get("port"))
            results.append({
                'ip_port': url,
                'source': province+source,
                'province': provincename,
            })
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if response1 is not None:
            response1.close()
    return results
def checkValidUrl(url):
    print("checkValidUrl:"+url.get("ip_port"))
    try:
        response=None
        response = requests.get(url.get("ip_port")+"/status",timeout=(2, 2))
        if response is not None and response.status_code == 200:
            return 1
        else:
            return 0
    except Exception as e:
        return 0


def validPlay(payUlr):
    # 开始计时
    try:
        # 发送GET请求，设置headers以保持长连接
        # 注意：连接超时时间为 5 秒，而读取超时时间为 3 秒。
        print("校验palyurl:"+payUlr)
        response = requests.get(payUlr, stream=True, headers={"Connection": "keep-alive"}, timeout=(3, 3))
        #response = requests.get(ts_url, stream=True, headers={"Connection": "keep-alive"})
        # 检查响应状态码是否为200，即请求成功
        if response is not None and response.status_code == 200:
            # 下载一小部分数据，例如1MB
            chunk_size = 2*1024 * 1024 # 1MB
            data = b''
            #data = response.raw.read(chunk_size)
            # 试试下面的代码
            try:
                start_time = time.time()
                '''
                for chunk in response.iter_content(chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        data += chunk
                        break  # 只读取第一个chunk，根据需要调整
                '''
                # 读取数据，同时监控时间，确保不超过5秒
                read_timeout = 5  # 设置读取数据的最大时间
                while time.time() - start_time < read_timeout:
                    chunk = next(response.iter_content(chunk_size), None)
                    if chunk:
                        data += chunk
                        break  # 只读取第一个chunk
                # 结束计时
                end_time = time.time()
                # 计算下载速度
                response_time = end_time - start_time
            except Exception as e:
                return 0
            finally:
                if response is not None:
                    response.close()
            if data:
                file_size = len(data)
                # print(f"文件大小：{file_size} 字节")
                download_speed = file_size / response_time / 1024
                print(f"下载速度：{download_speed:.3f} kB/s")
                if(download_speed>1000):
                    return download_speed
                else:
                    return 0
            else:
                return 0
    except Exception as e:
        return 0
#https://ip.taobao.com/outGetIpInfo?accessKey=alibaba-inc&ip=123.161.92.252 ip运营商获取
def checkOpenUrl(url):
    file_path = url.get("source")+".txt"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                payUrl = line.strip()
                payUrl = payUrl.replace("http://61.52.154.181:4100",url.get("ip_port"))
                payUrl = payUrl.replace("http://1.192.5.29:8800",url.get("ip_port"))
                payUrl = payUrl.replace("http://219.145.19.76:5555",url.get("ip_port"))
                payUrl = payUrl.replace("http://1.70.34.66:8085",url.get("ip_port"))
                payUrl = payUrl.replace("http://106.9.182.35:6000",url.get("ip_port"))
                payUrl = payUrl.replace("http://60.7.56.50:4000",url.get("ip_port"))
                payUrl = payUrl.replace("http://1.203.184.234:4000",url.get("ip_port"))
                payUrl = payUrl.replace("http://114.252.229.94:8000",url.get("ip_port"))
                payUrl = payUrl.replace("http://121.60.90.161:8000",url.get("ip_port"))
                payUrl = payUrl.replace("http://118.254.201.17:8888",url.get("ip_port"))
                payUrl = payUrl.replace("http://223.72.16.224:8887",url.get("ip_port"))
                payUrl = payUrl.replace("http://113.92.165.182:60000",url.get("ip_port"))
                payUrl = payUrl.replace("http://113.120.108.236:4000",url.get("ip_port"))
                payUrl = payUrl.replace("http://27.210.198.200:1029",url.get("ip_port"))
                payUrl = payUrl.replace("http://60.189.35.225:9999",url.get("ip_port"))
                payUrl = payUrl.replace("http://58.41.27.144:18888",url.get("ip_port"))
                payUrl = payUrl.replace("http://113.251.228.27:58888",url.get("ip_port"))
                payUrl = payUrl.replace("http://27.10.77.23:8004",url.get("ip_port"))
                payUrl = payUrl.replace("http://117.13.250.38:4022",url.get("ip_port"))
                payUrl = payUrl.replace("http://180.213.163.213:8000",url.get("ip_port"))
                payUrl = payUrl.replace("http://110.184.114.148:4000",url.get("ip_port"))
                payUrl = payUrl.replace("http://58.42.184.110:8888",url.get("ip_port"))
                payUrl = payUrl.replace("http://106.59.2.162:55555",url.get("ip_port"))
                payUrl = payUrl.replace("http://116.252.77.132:4444",url.get("ip_port"))
                payUrl = payUrl.replace("http://110.7.130.15:4022",url.get("ip_port"))
                payUrl = payUrl.replace("http://117.28.177.215:8605",url.get("ip_port"))
                payUrl = payUrl.replace("http://www.lebaobei.top:6868",url.get("ip_port"))
                payUrl = payUrl.replace("http://60.17.195.0:8888",url.get("ip_port"))
                payUrl = payUrl.replace("http://183.166.208.104:4000",url.get("ip_port"))
                payUrls = payUrl.split(",")
                speed = validPlay(payUrls[1])
                if(speed is not None and speed>300):
                    print("validPlay yes:"+payUrl+"speed:"+str(speed))  # strip() 方法去除每行末尾的换行符
                    return speed
                    break
                else:
                    return 0
                    break
    return 0
#'''
def quchong(urls_all):
    # 使用字典去重
    unique_proxies = {}
    for proxy in urls_all:
        unique_proxies[proxy['ip_port']] = proxy
    # 转换为列表
    unique_proxies_list = list(unique_proxies.values())
    return unique_proxies_list

for province in surls:
    chinanet_urls_all=[];
    chinanet_urls_all1=[];
    chinanet_urls_all2=[];
    chinanet_urls_all3=[];
    chinanet_urls_all4=[];
    if province=="北京":
        chinanet_urls_all = get_sourceIps(province,'',"China Unicom Beijing Province Network")#联通
    else:
        chinanet_urls_all = get_sourceIps(province,'',"CHINA UNICOM China169 Backbone")#联通
    if province=="北京":
        chinanet_urls_all1 = get_sourceIps(province,'',"China Networks Inter-Exchange")
    if province=="上海":
        chinanet_urls_all1 = get_sourceIps(province,'',"China Telecom Group")
    if province=="天津":
        chinanet_urls_all1 = get_sourceIps(province,'',"ASN for TIANJIN Provincial Net of CT")
    else:
        chinanet_urls_all1 = get_sourceIps(province,'',"Chinanet")
    for chinanet_url in chinanet_urls_all1:
        chinanet_urls_all.append(chinanet_url)
    chinanet_urls_all2 = get_sourceIpsBy360(province,"电信")
    chinanet_urls_all3 = get_sourceIpsBy360(province,"联通")
    chinanet_urls_all4 = get_sourceIpsBy360(province,"移动")
    for chinanet_url in chinanet_urls_all2:
        chinanet_urls_all.append(chinanet_url)
    for chinanet_url in chinanet_urls_all3:
        chinanet_urls_all.append(chinanet_url)
    for chinanet_url in chinanet_urls_all4:
        chinanet_urls_all.append(chinanet_url)
    #urls_all=[{'ip_port': 'http://42.233.43.49:4000', 'source': 'henanliantong'}, {'ip_port': 'http://123.163.115.6:21', 'source': 'henandianxin'}, {'ip_port': 'http://123.163.115.6:21', 'source': 'henandianxin'}, {'ip_port': 'http://61.52.27.249:2000', 'source': 'henanliantong'}, {'ip_port': 'http://115.60.241.249:2000', 'source': 'henanliantong'}, {'ip_port': 'http://115.60.241.249:2000', 'source': 'henanliantong'}, {'ip_port': 'http://61.52.27.249:2000', 'source': 'henanliantong'}, {'ip_port': 'http://61.163.146.176:8888', 'source': 'henanliantong'}, {'ip_port': 'http://123.13.245.57:4000', 'source': 'henanliantong'}, {'ip_port': 'http://123.13.245.57:4000', 'source': 'henanliantong'}]
    urls = quchong(chinanet_urls_all)  # 去重得到唯一的URL列表
    print("获取到的url:"+json.dumps(urls))
    for url in urls:
        if(checkValidUrl(url)==1):
            speed = checkOpenUrl(url)
            if(speed is not None and speed>100):
                resultsUrl.append({
                    'ip_port': url.get("ip_port"),
                    'speed': speed,
                    'source': url.get("source"),
                    'province': url.get("province"),
                })
    #urls_all=[{'ip_port': 'http://42.233.43.49:4000', 'source': 'henanliantong'}, {'ip_port': 'http://123.163.115.6:21', 'source': 'henandianxin'}, {'ip_port': 'http://123.163.115.6:21', 'source': 'henandianxin'}, {'ip_port': 'http://61.52.27.249:2000', 'source': 'henanliantong'}, {'ip_port': 'http://115.60.241.249:2000', 'source': 'henanliantong'}, {'ip_port': 'http://115.60.241.249:2000', 'source': 'henanliantong'}, {'ip_port': 'http://61.52.27.249:2000', 'source': 'henanliantong'}, {'ip_port': 'http://61.163.146.176:8888', 'source': 'henanliantong'}, {'ip_port': 'http://123.13.245.57:4000', 'source': 'henanliantong'}, {'ip_port': 'http://123.13.245.57:4000', 'source': 'henanliantong'}]
    '''
    urls_all_unicom = get_sourceIps(province,'',"CHINA UNICOM China169 Backbone")#联通
    urls1 = quchong(urls_all_unicom)  # 去重得到唯一的URL列表
    for url in urls1:
        if(checkValidUrl(url)==1):
            speed = checkOpenUrl(url)
            if(speed>100):
                resultsUrl.append({
                    'ip_port': url.get("ip_port"),
                    'speed': speed,
                    'source': url.get("source"),
                    'province': province,
                })
    '''
    print("有用的url:"+json.dumps(resultsUrl))
results = []
for vurl in resultsUrl:
    ip_port = vurl.get("ip_port")
    source = vurl.get("source")
    speed = vurl.get("speed")
    province = vurl.get("province")
    normalized_speed = min(max(speed / 1024, 0.001), 100)  # 将速率从kB/s转换为MB/s并限制在1~100之间
    file_path=source+".txt"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                payUrl = line.strip()
                payUrl = payUrl.replace("http://61.52.154.181:4100",ip_port)
                payUrl = payUrl.replace("http://1.192.5.29:8800",ip_port)
                payUrl = payUrl.replace("http://219.145.19.76:5555",ip_port)
                payUrl = payUrl.replace("http://1.70.34.66:8085",ip_port)
                payUrl = payUrl.replace("http://106.9.182.35:6000",ip_port)
                payUrl = payUrl.replace("http://60.7.56.50:4000",ip_port)
                payUrl = payUrl.replace("http://1.203.184.234:4000",ip_port)
                payUrl = payUrl.replace("http://114.252.229.94:8000",ip_port)
                payUrl = payUrl.replace("http://121.60.90.161:8000",ip_port)
                payUrl = payUrl.replace("http://118.254.201.17:8888",ip_port)
                payUrl = payUrl.replace("http://223.72.16.224:8887",ip_port)
                payUrl = payUrl.replace("http://113.92.165.182:60000",ip_port)
                payUrl = payUrl.replace("http://113.120.108.236:4000",ip_port)
                payUrl = payUrl.replace("http://27.210.198.200:1029",ip_port)
                payUrl = payUrl.replace("http://60.189.35.225:9999",ip_port)
                payUrl = payUrl.replace("http://58.41.27.144:18888",ip_port)
                payUrl = payUrl.replace("http://113.251.228.27:58888",ip_port)
                payUrl = payUrl.replace("http://27.10.77.23:8004",ip_port)
                payUrl = payUrl.replace("http://117.13.250.38:4022",ip_port)
                payUrl = payUrl.replace("http://180.213.163.213:8000",ip_port)
                payUrl = payUrl.replace("http://110.184.114.148:4000",ip_port)
                payUrl = payUrl.replace("http://58.42.184.110:8888",ip_port)
                payUrl = payUrl.replace("http://106.59.2.162:55555",ip_port)
                payUrl = payUrl.replace("http://116.252.77.132:4444",ip_port)
                payUrl = payUrl.replace("http://110.7.130.15:4022",ip_port)
                payUrl = payUrl.replace("http://117.28.177.215:8605",ip_port)
                payUrl = payUrl.replace("http://www.lebaobei.top:6868",ip_port)
                payUrl = payUrl.replace("http://60.17.195.0:8888",ip_port)
                payUrl = payUrl.replace("http://183.166.208.104:4000",ip_port)
                channel_name,channel_url = payUrl.split(",")
                result = channel_name, channel_url, f"{normalized_speed:.3f} MB/s",province
                results.append(result)

def channel_key(channel_name):
    match = re.search(r'\d+', channel_name)
    if match:
        return int(match.group())
    else:
        return float('inf')  # 返回一个无穷大的数字作为关键字

# 对频道进行排序
results.sort(key=lambda x: (x[0], -float(x[2].split()[0])))
results.sort(key=lambda x: channel_key(x[0]))


result_counter = 20  # 每个频道需要的个数

with open("itvlist.txt", 'w', encoding='utf-8') as file:
    channel_counters = {}
    file.write('央视频道,#genre#\n')
    for result in results:
        channel_name, channel_url, speed,province = result
        if 'CCTV' in channel_name or 'CGTN' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    file.write('卫视频道,#genre#\n')
    for result in results:
        channel_name, channel_url, speed,province = result
        if '卫视' in channel_name or 'CHC' in channel_name:
            if channel_name in channel_counters:
                if channel_counters[channel_name] >= result_counter:
                    continue
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] += 1
            else:
                file.write(f"{channel_name},{channel_url}\n")
                channel_counters[channel_name] = 1
    channel_counters = {}
    for url in surls:
        file.write(url+',#genre#\n')
        for result in results:
            channel_name, channel_url, speed,province = result
            if 'CCTV' not in channel_name and '卫视' not in channel_name and '测试' not in channel_name and province == url and  'CHC' not in channel_name and  'CGTN' not in channel_name:
                if channel_name in channel_counters:
                    if channel_counters[channel_name] >= result_counter:
                        continue
                    else:
                        file.write(f"{channel_name},{channel_url}\n")
                        channel_counters[channel_name] += 1
                else:
                    file.write(f"{channel_name},{channel_url}\n")
                    channel_counters[channel_name] = 1


def uploadTvlist(file_path):
    # 读取文件
    try:
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': (file_path, f)}
            response = requests.post("http://api.ximiba.cn/proxy/iptv/uploadTvlist.php", files=files,timeout=(5, 5))
            # 检查响应状态码
            if response.status_code == 200:
                print('File uploaded successfully.')
            else:
                print(f'Error uploading file: {response.text}')
    except Exception as e:
        print(f"上传tvlist失败: {e}")
uploadTvlist("itvlist.txt");
