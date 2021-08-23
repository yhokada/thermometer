import datetime
import ast
import redis
import yaml
import requests

def send_line_notify(notification_message):
    with open('line_param.yml', 'r') as f:
        yf = yaml.safe_load(f)
        line_notify_token = yf['line_notify_token']

    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_notify_token}'}
    data = {'message': f'message: {notification_message}'}
    requests.post(line_notify_api, headers = headers, data = data)

def alert_thi(event, context):
    # read params from file
    with open('redis_param.yml', 'r') as f:
        yf = yaml.safe_load(f)
        RedisHost = yf['RedisHost']
        RedisPort = yf['RedisPort']
        RedisPwd  = yf['RedisPwd']

    currenttime = datetime.datetime.now()
    lastdaytime = currenttime - datetime.timedelta(days=1)
    
    r = redis.Redis(host=RedisHost, port=RedisPort, password=RedisPwd, db=0)
    today_rec_list=r.lrange(str(currenttime.strftime('%Y%m%d')), 0, -1)
    yesterday_rec_list=r.lrange(str(lastdaytime.strftime('%Y%m%d')), 0, -1)

    # get most recent data
    recent_record=ast.literal_eval(today_rec_list[-1].decode("utf-8"))
    
    # get max data in last 1 hours
    comparetime = currenttime - datetime.timedelta(hours=1)
    comparetime_str = comparetime.strftime('%Y%m%d%H%M%S')

    max=0
    # for record in yesterday_rec_list:
    #     this_record=ast.literal_eval(record.decode("utf-8"))
    #     if int(comparetime_str) < this_record['time'] and max < this_record['thi']:
    #         max = this_record['thi']
    #         max_record=this_record
    for record in today_rec_list:
        this_record=ast.literal_eval(record.decode("utf-8"))
        if int(comparetime_str) < this_record['time'] and max < this_record['thi']:
            max = this_record['thi']
            max_record=this_record

    mt=datetime.datetime.strptime(str(max_record['time']), '%Y%m%d%H%M%S')
    max_record_time="{}:{}".format(mt.hour, mt.minute)

    # comment
    if recent_record['thi'] < 50:
        comment=u"寒すぎるので部屋を暖めましょう"
    elif recent_record['thi'] > 50 and recent_record['thi'] < 55:
        comment=u"ちょっと寒いようです"
    elif recent_record['thi'] > 55 and recent_record['thi'] < 60:
        comment=u"肌寒いレベルです"
    elif recent_record['thi'] > 60 and recent_record['thi'] < 65:
        comment=u"特に寒さを感じないレベルです"
    elif recent_record['thi'] > 65 and recent_record['thi'] < 70:
        comment=u"快適です"
    elif recent_record['thi'] > 70 and recent_record['thi'] < 75:
        comment=u"一部の人は不快感を持つかもしれません"
    elif recent_record['thi'] > 75 and recent_record['thi'] < 80:
        comment=u"多くの人が不快感を持つレベルです"
    elif recent_record['thi'] > 80 and recent_record['thi'] < 85:
        comment=u"誰もが不快感を持つレベルです"
    elif recent_record['thi'] > 85:
        comment=u"暑すぎるのでクーラーを使いましょう"
    
    line_msg = u"現在の気温は{}℃、現在の湿度は{}%です。{}(不快度指数={:.1f})。\n".format(
        recent_record['temperature'],recent_record['humidity'],comment,recent_record['thi'])
    line_msg += u"なおこの1時間で最高値を記録したのは{}、温度は{}℃、湿度は{}%でした(不快度指数={:.1f})。".format(
        max_record_time,max_record['temperature'],max_record['humidity'],max_record['thi'])
    send_line_notify(line_msg)
    
if __name__ == '__main__':
    alert_thi(None, None)
