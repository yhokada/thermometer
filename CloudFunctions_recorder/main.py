import base64
import ast
import redis
import yaml

def record_RedisLab(event, context):
    # read params from file
    with open('redis_param.yml', 'r') as f:
        yf = yaml.safe_load(f)
        RedisHost = yf['RedisHost']
        RedisPort = yf['RedisPort']
        RedisPwd  = yf['RedisPwd']

    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    msg_dict = ast.literal_eval(pubsub_message)
    datetime = str(msg_dict['time'])
    r = redis.Redis(host=RedisHost, port=RedisPort, password=RedisPwd, db=0)
    r.rpush(datetime[0:8], pubsub_message)
